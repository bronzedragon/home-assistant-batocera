"""Test safe per-device Batocera SSH power-management behavior."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

fake_ssh = types.ModuleType("asyncssh")
sys.modules.setdefault("asyncssh", fake_ssh)
package = types.ModuleType("batocera_power_tests")
package.__path__ = []
sys.modules[package.__name__] = package

path = Path(__file__).resolve().parents[1] / "custom_components" / "batocera" / "power.py"
spec = importlib.util.spec_from_file_location("batocera_power_tests.power", path)
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


def entry(enabled=True, **overrides):
    options = {
        "power_enabled": enabled,
        "ssh_port": 22,
        "ssh_key_path": "/config/.ssh/id_ed25519",
        "ssh_known_hosts": "/config/.ssh/known_hosts",
    }
    options.update(overrides)
    return types.SimpleNamespace(
        data={"host": "10.8.76.244"}, options=options,
    )


class FakeConnection:
    def __init__(self):
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def run(self, command, check):
        self.commands.append((command, check))
        return types.SimpleNamespace(exit_status=0)


class PowerTests(unittest.IsolatedAsyncioTestCase):
    async def test_opt_in_required(self):
        self.assertFalse(power.settings_ready(entry(enabled=False)))
        with self.assertRaises(ValueError):
            await power.send_power_command(entry(enabled=False), "shutdown")

    async def test_arbitrary_commands_blocked(self):
        with self.assertRaises(ValueError):
            await power.send_power_command(entry(), "rm -rf /")

    async def test_shutdown_uses_native_batocera_command(self):
        connection = FakeConnection()
        fake_ssh.connect = lambda *args, **kwargs: connection
        with patch.object(power.Path, "is_file", return_value=True):
            await power.send_power_command(entry(), "shutdown")
        self.assertEqual(len(connection.commands), 1)
        command, check = connection.commands[0]
        self.assertIn("batocera-es-swissknife --shutdown", command)
        self.assertNotIn("--reboot", command)
        self.assertFalse(check)

    async def test_reboot_uses_native_batocera_command(self):
        connection = FakeConnection()
        fake_ssh.connect = lambda *args, **kwargs: connection
        with patch.object(power.Path, "is_file", return_value=True):
            await power.send_power_command(entry(), "reboot")
        self.assertIn("batocera-es-swissknife --reboot", connection.commands[0][0])

    async def test_missing_key_blocks_command(self):
        connection = FakeConnection()
        fake_ssh.connect = lambda *args, **kwargs: connection
        with patch.object(power.Path, "is_file", return_value=False):
            with self.assertRaises(FileNotFoundError):
                await power.send_power_command(entry(), "shutdown")
        self.assertFalse(connection.commands)


if __name__ == "__main__":
    unittest.main()
