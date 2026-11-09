"""Stable ASCII device names independent of Unicode mDNS display labels."""

from __future__ import annotations

import ipaddress
import re

from homeassistant.const import CONF_HOST

CONF_HOSTNAME = "hostname"
_HOST_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")


def normalized_hostname(value: str) -> str:
    """Return a safe ASCII name for device/entity naming.

    This is not the connection address; internationalized display names are
    deliberately kept separate from this machine hostname.
    """
    value = value.strip().rstrip(".")
    if value.lower().endswith(".local"):
        value = value[:-6]
    value = value.lower()
    if not _HOST_LABEL.fullmatch(value):
        raise ValueError("Hostname must be a single ASCII DNS label (letters, digits, hyphens)")
    return value


def fallback_hostname(host: str) -> str:
    """Derive a compatible name when upgrading older manual entries."""
    host = host.strip().rstrip(".")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        candidate = host.split(".", 1)[0]
    else:
        candidate = "batocera-" + host.replace(".", "-").replace(":", "-")
    candidate = re.sub(r"[^a-z0-9-]", "-", candidate.lower()).strip("-")
    candidate = re.sub("-+", "-", candidate)[:63].strip("-")
    if candidate and _HOST_LABEL.fullmatch(candidate):
        return candidate
    return "batocera"


def entity_device_name(entry) -> str:
    """Naming base, using configurable override before discovered hostname."""
    override = entry.options.get(CONF_HOSTNAME)
    if override:
        return normalized_hostname(override)
    stored = entry.data.get(CONF_HOSTNAME)
    if stored:
        try:
            return normalized_hostname(stored)
        except ValueError:
            pass
    return fallback_hostname(entry.data[CONF_HOST])
