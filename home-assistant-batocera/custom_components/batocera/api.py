"""Local EmulationStation HTTP API client for Batocera Linux."""

from __future__ import annotations

from urllib.parse import quote

from aiohttp import ClientError, ClientSession, ClientTimeout


class BatoceraApiError(Exception):
    """An EmulationStation API request failed."""


class BatoceraApi:
    """Small, read-only client. No authentication is provided by Batocera's API."""

    def __init__(self, session: ClientSession, host: str, port: int = 1234) -> None:
        self._session = session
        self.base_url = f"http://{host}:{port}"

    async def _get(self, path: str, *, allow_no_game: bool = False):
        try:
            async with self._session.get(
                f"{self.base_url}{path}", timeout=ClientTimeout(total=10)
            ) as response:
                if response.status == 201 and allow_no_game:
                    body = await response.json(content_type=None)
                    if isinstance(body, dict) and body.get("msg") == "NO GAME RUNNING":
                        return None
                if response.status != 200:
                    raise BatoceraApiError(f"{path}: HTTP {response.status}")
                return await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise BatoceraApiError(f"Cannot retrieve {path}: {err}") from err

    async def capabilities(self) -> dict:
        result = await self._get("/caps")
        if not isinstance(result, dict) or "Version" not in result:
            raise BatoceraApiError("Unexpected /caps response")
        return result

    async def systems(self) -> list[dict]:
        result = await self._get("/systems")
        if not isinstance(result, list):
            raise BatoceraApiError("Unexpected /systems response")
        return result

    async def running_game(self) -> dict | None:
        result = await self._get("/runningGame", allow_no_game=True)
        if result is not None and not isinstance(result, dict):
            raise BatoceraApiError("Unexpected /runningGame response")
        return result

    async def is_idle(self) -> bool:
        result = await self._get("/isIdle")
        if not isinstance(result, list) or not result or not isinstance(result[0], bool):
            raise BatoceraApiError("Unexpected /isIdle response")
        return result[0]

    async def games(self, system: str) -> list[dict]:
        """Fetch a single selected system; never bulk-load the entire ROM library."""
        if not system or "/" in system or system in (".", ".."):
            raise BatoceraApiError("Invalid system identifier")
        result = await self._get(f"/systems/{quote(system, safe='')}/games")
        if not isinstance(result, list):
            raise BatoceraApiError("Unexpected game list response")
        return result
