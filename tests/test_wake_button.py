"""Regression tests for Wake Batocera button and packet format."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


def stub(name):
    result = sys.modules.get(name)
    if result is None:
        result = types.ModuleType(name)
        sys.modules[name] = result
    return result


stub("homeassistant.components.button").ButtonEntity = type("ButtonEntity", (), {})
errors = stub("homeassistant.exceptions")
if not hasattr(errors, "HomeAssistantError"):
    errors.HomeAssistantError = type("HomeAssistantError", (Exception,), {})
stub("homeassistant.helpers.device_registry").DeviceInfo = dict
package = stub("batocera_wake_tests")
package.__path__ = []
stub("batocera_wake_tests.const").DOMAIN = "batocera"
stub("batocera_wake_tests.naming").entity_device_name = lambda entry: "ginryuu"

wol_source = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "batocera" / "wol.py"
)
wol_spec = importlib.util.spec_from_file_location(
    "batocera_wake_tests.wol", wol_source
)
wol_module = importlib.util.module_from_spec(wol_spec)
sys.modules[wol_spec.name] = wol_module
wol_spec.loader.exec_module(wol_module)

source = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "batocera" / "button.py"
)
spec = importlib.util.spec_from_file_location(
    "batocera_wake_tests.button", source
)
wake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wake)


class MockSocket:
    def __init__(self):
        self.sent = []
        self.options = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def setsockopt(self, *args):
        self.options.append(args)

    def sendto(self, packet, address):
        self.sent.append((packet, address))


class FakeHass:
    def __init__(self):
        self.calls = []

    async def async_add_executor_job(self, func, *args):
        self.calls.append((func, args))


class WakeButtonTests(unittest.IsolatedAsyncioTestCase):
    def test_recover_mac_from_unique_id(self):
        entry = types.SimpleNamespace(
            entry_id="abc", data={}, options={},
            unique_id="3c:52:82:63:12:63",
        )
        self.assertEqual(wol_module.effective_mac(entry), "3c:52:82:63:12:63")
        self.assertTrue(wake.BatoceraWakeButton(FakeHass(), entry).available)

    def test_options_mac_override_survives_missing_discovery(self):
        entry = types.SimpleNamespace(
            entry_id="abc", data={}, options={"mac": "3C:52:82:63:12:63"},
            unique_id="10.8.76.244:1234",
        )
        self.assertEqual(wol_module.effective_mac(entry), "3c:52:82:63:12:63")
        self.assertTrue(wake.BatoceraWakeButton(FakeHass(), entry).available)

    def test_packet_bytes_and_broadcast(self):
        sock = MockSocket()
        with patch.object(wake.socket, "socket", return_value=sock):
            wake.send_magic_packet("3c:52:82:63:12:63")
        raw = bytes.fromhex("3c5282631263")
        self.assertEqual(sock.sent, [(bytes([255]) * 6 + raw * 16, ("255.255.255.255", 9))])
        self.assertIn(
            (wake.socket.SOL_SOCKET, wake.socket.SO_BROADCAST, 1), sock.options
        )

    def test_reject_invalid_and_multicast_mac(self):
        for mac in (None, "", "not-a-mac", "00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff"):
            self.assertFalse(wake.valid_wol_mac(mac))
            with self.assertRaises(ValueError):
                wake.send_magic_packet(mac)

    async def test_wake_available_even_if_api_offline(self):
        hass = FakeHass()
        entry = types.SimpleNamespace(
            entry_id="abc", data={"mac": "3c:52:82:63:12:63", "wol_supported": "true"}
        )
        button = wake.BatoceraWakeButton(hass, entry)
        self.assertTrue(button.available)
        await button.async_press()
        self.assertEqual(hass.calls, [(wake.send_magic_packet, ("3c:52:82:63:12:63", "255.255.255.255"))])

    async def test_configured_subnet_broadcast_used(self):
        hass = FakeHass()
        entry = types.SimpleNamespace(
            entry_id="abc", unique_id=None, data={"mac": "3c:52:82:63:12:63"},
            options={"wol_broadcast": "10.8.76.255"},
        )
        button = wake.BatoceraWakeButton(hass, entry)
        await button.async_press()
        self.assertEqual(
            hass.calls,
            [(wake.send_magic_packet, ("3c:52:82:63:12:63", "10.8.76.255"))],
        )
        sock = MockSocket()
        with patch.object(wake.socket, "socket", return_value=sock):
            wake.send_magic_packet("3c:52:82:63:12:63", "10.8.76.255")
        self.assertEqual(sock.sent[0][1], ("10.8.76.255", 9))

    async def test_no_mac_or_unsupported_disables_button(self):
        for data in ({}, {"mac": "3c:52:82:63:12:63", "wol_supported": "false"}):
            hass = FakeHass()
            button = wake.BatoceraWakeButton(
                hass, types.SimpleNamespace(entry_id="abc", data=data)
            )
            self.assertFalse(button.available)
            with self.assertRaises(wake.HomeAssistantError):
                await button.async_press()
            self.assertFalse(hass.calls)


if __name__ == "__main__":
    unittest.main()
