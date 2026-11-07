"""Regression tests for Batocera 42/43 API response conventions."""

import importlib.util
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "batocera" / "api.py"
spec = importlib.util.spec_from_file_location("batocera_test_api", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
BatoceraApi = module.BatoceraApi
BatoceraApiError = module.BatoceraApiError


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self, **kwargs):
        return self.payload


class FakeSession:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    def get(self, *args, **kwargs):
        return FakeResponse(self.status, self.payload)


class TestApiStatus(IsolatedAsyncioTestCase):
    async def test_idle_true_http_200(self):
        self.assertTrue(await BatoceraApi(FakeSession(200, [True]), "localhost").is_idle())

    async def test_idle_false_http_201(self):
        self.assertFalse(await BatoceraApi(FakeSession(201, [False]), "localhost").is_idle())

    async def test_running_game_http_200(self):
        result = {"name": "Super Mario Bros. 3", "systemName": "nes"}
        self.assertEqual(
            await BatoceraApi(FakeSession(200, result), "localhost").running_game(),
            result,
        )

    async def test_no_running_game_http_201(self):
        self.assertIsNone(
            await BatoceraApi(
                FakeSession(201, {"msg": "NO GAME RUNNING"}), "localhost"
            ).running_game()
        )

    async def test_other_http_201_is_not_accepted(self):
        with self.assertRaises(BatoceraApiError):
            await BatoceraApi(FakeSession(201, {}), "localhost").capabilities()

    async def test_invalid_idle_payload_rejected(self):
        with self.assertRaises(BatoceraApiError):
            await BatoceraApi(FakeSession(201, {"idle": False}), "localhost").is_idle()
