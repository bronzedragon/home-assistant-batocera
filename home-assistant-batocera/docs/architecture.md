# Architecture (v0.1.0)

- `api.py`: read-only EmulationStation API client using Home Assistant's aiohttp session.
- `config_flow.py`: validates the local HTTP endpoint via `/caps`.
- `coordinator.py`: 30-second poll of capabilities, idle status and running game; refresh `/systems` every 20 polls.
- `sensor.py`: version, game/system counts, runtime state and current title/system.
- `binary_sensor.py`: HTTP API connectivity, including offline/unavailable transitions.

The game list endpoint has been validated on Batocera 42, but is not yet surfaced as a UI browser. No per-ROM entity proliferation, credentials or write controls in v0.1.0.

## Verified test environment

- Batocera 42o, HP EliteDesk 800 G3 SFF
- Host LAN IP `10.8.76.244`, TCP 1234
- `/caps` HTTP 200
- `/systems` console metadata and game counts
- `/systems/nes/games` game IDs, names and media paths
- `/runningGame` HTTP 201 with `NO GAME RUNNING` while idle
- `/isIdle` HTTP 200 with `[true]` while idle

## Future work

- On-demand game library browse and artwork
- Game launch/stop controls after API command testing
- Wake-on-LAN and authenticated SSH system controls
- Tests with a live Home Assistant installation
