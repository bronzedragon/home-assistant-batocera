# Home Assistant Batocera Linux

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=bronzedragon&repository=home-assistant-batocera&category=integration)

Custom Home Assistant integration for Batocera's EmulationStation HTTP API.

**v0.1.0 development preview (read-only)** — tested at the API level against Batocera 42.

## Features
- Configuration flow for a Batocera host and port (default TCP 1234)
- Version, system state, current game, current console
- Console and game counts with automatic collections excluded
- API connectivity binary sensor
- 30-second shared polling with cached system metadata

## Install from HACS or Home Assistant Marketplace

Add `https://github.com/bronzedragon/home-assistant-batocera` as a **custom integration repository** in HACS, or under **Settings → Marketplace** in Home Assistant 2026.11+. Download it, restart Home Assistant, and add **Batocera Linux** under Settings → Devices & services.

The integration is **not yet in the default catalog**. Default catalog submission requires passing HACS and Hassfest checks, published GitHub release, and catalog review.

## Install manually
Copy `custom_components/batocera` into Home Assistant's `/config/custom_components/`, restart Home Assistant, and add Batocera Linux.

On Batocera enable System Settings → Frontend Developer Options → Public Web Access. The HTTP API has no authentication: restrict TCP 1234 to your trusted LAN.

## Verified API responses
- `GET /caps` gives Version
- `GET /systems` gives console catalog/counts
- `GET /systems/nes/games` gives game metadata
- `GET /isIdle` gives a Boolean array, e.g. `[true]`
- `GET /runningGame` returns HTTP 201 and `{"msg":"NO GAME RUNNING"}` when idle

## Planned
On-demand console game browser; launch and stop controls; Wake-on-LAN; SSH power management.

No ROM files or copyrighted game assets are distributed by this project.
