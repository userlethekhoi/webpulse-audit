"""Sandbox wrapper for executing third-party plugins in subprocess isolation.

Uses JSON-RPC 2.0 over stdin/stdout pipelines to manage the execution lifecycle.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

from webpulse.core.exceptions import PluginException
from webpulse.reports.schemas import Finding

logger = logging.getLogger("webpulse.core.sandbox")


class SubprocessSandboxWorker:
    """Spawns and communicates with an isolated subprocess running a plugin."""

    def __init__(self, plugin_dir: Path, python_executable: Path | None = None) -> None:
        """Initialize the SubprocessSandboxWorker.

        Args:
            plugin_dir: Path to the target plugin folder.
            python_executable: Override path to isolated virtualenv python binary if needed.
        """
        self.plugin_dir = plugin_dir
        self.python_executable = python_executable or Path(sys.executable)
        self._proc: asyncio.subprocess.Process | None = None
        self._id_counter = 0
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def start(self) -> None:
        """Spawn the sandbox worker subprocess."""
        cmd = [
            str(self.python_executable),
            "-m",
            "webpulse.core.sandbox_worker",
            str(self.plugin_dir),
        ]
        try:
            logger.debug(f"Spawning sandbox worker command: {' '.join(cmd)}")
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Start background task to consume stderr and log it to prevent pipes freezing
            task = asyncio.create_task(self._log_stderr())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        except Exception as e:
            raise PluginException(f"Failed to spawn sandbox subprocess: {e}") from e

    async def _log_stderr(self) -> None:
        """Read worker stderr lines and write them to our local logs."""
        if not self._proc or not self._proc.stderr:
            return
        try:
            while True:
                line_bytes = await self._proc.stderr.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8").strip()
                if line:
                    logger.warning(f"[Sandbox-Worker-Stderr] {line}")
        except Exception as e:
            logger.debug(f"Error reading sandbox worker stderr: {e}")

    async def call(self, method: str, params: dict[str, Any]) -> Any:
        """Make a JSON-RPC 2.0 invocation call to the worker.

        Args:
            method: Method name ('on_load' or 'execute').
            params: Parameters dictionary.

        Returns:
            The parsed result returned by the worker.
        """
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise PluginException("Sandbox process is not running.")

        self._id_counter += 1
        req_id = self._id_counter
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id,
        }

        # Write request payload
        req_str = json.dumps(payload) + "\n"
        self._proc.stdin.write(req_str.encode("utf-8"))
        await self._proc.stdin.drain()

        # Read response payload
        resp_bytes = await self._proc.stdout.readline()
        if not resp_bytes:
            raise PluginException("Sandbox worker exited prematurely without writing a response.")

        try:
            resp_str = resp_bytes.decode("utf-8").strip()
            response = json.loads(resp_str)
        except Exception as e:
            raise PluginException(f"Failed to parse JSON-RPC response from worker: {e}") from e

        # Validate response envelope
        if response.get("id") != req_id:
            raise PluginException(
                f"ID mismatch in JSON-RPC response (expected {req_id}, got {response.get('id')})"
            )

        if "error" in response:
            err = response["error"]
            raise PluginException(f"Sandbox worker execution failed: {err.get('message', err)}")

        return response.get("result")

    async def execute_plugin(self, target_url: str, config: dict[str, Any]) -> list[Finding]:
        """Wrap dynamic loading execution in an easy-to-use method.

        Args:
            target_url: URL to audit.
            config: Config dictionary passed to the plugin.

        Returns:
            List of Pydantic Finding objects parsed from JSON results.
        """
        # 1. Initialize plugin in sandbox
        await self.call("on_load", {"config": config})

        # 2. Run execute target
        raw_findings = await self.call("execute", {"target": {"url": target_url}})

        # 3. Parse list of Findings
        findings: list[Finding] = []
        if isinstance(raw_findings, list):
            for data in raw_findings:
                findings.append(Finding.model_validate(data))
        return findings

    async def stop(self) -> None:
        """Close input/output pipes and terminate the worker process."""
        if self._proc:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                await self._proc.wait()
            except Exception as e:
                logger.debug(f"Error during sandbox worker teardown: {e}")
            finally:
                self._proc = None
