# Home Assistant Batocera Linux

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=bronzedragon&repository=home-assistant-batocera&category=integration)

Custom Home Assistant integration for Batocera's EmulationStation HTTP API.

**v0.2.2 development preview (read-only)** — active-game monitoring verified with Batocera 43.1; browse feature still needs live Home Assistant testing.

### v0.1.1 compatibility fix
Batocera 43 can return HTTP 201 with `[false]` from `/isIdle` while a game is active. Earlier versions of this integration treated that response as an API error and marked all entities unavailable. The client now accepts both 200 and 201 for `/isIdle`, while separately handling the `NO GAME RUNNING` response from `/runningGame`.

## Release history
- **v0.2.0:** On-demand console and game browser.
- **v0.2.1:** Repository cleanup and icon placement. This published tag contains manifest version 0.2.0, an existing versioning discrepancy; do not rewrite the published tag.
- **v0.2.2 (planned):** Align manifest, docs, and release version while retaining the corrected brand assets.

## Features
- Console selection and on-demand game lists through Home Assistant select entities
- Game selection and a metadata sensor with description, release date, genre, developer, rating, favorites, play history, and media URLs
- Configuration flow for a Batocera host and port (default TCP 1234)
- Version, system state, current game, current console
- Console and game counts with automatic collections excluded
- API connectivity binary sensor
- 30-second shared polling with cached system metadata

## Install from HACS or Home Assistant Marketplace

Add `https://github.com/bronzedragon/home-assistant-batocera` as a **custom integration repository** in HACS, or under **Settings → Marketplace** in Home Assistant 2026.11+. Download it, restart Home Assistant, and add **Batocera Linux** under Settings → Devices & services.

The integration is **not yet in the default catalog**. HACS and Hassfest checks are passing, but default catalog inclusion still requires submission and review.

## Install manually
Copy `custom_components/batocera` into Home Assistant's `/config/custom_components/`, restart Home Assistant, and add Batocera Linux.

On Batocera enable System Settings → Frontend Developer Options → Public Web Access. The HTTP API has no authentication: restrict TCP 1234 to your trusted LAN.

## Verified API responses
- `GET /caps` gives Version
- `GET /systems` gives console catalog/counts
- `GET /systems/nes/games` gives game metadata
- `GET /isIdle` gives a Boolean array, e.g. `[true]`
- `GET /runningGame` returns HTTP 201 and `{"msg":"NO GAME RUNNING"}` when idle

## Browse games in Home Assistant
After installing and restarting Home Assistant, open the Batocera device and set **Browse Console**, then **Browse Game**. The **Selected Game** sensor exposes metadata in its attributes and the **Selected Console Game Count** sensor reports the number loaded. Selecting a game does not launch it.

EmulationStation may expose thousands of games for a console; this integration retrieves only the chosen console. Game lists are held in memory and cleared on integration reload. Art URLs are exposed as metadata but not yet proxied through Home Assistant for artwork display.

## Planned
Artwork proxy and graphical library card; launch and stop controls; Wake-on-LAN; SSH power management.

No ROM files or copyrighted game assets are distributed by this project.

## Integration icon

Home Assistant 2026.3+ loads custom integration branding from `custom_components/batocera/brand/`. The icon package provides `icon.png` (256 × 256) and `icon@2x.png` (512 × 512). These image assets are included under the canonical integration path. A missing Marketplace/HACS listing icon does not necessarily mean Home Assistant's installed integration icon is missing.
