"""Batocera status sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities(
        [BatoceraSensor(coordinator, entry, key) for key in (
            "version", "system_count", "game_count", "state", "current_game", "current_console"
        )]
    )


class BatoceraSensor(CoordinatorEntity, SensorEntity):
    """A read-only sensor backed by shared coordinator state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = key.replace("_", " ").title()
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def native_value(self):
        data = self.coordinator.data
        game = data["running_game"] or {}
        if self._key == "state":
            return "playing" if game else "idle" if data["idle"] else "busy"
        if self._key == "current_game":
            return game.get("name") or game.get("game")
        if self._key == "current_console":
            return game.get("systemName") or game.get("system")
        return data[self._key]

    @property
    def extra_state_attributes(self):
        if self._key == "system_count":
            return {"consoles": [s.get("fullname", s.get("name")) for s in self.coordinator.data["systems"]]}
        return None
