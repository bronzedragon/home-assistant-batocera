"""Batocera API availability binary sensor."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .naming import entity_device_name


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BatoceraOnline(entry.runtime_data, entry)])
    async_add_entities([
        BatoceraWolDiagnostic(entry, "wol_supported", "Wake-on-LAN Supported"),
        BatoceraWolDiagnostic(entry, "wol", "Wake-on-LAN Enabled"),
    ])


class BatoceraOnline(CoordinatorEntity, BinarySensorEntity):
    """Indicate whether the EmulationStation API is reachable."""

    _attr_has_entity_name = True
    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entity_device_name(entry),
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.last_update_success


class BatoceraWolDiagnostic(BinarySensorEntity):
    """Cached WoL information, not live NIC telemetry."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, key, title):
        self._entry = entry
        self._key = key
        self._attr_name = title
        self._attr_unique_id = f"{entry.entry_id}_diagnostic_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entity_device_name(entry),
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def available(self):
        if self._key == "wol_supported":
            return self._entry.data.get(self._key) in ("true", "false")
        return self._entry.data.get(self._key) in ("enabled", "disabled", "unsupported")

    @property
    def is_on(self):
        if not self.available:
            return None
        if self._key == "wol_supported":
            return self._entry.data[self._key] == "true"
        return self._entry.data[self._key] == "enabled"
