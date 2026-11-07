# Home Assistant Batocera Linux

Custom Home Assistant integration for Batocera's EmulationStation HTTP API.

**Status: v0.1.0 development preview, read-only.** Verified against Batocera 42o (`2025/10/06`).

## Features

- UI configuration via host/IP and TCP port (default 1234)
- Batocera version, machine state, current game and console
- Console and game counts (collections and grouped systems excluded to avoid double-counting)
- Console names as attributes on the console count sensor
- Binary API connectivity sensor that stays visible when the host is offline
- Shared 30-second polling, with console catalogue refresh every 10 minutes

## Installation

Copy `custom_components/batocera` into your Home Assistant `/config/custom_components/` directory and restart Home Assistant. Go to **Settings → Devices & services → Add integration → Batocera Linux**. Enter the Batocera address (e.g. `10.8.76.244`) and port `1234`.

On Batocera, enable **System Settings → Frontend Developer Options → Public Web Access**. Restrict TCP 1234 to trusted LAN devices; the API has no authentication.

## Upcoming features

- On-demand per-system game catalog and artwork browser
- Game launch and stop controls (after endpoint validation)
- Wake-on-LAN and SSH shutdown/restart, with explicit credential setup
- MQTT game-state events and optional dashboard card

## API behavior verified

- `GET /caps` returns `Version`
- `GET /systems` returns system metadata and counts
- `GET /systems/nes/games` returns full metadata including artwork paths
- `GET /isIdle` returns `[true]` when idle
- `GET /runningGame` returns HTTP 201 with `{ "msg": "NO GAME RUNNING" }` when idle

No game assets or ROM files are included in this repository.
