"""Command Line Interface (CLI) Entrypoint for WebPulse.

Supports target scanning, crawler traversal, session authentication,
plugin queries, configuration management, and POSIX pipeline exits.
"""

import argparse
import asyncio
import datetime
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from webpulse.core.auth import AuthCoordinator
from webpulse.core.config import PROFILES, AppConfig, ConfigManager
from webpulse.core.crawler import BFSWebCrawler
from webpulse.core.plugin_loader import PluginLoader
from webpulse.reports.reporter import ReportGenerator
from webpulse.reports.schemas import Severity, Target
from webpulse.utils.logging import setup_logging
from webpulse.utils.network import AsyncNetworkClient

logger = logging.getLogger("webpulse.cli")


def create_parser() -> argparse.ArgumentParser:
    """Construct the command line arguments parser hierarchy."""
    parser = argparse.ArgumentParser(
        prog="webpulse",
        description="WebPulse - Automated defensive website auditing and security scanner.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output logging verbosity (-v, -vv).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable full traceback prints and disable interception.",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable all ANSI colors in console output."
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # 1. SCAN Subcommand
    scan_parser = subparsers.add_parser("scan", help="Audit a target website URL.")
    scan_parser.add_argument("target_url", help="The target URL or domain to audit.")
    scan_parser.add_argument("-o", "--output", help="Write report to the specified file path.")
    scan_parser.add_argument(
        "-f",
        "--format",
        default="console",
        help="Report format type (console, json, html, markdown). Comma-separated list supported.",
    )
    scan_parser.add_argument(
        "-p",
        "--profile",
        default="default",
        choices=["fast", "default", "full"],
        help="Scanning preset intensity.",
    )
    scan_parser.add_argument(
        "-r", "--rate-limit", type=int, help="Limit maximum requests per second."
    )
    scan_parser.add_argument(
        "-c", "--concurrency", type=int, help="Limit maximum concurrent connections."
    )
    scan_parser.add_argument("--timeout", type=int, help="Global connection timeout in seconds.")
    scan_parser.add_argument(
        "--use-browser", action="store_true", help="Enable browser headless checks."
    )
    scan_parser.add_argument(
        "--yes-i-have-authorization",
        action="store_true",
        help="Acknowledge stress scan authorization.",
    )
    scan_parser.add_argument(
        "--crawl", action="store_true", help="Enable crawler link discovery traversal."
    )
    scan_parser.add_argument("--max-depth", type=int, help="Crawler recursion limit.")
    scan_parser.add_argument("--max-pages", type=int, help="Crawler total target limit.")
    scan_parser.add_argument("--auth-config", help="Path to credentials session file.")
    scan_parser.add_argument(
        "--allow-private-ips", action="store_true", help="Allow connections to private networks."
    )
    scan_parser.add_argument(
        "--sandbox-plugins", type=str, choices=["true", "false"], help="Toggle plugin isolation."
    )

    # 2. PLUGINS Subcommand
    plugins_parser = subparsers.add_parser("plugins", help="Manage and query plugins.")
    plugins_subparsers = plugins_parser.add_subparsers(dest="subcommand", help="Plugin subcommands")

    plugins_subparsers.add_parser("list", help="List all discovered plugins.")

    info_parser = plugins_subparsers.add_parser("info", help="Show manifest details for a plugin.")
    info_parser.add_argument("plugin_name", help="Slug name of the plugin.")

    validate_parser = plugins_subparsers.add_parser("validate", help="Validate a plugin directory.")
    validate_parser.add_argument("plugin_path", help="Path to the plugin folder.")

    # 3. CONFIG Subcommand
    config_parser = subparsers.add_parser("config", help="Manage configuration profiles.")
    config_subparsers = config_parser.add_subparsers(
        dest="subcommand", help="Configuration subcommands"
    )

    config_subparsers.add_parser("show", help="Show current merged configuration parameters.")

    set_parser = config_subparsers.add_parser("set", help="Set user global config settings.")
    set_parser.add_argument("key", help="Configuration dot-notation key (e.g. core.rate_limit).")
    set_parser.add_argument("value", help="Value to assign.")

    config_subparsers.add_parser("validate", help="Validate workspace configurations file.")

    return parser


def coerce_value(val_str: str) -> Any:
    """Coerce string value to standard config type representation."""
    val_lower = val_str.lower()
    if val_lower == "true":
        return True
    if val_lower == "false":
        return False
    try:
        return int(val_str)
    except ValueError:
        try:
            return float(val_str)
        except ValueError:
            return val_str


async def handle_scan(args: argparse.Namespace, config: AppConfig) -> int:
    """Run target site scanning suite and export reports."""
    # Prefix protocol if missing
    target_url = args.target_url
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        target_url = "https://" + target_url

    client = AsyncNetworkClient(allow_private_ips=config.network.allow_private_ips)
    start_time = time.time()

    try:
        pages_discovered = 1
        pages_scanned = 1
        targets = [Target(url=target_url)]
        scanned_urls = [target_url]

        # 1. Crawl if enabled
        if config.crawler.enabled:
            logger.info("Initializing BFS crawler...")
            crawler = BFSWebCrawler(
                max_depth=config.crawler.max_depth,
                max_pages=config.crawler.max_pages,
                allowed_domains=[],
                exclude_patterns=config.crawler.exclude_patterns,
            )
            targets = await crawler.crawl(Target(url=target_url), client)
            scanned_urls = [t.url for t in targets]
            pages_discovered = len(scanned_urls)
            pages_scanned = len(scanned_urls)

        # 2. Establish Auth Session
        auth_coord = AuthCoordinator(config.auth.model_dump())
        auth_success = await auth_coord.establish_session(client)
        auth_status = "DISABLED"
        if config.auth.enabled:
            auth_status = "SUCCESS" if auth_success else "FAILED"

        # Inject session tokens
        if auth_success and config.auth.enabled:
            injected_headers = auth_coord.inject_headers({})
            for k, v in injected_headers.items():
                if k.lower() == "cookie":
                    for cookie_part in v.split(";"):
                        if "=" in cookie_part:
                            ck, cv = cookie_part.strip().split("=", 1)
                            client._client.cookies.set(ck, cv)
                else:
                    client._client.headers[k] = v

        # 3. Discover Plugins
        loader = PluginLoader()
        search_paths = [
            Path(__file__).parent.parent / "modules",
            Path.cwd() / "plugins",
        ]
        plugin_classes = loader.discover_plugins(search_paths)

        active_plugins = []
        for cls in plugin_classes:
            plugin = cls()
            plugin_name = plugin.metadata.name

            enabled = True
            if hasattr(config.modules, plugin_name):
                enabled = getattr(config.modules, plugin_name).enabled

            if enabled:
                mod_conf = {}
                if hasattr(config.modules, plugin_name):
                    attr = getattr(config.modules, plugin_name)
                    if hasattr(attr, "model_dump"):
                        mod_conf = attr.model_dump()
                await plugin.on_load(mod_conf)
                active_plugins.append(plugin)

        logger.info(f"Loaded {len(active_plugins)} active plugins.")

        # 4. Execute Scans
        findings = []
        for target in targets:
            logger.info(f"Scanning target page: {target.url}")
            for plugin in active_plugins:
                is_third_party = not str(Path(plugin.__class__.__module__).resolve()).startswith(
                    str(Path(__file__).parent.parent.resolve())
                )

                use_sandbox = config.core.sandbox_plugins and is_third_party

                try:
                    if use_sandbox:
                        from webpulse.core.sandbox import SubprocessSandboxWorker

                        plugin_module = sys.modules[plugin.__class__.__module__]
                        assert plugin_module.__file__ is not None
                        plugin_dir = Path(plugin_module.__file__).parent
                        worker = SubprocessSandboxWorker(plugin_dir)
                        await worker.start()
                        try:
                            pf = await worker.execute_plugin(target.url, plugin.config)
                            findings.extend(pf)
                        finally:
                            await worker.stop()
                    else:
                        pf = await plugin.execute(target, client)
                        findings.extend(pf)
                except Exception as e:
                    logger.error(f"Plugin '{plugin.metadata.name}' failed on '{target.url}': {e}")

        # 5. Generate metrics and scores
        duration = time.time() - start_time
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        generator = ReportGenerator(
            target_url=target_url,
            scan_timestamp=timestamp,
            duration_seconds=duration,
            findings=findings,
            auth_enabled=config.auth.enabled,
            auth_status=auth_status,
            max_depth=config.crawler.max_depth,
            max_pages=config.crawler.max_pages,
            pages_discovered=pages_discovered,
            pages_scanned=pages_scanned,
            scanned_urls=scanned_urls,
        )

        # 6. Output Reports
        formats = [f.strip().lower() for f in args.format.split(",")]

        # Always output to console if console is chosen or by default
        if "console" in formats:
            console_str = generator.to_console()
            try:
                sys.stdout.write(console_str + "\n")
            except UnicodeEncodeError:
                enc = sys.stdout.encoding or "utf-8"
                sys.stdout.buffer.write(console_str.encode(enc, errors="replace") + b"\n")
                sys.stdout.flush()

        if args.output:
            out_path = Path(args.output)
            # Create parent directories
            out_path.parent.mkdir(parents=True, exist_ok=True)

            if len(formats) == 1:
                # Write directly to out_path
                fmt = formats[0]
                if fmt == "json":
                    out_path.write_text(generator.to_json(), encoding="utf-8")
                elif fmt == "markdown":
                    out_path.write_text(generator.to_markdown(), encoding="utf-8")
                elif fmt == "html":
                    out_path.write_text(generator.to_html(), encoding="utf-8")
            else:
                # Write to multi-files appending extensions
                for fmt in formats:
                    if fmt == "json":
                        out_path.with_suffix(".json").write_text(
                            generator.to_json(), encoding="utf-8"
                        )
                    elif fmt == "markdown":
                        out_path.with_suffix(".md").write_text(
                            generator.to_markdown(), encoding="utf-8"
                        )
                    elif fmt == "html":
                        out_path.with_suffix(".html").write_text(
                            generator.to_html(), encoding="utf-8"
                        )
        else:
            # Handle config reporting directories
            out_dir = Path(config.reporting.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            domain_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', target_url)
            domain_safe = re.sub(r'_+', '_', domain_safe).strip('_')
            ts_safe = timestamp.replace(":", "-")
            name_base = config.reporting.report_name_template.format(
                target=domain_safe, timestamp=ts_safe
            )

            # Export configured formats (excluding console)
            for raw_fmt in config.reporting.formats:
                fmt = raw_fmt.strip().lower()
                if fmt == "json":
                    (out_dir / f"{name_base}.json").write_text(
                        generator.to_json(), encoding="utf-8"
                    )
                elif fmt == "markdown":
                    (out_dir / f"{name_base}.md").write_text(
                        generator.to_markdown(), encoding="utf-8"
                    )
                elif fmt == "html":
                    (out_dir / f"{name_base}.html").write_text(
                        generator.to_html(), encoding="utf-8"
                    )

        # 7. Evaluate POSIX Exit Thresholds
        if config.core.fail_on_critical:
            criticals = [f for f in findings if f.severity == Severity.CRITICAL]
            if criticals:
                logger.error(
                    f"Scan finished, but {len(criticals)} critical severity findings were discovered."
                )
                return 3

        if generator.scores["overall_health_score"] < config.core.fail_on_health:
            logger.error(
                f"Overall Health Score {generator.scores['overall_health_score']}% "
                f"fell below threshold limit of {config.core.fail_on_health}%."
            )
            return 2

        return 0

    finally:
        await client.close()


def handle_plugins(args: argparse.Namespace) -> int:
    """Query, list, and validate plugin manifests."""
    loader = PluginLoader()
    search_paths = [
        Path(__file__).parent.parent / "modules",
        Path.cwd() / "plugins",
    ]

    if args.subcommand == "list":
        classes = loader.discover_plugins(search_paths)
        print("Discovered WebPulse Plugins:")
        print("-" * 50)
        for cls in classes:
            p = cls()
            print(f"Name:        {p.metadata.name}")
            print(f"Category:    {p.metadata.category}")
            print(f"Version:     {p.metadata.version}")
            print("-" * 50)
        return 0

    if args.subcommand == "info":
        loader.discover_plugins(search_paths)
        name = args.plugin_name
        if name not in loader.manifests:
            print(f"Plugin '{name}' not found.")
            return 1
        manifest = loader.manifests[name]
        print(yaml.dump(manifest.model_dump(), default_flow_style=False))
        return 0

    if args.subcommand == "validate":
        try:
            plugin_dir = Path(args.plugin_path)
            manifest_path = plugin_dir / "manifest.yaml"
            if not manifest_path.exists():
                manifest_path = plugin_dir / "manifest.yml"
            if not manifest_path.exists():
                print(f"Manifest file not found in: {args.plugin_path}")
                return 1
            loader.load_plugin(plugin_dir, manifest_path)
            print("Plugin validated successfully!")
            return 0
        except Exception as e:
            print(f"Validation failed: {e}")
            return 1

    return 1


def handle_config(args: argparse.Namespace) -> int:
    """Manage local/global configurations."""
    config_manager = ConfigManager()

    if args.subcommand == "show":
        try:
            config = config_manager.load_config()
            print(yaml.dump(config.model_dump(), default_flow_style=False))
            return 0
        except Exception as e:
            print(f"Failed to load config: {e}")
            return 1

    if args.subcommand == "set":
        try:
            user_config_path = Path.home() / ".webpulse" / "config.yaml"
            user_config_path.parent.mkdir(parents=True, exist_ok=True)

            config_dict: dict[str, Any] = {}
            if user_config_path.exists():
                with user_config_path.open("r", encoding="utf-8") as f:
                    config_dict = yaml.safe_load(f) or {}

            key = args.key
            value = coerce_value(args.value)

            parts = key.split(".")
            current = config_dict
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

            with user_config_path.open("w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False)

            print(f"Updated setting: {key} = {value}")
            return 0
        except Exception as e:
            print(f"Failed to update setting: {e}")
            return 1

    if args.subcommand == "validate":
        try:
            config_manager.load_config()
            print("Configuration file is valid!")
            return 0
        except Exception as e:
            print(f"Configuration is invalid: {e}")
            return 1

    return 1


def main() -> None:
    """Main process controller entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Resolve core overrides
    config_manager = ConfigManager()
    try:
        config = config_manager.load_config()
    except Exception:
        sys.exit(1)

    # Setup profile overlays
    if args.command == "scan":
        if args.profile:
            config.profile = args.profile
            if args.profile in PROFILES:
                profile_settings = PROFILES[args.profile]
                if "core" in profile_settings:
                    for k, v in profile_settings["core"].items():
                        setattr(config.core, k, v)
                if "modules" in profile_settings:
                    for k, v in profile_settings["modules"].items():
                        if hasattr(config.modules, k):
                            mod_model = getattr(config.modules, k)
                            for mk, mv in v.items():
                                setattr(mod_model, mk, mv)

        if args.rate_limit is not None:
            config.core.rate_limit = args.rate_limit
        if args.concurrency is not None:
            config.core.max_connections = args.concurrency
        if args.timeout is not None:
            config.core.timeout = args.timeout
        if args.allow_private_ips:
            config.network.allow_private_ips = True
        if args.crawl:
            config.crawler.enabled = True
        if args.max_depth is not None:
            config.crawler.max_depth = args.max_depth
        if args.max_pages is not None:
            config.crawler.max_pages = args.max_pages
        if args.sandbox_plugins:
            config.core.sandbox_plugins = args.sandbox_plugins == "true"

        if args.auth_config is not None:
            try:
                auth_path = Path(args.auth_config)
                if not auth_path.exists():
                    sys.exit(1)
                with auth_path.open("r", encoding="utf-8") as f:
                    if auth_path.suffix in (".yaml", ".yml"):
                        auth_data = yaml.safe_load(f) or {}
                    else:
                        auth_data = json.load(f) or {}
                from webpulse.core.config import AuthConfig

                config.auth = AuthConfig.model_validate(auth_data)
            except Exception:
                sys.exit(1)

    # 1. Execute Scan Subcommand
    if args.command == "scan":
        log_level = logging.WARNING
        if args.verbose == 1:
            log_level = logging.INFO
        elif args.verbose >= 2:
            log_level = logging.DEBUG
        setup_logging(log_level)

        if args.debug:
            exit_code = asyncio.run(handle_scan(args, config))
        else:
            try:
                exit_code = asyncio.run(handle_scan(args, config))
            except KeyboardInterrupt:
                logger.error("Scan canceled by user.")
                exit_code = 130
            except Exception as e:
                logger.error(f"Scan failed with system error: {e}")
                exit_code = 1
        sys.exit(exit_code)

    # 2. Execute Plugins Subcommand
    elif args.command == "plugins":
        if not args.subcommand:
            sys.exit(1)
        sys.exit(handle_plugins(args))

    # 3. Execute Config Subcommand
    elif args.command == "config":
        if not args.subcommand:
            sys.exit(1)
        sys.exit(handle_config(args))


if __name__ == "__main__":
    main()
