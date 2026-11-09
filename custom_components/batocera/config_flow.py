"""User and Zeroconf configuration for Batocera's EmulationStation API."""

from __future__ import annotations

import ipaddress
import re

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import BatoceraApi, BatoceraApiError
from .const import DEFAULT_PORT, DOMAIN
from .naming import CONF_HOSTNAME, fallback_hostname, normalized_hostname

CONF_MAC = "mac"
CONF_WOL = "wol"
CONF_WOL_SUPPORTED = "wol_supported"
CONF_WOL_MODES = "wol_modes"
CONF_MODEL = "model"
CONF_ARCH = "arch"
CONF_INTERFACE = "interface"
CONF_DISCOVERY_NAME = "discovery_name"

_MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


def discovery_metadata(properties: dict) -> dict:
    """Extract only recognized, bounded TXT fields; never trust TXT for access."""
    metadata = {}
    for field in (CONF_WOL, CONF_WOL_SUPPORTED, CONF_WOL_MODES,
                  CONF_MODEL, CONF_ARCH, CONF_INTERFACE):
        raw = properties.get(field)
        if isinstance(raw, str) and raw and len(raw) <= 200:
            metadata[field] = raw
    return metadata


def matching_host(a: str, b: str) -> bool:
    """Compare literal IPs and ordinary mDNS hostnames, without doing DNS."""
    return a.rstrip(".").lower() == b.rstrip(".").lower()


def advertised_display_name(service_name: str) -> str:
    """Return the instance label, excluding the DNS-SD service/type suffix."""
    suffix = "._batocera._tcp.local."
    if service_name.lower().endswith(suffix):
        name = service_name[:-len(suffix)]
    else:
        name = service_name.rstrip(".")
    return name.strip()[:128]


class BatoceraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up a Batocera machine manually or from Avahi."""

    VERSION = 1

    async def _check_api(self, host: str, port: int) -> bool:
        try:
            await BatoceraApi(
                async_get_clientsession(self.hass), host, port
            ).capabilities()
        except BatoceraApiError:
            return False
        return True

    async def async_step_user(self, user_input=None):
        """Manual setup stays available without mDNS or a MAC address."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                hostname = normalized_hostname(user_input.get(CONF_HOSTNAME) or fallback_hostname(host))
            except ValueError:
                errors[CONF_HOSTNAME] = "invalid_hostname"
            if errors:
                pass
            elif not host or not await self._check_api(host, port):
                errors["base"] = "cannot_connect"
            else:
                for entry in self._async_current_entries():
                    if (matching_host(entry.data[CONF_HOST], host)
                            and entry.data[CONF_PORT] == port):
                        return self.async_abort(reason="already_configured")
                await self.async_set_unique_id(f"{host.lower()}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Batocera ({host})",
                    data={CONF_HOST: host, CONF_PORT: port, CONF_HOSTNAME: hostname},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="batocera.local"): str,
                vol.Optional(CONF_HOSTNAME): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }),
            errors=errors,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ):
        """Discover via _batocera._tcp.local., then request confirmation."""
        properties = discovery_info.properties
        if properties.get("api") != "emulationstation":
            return self.async_abort(reason="not_batocera")

        raw_mac = properties.get(CONF_MAC, "")
        if not isinstance(raw_mac, str) or not _MAC_RE.fullmatch(raw_mac):
            return self.async_abort(reason="invalid_discovery")
        mac = format_mac(raw_mac)

        host = discovery_info.host
        port = discovery_info.port
        if not host or not (1 <= port <= 65535):
            return self.async_abort(reason="invalid_discovery")
        try:
            if ipaddress.ip_address(host).version == 6:
                return self.async_abort(reason="invalid_discovery")
        except ValueError:
            pass

        # Validate the advertised API before treating TXT metadata as device data.
        if not await self._check_api(host, port):
            return self.async_abort(reason="cannot_connect")

        display_name = advertised_display_name(discovery_info.name)
        if not display_name:
            return self.async_abort(reason="invalid_discovery")

        try:
            hostname = normalized_hostname(discovery_info.hostname)
        except ValueError:
            hostname = fallback_hostname(host)

        details = {
            CONF_HOSTNAME: hostname,
            CONF_DISCOVERY_NAME: display_name,
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_MAC: mac,
            **discovery_metadata(properties),
        }

        # Reconcile already configured devices before the unique-ID abort so
        # their display titles can follow the current advertised service name.
        # This also covers older manually configured host:port IDs.
        # This handles matching IPs or identical hostnames, but cannot establish
        # that a changed hostname and a new IP belong to the same older entry.
        for entry in self._async_current_entries():
            entry_host = entry.data.get(CONF_HOST, "")
            advertised_hostname = discovery_info.hostname.rstrip(".")
            if (entry.data.get(CONF_MAC) == mac
                    or (entry.data.get(CONF_PORT) == port
                        and (matching_host(entry_host, host)
                             or matching_host(entry_host, advertised_hostname)))):
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, **details}, title=display_name
                )
                return self.async_abort(reason="already_configured")

        # A newly discovered entry uses its stable MAC as the unique ID.
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured(updates=details)

        self._discovered_data = details
        self._discovered_title = display_name
        return await self.async_step_discovery_confirm()

    @staticmethod
    def async_get_options_flow(config_entry):
        """Allow users to override the entity naming hostname."""
        return BatoceraOptionsFlow(config_entry)

    async def async_step_discovery_confirm(self, user_input=None):
        """Require a user confirmation; discovery never auto-creates entries."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_title,
                data=self._discovered_data,
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={
                "host": self._discovered_data[CONF_HOST],
                "port": str(self._discovered_data[CONF_PORT]),
                "model": self._discovered_data.get(CONF_MODEL, "Batocera"),
                "wol": self._discovered_data.get(CONF_WOL, "unknown"),
            },
        )


class BatoceraOptionsFlow(config_entries.OptionsFlow):
    """Edit the ASCII hostname without changing the Unicode integration title."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                hostname = normalized_hostname(user_input[CONF_HOSTNAME])
            except ValueError:
                errors[CONF_HOSTNAME] = "invalid_hostname"
            else:
                return self.async_create_entry(
                    title="",
                    data={**self._config_entry.options, CONF_HOSTNAME: hostname},
                )
        default = (
            self._config_entry.options.get(CONF_HOSTNAME)
            or self._config_entry.data.get(CONF_HOSTNAME)
            or fallback_hostname(self._config_entry.data[CONF_HOST])
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required(CONF_HOSTNAME, default=default): str}),
            errors=errors,
        )
