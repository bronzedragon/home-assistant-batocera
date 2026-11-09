"""Console and game selectors for Batocera."""

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .naming import entity_device_name


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([
        BatoceraBrowseSelect(coordinator, entry, "console"),
        BatoceraBrowseSelect(coordinator, entry, "game"),
    ])


class BatoceraBrowseSelect(CoordinatorEntity, SelectEntity):
    """Select a console then choose a game without launching it."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, kind):
        super().__init__(coordinator)
        self._kind = kind
        self._attr_name = "Browse Console" if kind == "console" else "Browse Game"
        self._attr_unique_id = f"{entry.entry_id}_browse_{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entity_device_name(entry),
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def options(self):
        browser = self.coordinator.browser
        return browser.console_options if self._kind == "console" else browser.game_options

    @property
    def current_option(self):
        browser = self.coordinator.browser
        return (
            browser.current_console_option
            if self._kind == "console"
            else browser.current_game_option
        )

    async def async_select_option(self, option: str) -> None:
        browser = self.coordinator.browser
        if self._kind == "console":
            await browser.choose_console(option)
        else:
            browser.choose_game(option)
