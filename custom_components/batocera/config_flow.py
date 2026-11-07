"""User configuration for the Batocera HTTP API."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BatoceraApi, BatoceraApiError
from .const import DEFAULT_PORT, DOMAIN


class BatoceraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up a Batocera machine."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                await BatoceraApi(
                    async_get_clientsession(self.hass), host, port
                ).capabilities()
            except BatoceraApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host.lower()}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Batocera ({host})", data={CONF_HOST: host, CONF_PORT: port}
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="batocera.local"): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                }
            ),
            errors=errors,
        )
