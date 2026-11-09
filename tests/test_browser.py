"""Test console and game browsing without a Home Assistant runtime."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock

homeassistant = types.ModuleType("homeassistant")
exceptions = types.ModuleType("homeassistant.exceptions")
exceptions.HomeAssistantError = type("HomeAssistantError", (Exception,), {})
sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.exceptions", exceptions)

# Import browser as a package module so its relative .api import resolves.
# A stub is adequate here: the actual API has separate network tests.
package = types.ModuleType("batocera_browser_tests")
package.__path__ = []
sys.modules[package.__name__] = package
api = types.ModuleType("batocera_browser_tests.api")
api.BatoceraApiError = type("BatoceraApiError", (Exception,), {})
sys.modules[api.__name__] = api

source = (
    Path(__file__).resolve().parents[1]
    / "custom_components" / "batocera" / "browser.py"
)
spec = importlib.util.spec_from_file_location(
    "batocera_browser_tests.browser", source
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Coordinator:
    def __init__(self):
        self.data = {
            "systems": [
                {"name": "nes", "fullname": "Nintendo Entertainment System"},
                {"name": "snes", "fullname": "Super Nintendo Entertainment System"},
            ]
        }
        # Simulate a grouping scenario where the count-only catalog omits
        # NES, but raw browsing data still exposes the NES group.
        self.data["browsable_systems"] = [
            {"name": "fds", "fullname": "Family Computer Disk System",
             "groupsystem": "false", "totalGames": 8},
            {"name": "nes", "fullname": "Nintendo Entertainment System",
             "groupsystem": "true", "totalGames": 100},
            {"name": "snes", "fullname": "Super Nintendo Entertainment System"},
        ]
        self.api = types.SimpleNamespace(
            games=AsyncMock(return_value=[
                {"id": "id1", "name": "Super Mario Bros. 3", "genre": "Platform"},
                {"id": "id2", "name": "Super Mario Bros. 3", "genre": "Platform"},
                {"id": "id3", "name": "Nightshade"},
            ])
        )
        self.updates = 0

    def async_update_listeners(self):
        self.updates += 1


class BrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.coordinator = Coordinator()
        self.browser = module.BatoceraBrowser(self.coordinator)

    async def test_grouped_nes_available_as_console_option(self):
        self.assertIn("Family Computer Disk System (fds)", self.browser.console_options)
        self.assertIn("Nintendo Entertainment System (nes)", self.browser.console_options)
        await self.browser.choose_console("Nintendo Entertainment System (nes)")
        self.coordinator.api.games.assert_awaited_once_with("nes")
        self.assertIn("Super Mario Bros. 3", self.browser.game_options)

    async def test_loads_games_only_after_select(self):
        self.assertEqual(self.browser.game_options, [])
        await self.browser.choose_console(
            "Nintendo Entertainment System (nes)"
        )
        self.coordinator.api.games.assert_awaited_once_with("nes")
        self.assertEqual(len(self.browser.game_options), 3)
        self.assertEqual(self.browser.system_id, "nes")

    async def test_game_titles_sorted_alphabetically_case_insensitive(self):
        self.coordinator.api.games.return_value = [
            {"id": "z", "name": "zelda"},
            {"id": "b", "name": "Banjo"},
            {"id": "a", "name": "animal crossing"},
            {"id": "m", "name": "Mario"},
        ]
        await self.browser.choose_console("Nintendo Entertainment System (nes)")
        self.assertEqual(
            self.browser.game_options,
            ["animal crossing", "Banjo", "Mario", "zelda"],
        )
        self.browser.choose_game("Mario")
        self.assertEqual(self.browser.selected_game["id"], "m")

    async def test_duplicate_titles_are_selectable(self):
        await self.browser.choose_console("Nintendo Entertainment System (nes)")
        self.assertEqual(len(set(self.browser.game_options)), 3)
        other = next(x for x in self.browser.game_options if "[id2]" in x)
        self.browser.choose_game(other)
        self.assertEqual(self.browser.selected_game["id"], "id2")

    async def test_switching_console_clears_selected_game(self):
        await self.browser.choose_console("Nintendo Entertainment System (nes)")
        self.browser.choose_game("Nightshade")
        await self.browser.choose_console("Super Nintendo Entertainment System (snes)")
        self.assertIsNone(self.browser.selected_game)

    async def test_invalid_console_is_rejected(self):
        with self.assertRaises(exceptions.HomeAssistantError):
            await self.browser.choose_console("invalid console")

    async def test_failed_fetch_preserves_old_selection(self):
        await self.browser.choose_console("Nintendo Entertainment System (nes)")
        self.browser.choose_game("Nightshade")
        self.coordinator.api.games.side_effect = api.BatoceraApiError("offline")
        with self.assertRaises(exceptions.HomeAssistantError):
            await self.browser.choose_console(
                "Super Nintendo Entertainment System (snes)"
            )
        self.assertEqual(self.browser.system_id, "nes")
        self.assertEqual(self.browser.selected_game["name"], "Nightshade")


if __name__ == "__main__":
    unittest.main()
