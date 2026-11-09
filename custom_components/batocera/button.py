"""Wake Batocera using a LAN magic packet, without the EmulationStation API."""

from __future__ import annotations

import re
import socket

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .naming import entity_device_name

_MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")
_BROADCAST_ADDRESS = "255.255.255.255"
_BROADCAST_PORT = 9


def valid_wol_mac(mac: object) -> bool:
    """Require a real, unicast six-byte MAC address."""
    if not isinstance(mac, str) or not _MAC_RE.fullmatch(mac):
        return False
    raw = bytes.fromhex(mac.replace(":", ""))
    return raw != b"\x00" * 6 and not (raw[0] & 1)


def send_magic_packet(mac: str) -> None:
    """Send a UDP broadcast WoL packet from the executor."""
    if not valid_wol_mac(mac):
        raise ValueError("A valid unicast MAC address is required")
    raw = bytes.fromhex(mac.replace(":", ""))
    packet = b"\xff" * 6 + raw * 16
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, (_BROADCAST_ADDRESS, _BROADCAST_PORT))


async def async_setup_entry(hass, entry, async_add_entities):
    """Create a wake button for each Batocera config entry."""
    async_add_entities([BatoceraWakeButton(hass, entry)])


class BatoceraWakeButton(ButtonEntity):
    """Stateless wake button; pressing does not guarantee the host woke."""

    _attr_has_entity_name = True
    _attr_name = "Wake Batocera"
    _attr_icon = "mdi:power"

    def __init__(self, hass, entry):
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_wake"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entity_device_name(entry),
            manufacturer="Batocera",
            model="EmulationStation",
        )

    @property
    def available(self) -> bool:
        """Require valid stored MAC; explicit lack of WoL support disables."""
        return (
            valid_wol_mac(self._entry.data.get("mac"))
            and self._entry.data.get("wol_supported") != "false"
        )

    async def async_press(self) -> None:
        """Broadcast without depending on the target's API being online."""
        if not self.available:
            raise HomeAssistantError(
                "Wake-on-LAN requires a discovered MAC and supported network adapter"
            )
        try:
            await self._hass.async_add_executor_job(
                send_magic_packet, self._entry.data["mac"]
            )
        except OSError as err:
            raise HomeAssistantError(
                f"Could not broadcast Batocera Wake-on-LAN packet: {err}"
            ) from err
