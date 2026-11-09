"""Shared Batocera API polling."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BatoceraApi, BatoceraApiError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class BatoceraCoordinator(DataUpdateCoordinator[dict]):
    """Poll status and periodically refresh system metadata."""

    def __init__(self, hass, entry, api: BatoceraApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        self._systems: list[dict] = []
        self._polls = 0

    async def _async_update_data(self) -> dict:
        try:
            caps = await self.api.capabilities()
            if not self._systems or self._polls % 20 == 0:
                self._systems = await self.api.systems()
            game = await self.api.running_game()
            idle = await self.api.is_idle()
            self._polls += 1
            actual_systems = [
                s for s in self._systems
                if str(s.get("collection", "false")).lower() != "true"
                and str(s.get("groupsystem", "false")).lower() != "true"
                and str(s.get("gamesystem", "false")).lower() == "true"
            ]
            # Browsing must include grouped console entries, such as NES when
            # EmulationStation groups NES and Famicom Disk System together.
            # Keep the existing count filter separate to avoid count changes.
            browsable_systems = [
                s for s in self._systems
                if isinstance(s.get("name"), str) and s["name"]
                and str(s.get("collection", "false")).lower() != "true"
                and (int(s.get("totalGames", 0)) > 0
                     or int(s.get("visibleGames", 0)) > 0
                     or str(s.get("groupsystem", "false")).lower() == "true")
            ]
            return {
                "version": caps["Version"],
                "browsable_systems": browsable_systems,
                "systems": actual_systems,
                "system_count": len(actual_systems),
                "game_count": sum(int(s.get("totalGames", 0)) for s in actual_systems),
                "running_game": game,
                "idle": idle,
            }
        except (BatoceraApiError, TypeError, ValueError, KeyError) as err:
            raise UpdateFailed(str(err)) from err
