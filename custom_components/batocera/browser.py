"""On-demand Batocera console and game browsing."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError

from .api import BatoceraApiError


class BatoceraBrowser:
    """Maintain one selected system and its game catalog per config entry."""

    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator
        self.system_id: str | None = None
        self.game_id: str | None = None
        self.games: dict[str, dict] = {}
        self.game_labels: dict[str, str] = {}

    @property
    def systems(self) -> list[dict]:
        return self.coordinator.data.get("browsable_systems", self.coordinator.data.get("systems", [])) if self.coordinator.data else []

    @property
    def console_options(self) -> list[str]:
        """Full name plus stable identifier avoids duplicate display names."""
        return [
            f'{system.get("fullname") or system["name"]} ({system["name"]})'
            for system in self.systems
        ]

    @property
    def current_console_option(self) -> str | None:
        for system in self.systems:
            if system["name"] == self.system_id:
                return f'{system.get("fullname") or system["name"]} ({system["name"]})'
        return None

    @property
    def game_options(self) -> list[str]:
        return sorted(self.game_labels, key=lambda label: (label.casefold(), label))

    @property
    def current_game_option(self) -> str | None:
        for label, game_id in self.game_labels.items():
            if game_id == self.game_id:
                return label
        return None

    @property
    def selected_game(self) -> dict | None:
        return self.games.get(self.game_id) if self.game_id else None

    async def choose_console(self, option: str) -> None:
        matching = [
            system for system in self.systems
            if option == f'{system.get("fullname") or system["name"]} ({system["name"]})'
        ]
        if len(matching) != 1:
            raise HomeAssistantError("Unknown Batocera console")

        target = matching[0]["name"]
        if target == self.system_id:
            return

        try:
            payload = await self.coordinator.api.games(target)
        except BatoceraApiError as err:
            raise HomeAssistantError(f"Cannot retrieve {target} games: {err}") from err

        games: dict[str, dict] = {}
        labels: dict[str, str] = {}
        for game in payload:
            identifier = game.get("id")
            if not isinstance(identifier, str) or not identifier or identifier in games:
                continue
            games[identifier] = game
            title = str(game.get("name") or "Untitled")
            title = title[:210]
            label = title
            if label in labels:
                label = f"{title} [{identifier[:8]}]"
            if label in labels:
                label = f"{title} [{identifier}]"
            labels[label] = identifier

        self.system_id = target
        self.games = games
        self.game_labels = labels
        self.game_id = None
        self.coordinator.async_update_listeners()

    def choose_game(self, option: str) -> None:
        if option not in self.game_labels:
            raise HomeAssistantError("Unknown Batocera game")
        self.game_id = self.game_labels[option]
        self.coordinator.async_update_listeners()
