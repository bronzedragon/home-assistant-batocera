"""Opt-in SSH power management using Batocera's native shutdown utility."""

from __future__ import annotations

import asyncio
from pathlib import Path

import asyncssh

POWER_COMMANDS = {
    "shutdown": "batocera-es-swissknife --shutdown",
    "reboot": "batocera-es-swissknife --reboot",
}
DEFAULT_SSH_KEY = "/config/.ssh/id_ed25519"
DEFAULT_KNOWN_HOSTS = "/config/.ssh/known_hosts"


def power_settings(entry) -> dict:
    """Resolve per-entry SSH settings, never from global environment defaults."""
    options = entry.options
    return {
        "enabled": options.get("power_enabled", False) is True,
        "port": options.get("ssh_port", 22),
        "key": options.get("ssh_key_path", DEFAULT_SSH_KEY),
        "known_hosts": options.get("ssh_known_hosts", DEFAULT_KNOWN_HOSTS),
    }


def settings_ready(entry) -> bool:
    """Never show a functional destructive action without explicit opt-in."""
    settings = power_settings(entry)
    return bool(
        settings["enabled"]
        and isinstance(settings["port"], int)
        and 1 <= settings["port"] <= 65535
        and settings["key"]
        and settings["known_hosts"]
    )


async def send_power_command(entry, action: str) -> None:
    """Authenticate via an explicit key and verify the target's SSH host key."""
    if action not in POWER_COMMANDS:
        raise ValueError("Unsupported Batocera power operation")
    if not settings_ready(entry):
        raise ValueError("SSH power management has not been enabled")

    settings = power_settings(entry)
    for path in (settings["key"], settings["known_hosts"]):
        if not await asyncio.to_thread(Path(path).is_file):
            raise FileNotFoundError(f"SSH credential file not found: {path}")

    async with asyncssh.connect(
        entry.data["host"],
        port=settings["port"],
        username="root",
        client_keys=[settings["key"]],
        known_hosts=settings["known_hosts"],
        connect_timeout=10,
        login_timeout=10,
        agent_path=None,
    ) as connection:
        # Schedule after SSH exits, so the service can report success before
        # its own network connection is interrupted by shutdown or reboot.
        # The only remote commands are hardcoded in POWER_COMMANDS.
        command = POWER_COMMANDS[action]
        result = await asyncio.wait_for(
            connection.run(
                "nohup sh -c 'sleep 2; "
                + command
                + "' >/dev/null 2>&1 </dev/null &",
                check=False,
            ),
            timeout=10,
        )
        if result.exit_status != 0:
            raise RuntimeError(
                f"Batocera rejected {action} (SSH exit {result.exit_status})"
            )
