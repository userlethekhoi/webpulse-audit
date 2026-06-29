"""System information utility for Kaydus.

Retrieves operating system details, CPU specs, core count, and WebPulse authentication status.
"""

from __future__ import annotations

import os
import platform

from webpulse.core.config import ConfigManager


def get_sys_info() -> dict[str, str]:
    """Retrieve current system information.

    Returns:
        Dictionary containing OS, CPU, cores, and auth status information.
    """
    # 1. OS Info
    os_name = platform.system()
    os_release = platform.release()
    os_str = f"{os_name} {os_release}"

    # 2. CPU info
    cpu_arch = platform.machine()
    # Attempt to get a more user-friendly processor name
    processor = platform.processor() or cpu_arch
    if not processor:
        processor = "Unknown"

    # 3. CPU Cores
    cores = os.cpu_count() or 1
    cpu_str = f"{processor} ({cores} Cores)"

    # 4. WebPulse Auth Status
    auth_status = "DISABLED"
    try:
        config = ConfigManager().load_config()
        if config.auth.enabled:
            auth_status = "ENABLED"
    except Exception:
        pass

    return {
        "os": os_str,
        "cpu": cpu_str,
        "auth": auth_status,
    }
