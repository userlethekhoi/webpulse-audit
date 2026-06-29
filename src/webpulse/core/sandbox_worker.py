"""Subprocess worker executing WebPulse plugins inside isolated sandboxes.

Translates standard input JSON-RPC 2.0 messages into plugin hooks execution.
"""

import asyncio
import json
import logging
import queue
import sys
import threading
from pathlib import Path
from typing import Any

from webpulse.core.plugin_loader import PluginLoader
from webpulse.reports.schemas import Target
from webpulse.utils.network import AsyncNetworkClient

# Direct all standard logging outputs strictly to stderr so they do not
# contaminate stdout JSON-RPC pipes
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="[Worker] %(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("webpulse.core.sandbox_worker")


async def main() -> None:
    """Run the worker process listening loop."""
    if len(sys.argv) < 2:
        logger.error("Usage: python -m webpulse.core.sandbox_worker <plugin_dir>")
        sys.exit(1)

    plugin_dir = Path(sys.argv[1])
    manifest_path = plugin_dir / "manifest.yaml"
    if not manifest_path.exists():
        manifest_path = plugin_dir / "manifest.yml"

    if not manifest_path.exists():
        logger.error(f"Plugin manifest file not found in: {plugin_dir}")
        sys.exit(1)

    # 1. Load the plugin class dynamically inside the worker
    try:
        loader = PluginLoader()
        plugin_cls = loader.load_plugin(plugin_dir, manifest_path)
        plugin_instance = plugin_cls()
        manifest = loader.manifests[plugin_instance.metadata.name]
    except Exception as e:
        logger.error(f"Failed to initialize plugin inside sandbox worker: {e}")
        sys.exit(1)

    # 2. Start stdin command loop in a separate thread to prevent Windows blockages
    def read_stdin(q_in: queue.Queue[str | None]) -> None:
        for line in sys.stdin:
            q_in.put(line)
        q_in.put(None)

    stdin_queue: queue.Queue[str | None] = queue.Queue()
    t = threading.Thread(target=read_stdin, args=(stdin_queue,), daemon=True)
    t.start()

    loop = asyncio.get_running_loop()
    logger.info(f"Sandbox worker ready for plugin: {manifest.name}")

    while True:
        line = await loop.run_in_executor(None, stdin_queue.get)
        if line is None:
            break

        line = line.strip()
        if not line:
            continue

        req_id: Any = None
        try:
            payload = json.loads(line)
            req_id = payload.get("id")
            method = payload.get("method")
            params = payload.get("params", {})

            if method == "on_load":
                config = params.get("config", {})
                await plugin_instance.on_load(config)
                response = {"jsonrpc": "2.0", "result": None, "id": req_id}

            elif method == "execute":
                target_dict = params.get("target", {})
                target = Target.model_validate(target_dict)

                # Initialize a secure network client for the plugin execution
                # Allow private IP access only if the manifest allows it
                client = AsyncNetworkClient(allow_private_ips=manifest.permissions.network_access)
                try:
                    findings = await plugin_instance.execute(target, client)
                    result_findings = [f.model_dump() for f in findings]
                    response = {"jsonrpc": "2.0", "result": result_findings, "id": req_id}
                finally:
                    await client.close()

            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                    "id": req_id,
                }

        except Exception as e:
            logger.error(f"Error handling worker command: {e}")
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": req_id,
            }

        # Write result to stdout and flush immediately
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sandbox worker terminated by interrupt.")
