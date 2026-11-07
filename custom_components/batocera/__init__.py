"""Batocera Linux integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BatoceraApi
from .browser import BatoceraBrowser
from .coordinator import BatoceraCoordinator

PLATFORMS = ["sensor", "binary_sensor", "select"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize a Batocera host."""
    api = BatoceraApi(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT]
    )
    coordinator = BatoceraCoordinator(hass, entry, api)
    coordinator.browser = BatoceraBrowser(coordinator)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
