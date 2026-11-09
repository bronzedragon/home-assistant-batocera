"""Regression tests for cached Batocera diagnostic entity values."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest


def stub(name):
    result = sys.modules.get(name)
    if result is None:
        result = types.ModuleType(name)
        sys.modules[name] = result
    return result


sensor = stub("homeassistant.components.sensor")
sensor.SensorEntity = type("SensorEntity", (), {})
binary = stub("homeassistant.components.binary_sensor")
binary.BinarySensorEntity = type("BinarySensorEntity", (), {})
binary.BinarySensorDeviceClass = types.SimpleNamespace(CONNECTIVITY="connectivity")
registry = stub("homeassistant.helpers.device_registry")
registry.DeviceInfo = dict
entity = stub("homeassistant.helpers.entity")
entity.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
coordinator = stub("homeassistant.helpers.update_coordinator")
coordinator.CoordinatorEntity = type("CoordinatorEntity", (), {
    "__init__": lambda self, update_coordinator: None,
})

package = stub("batocera_diagnostics_tests")
package.__path__ = []
const = stub("batocera_diagnostics_tests.const")
const.DOMAIN = "batocera"
naming = stub("batocera_diagnostics_tests.naming")
naming.entity_device_name = lambda entry: "ginryuu"


def load(component):
    path = Path(__file__).resolve().parents[1] / "custom_components" / "batocera" / (component + ".py")
    spec = importlib.util.spec_from_file_location(
        "batocera_diagnostics_tests." + component, path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


wol = load("wol")
sensors = load("sensor")
binary_sensors = load("binary_sensor")


def entry(**data):
    return types.SimpleNamespace(entry_id="test_entry", data=data)


class DiagnosticsTests(unittest.TestCase):
    def test_mac_remains_available_without_api(self):
        item = sensors.BatoceraDiagnosticSensor(
            entry(mac="3c:52:82:63:12:63"), "mac", "MAC Address"
        )
        self.assertTrue(item.available)
        self.assertEqual(item.native_value, "3c:52:82:63:12:63")

    def test_missing_discovery_data_is_unavailable(self):
        item = sensors.BatoceraDiagnosticSensor(
            entry(), "model", "Hardware Model"
        )
        self.assertFalse(item.available)

    def test_wol_supported(self):
        item = binary_sensors.BatoceraWolDiagnostic(
            entry(wol_supported="true"), "wol_supported", "Wake-on-LAN Supported"
        )
        self.assertTrue(item.available)
        self.assertTrue(item.is_on)

    def test_wol_unsupported(self):
        item = binary_sensors.BatoceraWolDiagnostic(
            entry(wol_supported="false"), "wol_supported", "Wake-on-LAN Supported"
        )
        self.assertTrue(item.available)
        self.assertFalse(item.is_on)

    def test_wol_enabled(self):
        item = binary_sensors.BatoceraWolDiagnostic(
            entry(wol="enabled"), "wol", "Wake-on-LAN Enabled"
        )
        self.assertTrue(item.available)
        self.assertTrue(item.is_on)

    def test_wol_disabled(self):
        item = binary_sensors.BatoceraWolDiagnostic(
            entry(wol="disabled"), "wol", "Wake-on-LAN Enabled"
        )
        self.assertTrue(item.available)
        self.assertFalse(item.is_on)

    def test_unknown_wol_does_not_claim_disabled(self):
        for state in ("unknown", None):
            item = binary_sensors.BatoceraWolDiagnostic(
                entry(wol=state), "wol", "Wake-on-LAN Enabled"
            )
            self.assertFalse(item.available)
            self.assertIsNone(item.is_on)


if __name__ == "__main__":
    unittest.main()
