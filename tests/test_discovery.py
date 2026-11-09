"""Zeroconf setup regression tests without requiring a running HA instance."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock


def module(name):
    item = sys.modules.get(name)
    if item is None:
        item = types.ModuleType(name)
        sys.modules[name] = item
    return item


vol = module("voluptuous")
vol.Required = lambda name, **kwargs: name
vol.Schema = lambda arg: arg
vol.All = lambda *args: args
vol.Coerce = lambda arg: arg
vol.Range = lambda **kwargs: kwargs

ha = module("homeassistant")
config_entries = module("homeassistant.config_entries")


class FakeConfigFlow:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

    def __init__(self):
        self.hass = types.SimpleNamespace(
            config_entries=types.SimpleNamespace(async_update_entry=self.update_entry)
        )
        self.entries = []
        self.unique_id = None

    def update_entry(self, entry, data):
        entry.data = data

    async def async_set_unique_id(self, value):
        self.unique_id = value

    def _abort_if_unique_id_configured(self, updates=None):
        for entry in self.entries:
            if entry.unique_id == self.unique_id:
                if updates:
                    entry.data.update(updates)
                raise AssertionError("configured entry abort")

    def _async_current_entries(self):
        return self.entries

    def async_abort(self, reason):
        return {"type": "abort", "reason": reason}

    def _set_confirm_only(self):
        self.confirm_only = True

    def async_show_form(self, step_id, **kwargs):
        return {"type": "form", "step_id": step_id, **kwargs}

    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}


config_entries.ConfigFlow = FakeConfigFlow
ha.config_entries = config_entries

const = module("homeassistant.const")
const.CONF_HOST = "host"
const.CONF_PORT = "port"

client = module("homeassistant.helpers.aiohttp_client")
client.async_get_clientsession = lambda hass: object()

registry = module("homeassistant.helpers.device_registry")
registry.format_mac = lambda mac: mac.lower()

serviceinfo = module("homeassistant.helpers.service_info.zeroconf")
serviceinfo.ZeroconfServiceInfo = type("ZeroconfServiceInfo", (), {})

package = module("batocera_discovery_tests")
package.__path__ = []
api = module("batocera_discovery_tests.api")
api.BatoceraApiError = type("BatoceraApiError", (Exception,), {})


class FakeApi:
    def __init__(self, session, host, port):
        self.host, self.port = host, port

    async def capabilities(self):
        return {"Version": "43o.1"}


api.BatoceraApi = FakeApi
constants = module("batocera_discovery_tests.const")
constants.DEFAULT_PORT = 1234
constants.DOMAIN = "batocera"

source = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "batocera" / "config_flow.py"
)
spec = importlib.util.spec_from_file_location(
    "batocera_discovery_tests.config_flow", source
)
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


def advertise(mac="3c:52:82:63:12:63", api_name="emulationstation"):
    return types.SimpleNamespace(
        host="10.8.76.244",
        hostname="ginryuu.local.",
        port=1234,
        properties={
            "api": api_name,
            "mac": mac,
            "wol": "enabled",
            "wol_supported": "true",
            "model": "EliteDesk",
        },
    )


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.flow = discovery.BatoceraConfigFlow()

    async def test_discovery_requires_confirmation(self):
        result = await self.flow.async_step_zeroconf(advertise())
        self.assertEqual(result["step_id"], "discovery_confirm")
        self.assertEqual(self.flow.unique_id, "3c:52:82:63:12:63")
        result = await self.flow.async_step_discovery_confirm({})
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"]["wol"], "enabled")
        self.assertEqual(result["data"]["mac"], "3c:52:82:63:12:63")

    async def test_wrong_api_rejected(self):
        result = await self.flow.async_step_zeroconf(
            advertise(api_name="something_else")
        )
        self.assertEqual(result["reason"], "not_batocera")

    async def test_invalid_mac_rejected(self):
        result = await self.flow.async_step_zeroconf(advertise(mac="invalid"))
        self.assertEqual(result["reason"], "invalid_discovery")

    async def test_existing_manual_entry_updated_without_duplicate(self):
        entry = types.SimpleNamespace(
            unique_id="10.8.76.244:1234",
            data={"host": "10.8.76.244", "port": 1234},
        )
        self.flow.entries.append(entry)
        result = await self.flow.async_step_zeroconf(advertise())
        self.assertEqual(result["reason"], "already_configured")
        self.assertEqual(entry.data["mac"], "3c:52:82:63:12:63")
        self.assertEqual(entry.data["wol"], "enabled")

    async def test_failed_capability_check_aborts(self):
        self.flow._check_api = AsyncMock(return_value=False)
        result = await self.flow.async_step_zeroconf(advertise())
        self.assertEqual(result["reason"], "cannot_connect")


if __name__ == "__main__":
    unittest.main()
