"""Persistent Wake-on-LAN identity independent of API availability."""

from __future__ import annotations

import re

_MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


def valid_wol_mac(mac: object) -> bool:
    """Require a six-byte nonzero unicast MAC address."""
    if not isinstance(mac, str) or not _MAC_RE.fullmatch(mac):
        return False
    raw = bytes.fromhex(mac.replace(":", ""))
    return raw != bytes(6) and not (raw[0] & 1)


def effective_mac(entry) -> str | None:
    """Prefer explicit override, then discovery data, then MAC-based unique ID."""
    for candidate in (
        getattr(entry, "options", {}).get("mac"),
        entry.data.get("mac"),
        getattr(entry, "unique_id", None),
    ):
        if valid_wol_mac(candidate):
            return candidate.lower()
    return None


def effective_discovery_value(entry, key):
    """Expose manually preserved MAC alongside normal discovery metadata."""
    if key == "mac":
        return effective_mac(entry)
    return entry.data.get(key)
