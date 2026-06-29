"""Example script to demonstrate WebPulse configuration parsing and logging initialization.

Runs as a manual verification utility for Sprint 1.
"""

import logging
from pathlib import Path

from webpulse.core.config import ConfigManager
from webpulse.core.di import Container
from webpulse.utils.logging import setup_logging

logger = logging.getLogger("webpulse.examples")


def main() -> None:
    # 1. Initialize logging
    setup_logging(level=logging.DEBUG)
    logger.info("Initializing WebPulse Configuration Loader example...")

    # 2. Setup Dependency Injection Container
    container = Container()
    logger.info("DI Container initialized successfully.")

    # 3. Resolve configurations
    config_manager: ConfigManager = container.config_manager

    # We will write a dummy configuration file to show the loader in action
    temp_config_path = Path.cwd() / "examples" / "temp_webpulse.yaml"
    try:
        logger.info(f"Loading custom configuration from {temp_config_path}...")
        config = config_manager.load_config(temp_config_path)

        logger.info("=== Merged WebPulse Configurations ===")
        logger.info(f"Core Rate Limit:       {config.core.rate_limit} req/sec")
        logger.info(f"Core Max Connections:  {config.core.max_connections}")
        logger.info(f"SSRF Safety Guard:     {not config.network.allow_private_ips}")
        logger.info(f"Active Profile Preset: {config.profile}")
        logger.info(f"SEO Analyzer Enabled:  {config.modules.seo.enabled}")
        logger.info(f"SSL Verification Days: {config.modules.ssl.verify_expiry_days}")
        logger.info("=======================================")

    except Exception as e:
        logger.error(f"Error during configuration loading: {e}")


if __name__ == "__main__":
    main()
