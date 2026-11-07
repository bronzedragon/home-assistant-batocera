"""Batocera API availability binary sensor."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([BatoceraOnline(entry.runtime_data, entry)])


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
            name=entry.title,
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.last_update_success
