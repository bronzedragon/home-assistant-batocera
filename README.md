# Home Assistant Batocera Linux

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=bronzedragon&repository=home-assistant-batocera&category=integration)

Custom Home Assistant integration for Batocera's EmulationStation HTTP API.

**v0.3.0 development preview (read-only)** — active-game monitoring verified with Batocera 43.1; browse feature still needs live Home Assistant testing.

### v0.1.1 compatibility fix
Batocera 43 can return HTTP 201 with `[false]` from `/isIdle` while a game is active. Earlier versions of this integration treated that response as an API error and marked all entities unavailable. The client now accepts both 200 and 201 for `/isIdle`, while separately handling the `NO GAME RUNNING` response from `/runningGame`.

## Release history
- **v0.2.0:** On-demand console and game browser.
- **v0.2.1:** Repository cleanup and icon placement. This published tag contains manifest version 0.2.0, an existing versioning discrepancy; do not rewrite the published tag.
- **v0.2.2:** Release metadata and branding maintenance.
- **v0.3.0 (development):** Zeroconf/Avahi discovery and MAC/WoL metadata capture.

## Features
- Discover Avahi-advertised Batocera machines via `_batocera._tcp.local.` and confirm setup in Home Assistant
- Retain discovered MAC, hardware model, architecture, interface and WoL capability in configuration data
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

## Automatic discovery (v0.3.0)

Run the Batocera Avahi publisher script advertising `_batocera._tcp` on TCP 1234 with `api=emulationstation`, an actual NIC `mac`, and the dynamic `wol`, `wol_supported`, `wol_modes`, `model`, `arch`, and `interface` TXT records. Home Assistant needs Zeroconf enabled and mDNS visibility between it and Batocera. The integration verifies `/caps` before showing a **Discovered** configuration prompt; the user must confirm to add a new device. The Home Assistant entry title uses the actual Avahi DNS-SD instance display name (for example, `Batocera on ginryuus-Emulation-Box`), not the `.local` hostname. On rediscovery, recognized existing entries have their titles synchronized to this display name. Entries configured with the same IP or matching mDNS hostname are reconciled without creating a second entry. For existing manual configurations whose IP and hostname have both changed, identity matching may require manual intervention.

Discovered MAC and WoL fields are stored for future power controls; this release does **not** send wake packets or change NIC settings. The script reports the default IPv4 route's interface, which is not necessarily WoL-capable; only advertise a WoL-capable NIC if it is the intended wake target. TXT data is unauthenticated and valid only on a trusted LAN.

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

## Development resources

Non-installable project scripts and artwork are organized in [`development-assets/`](development-assets/), with separate [`scripts/`](development-assets/scripts/) and [`images/`](development-assets/images/) directories. These are not deployed by HACS; integration branding remains in `custom_components/batocera/brand/`.


## Display name versus entity hostname

The mDNS **service instance display name** (including Unicode, for example `銀龍`) is used for the Home Assistant **integration title**. The separate **hostname** setting is a single ASCII DNS label and is used as the Home Assistant device name / suggested entity naming prefix. Zeroconf discovery fills it from the SRV hostname (for example `ginryuu.local.` becomes `ginryuu`), never from the translated or Unicode service display label. For manual setup, the optional hostname field defaults to a safe name derived from the connection host.

To change it after setup, open **Settings → Devices & services → Batocera → Configure (Options)** and edit **Entity hostname**; an integration reload applies the new device name. Existing entity registry IDs and user-renamed devices/entities are retained by Home Assistant and may need manual renaming; this deliberately avoids breaking dashboards and automations. The connection address, mDNS display title, and stable integration/entity unique IDs do not change when the hostname option changes.

## Planned
Artwork proxy and graphical library card; launch and stop controls; Wake-on-LAN; SSH power management.

No ROM files or copyrighted game assets are distributed by this project.

## Integration icon

Home Assistant 2026.3+ loads custom integration branding from `custom_components/batocera/brand/`. The icon package provides `icon.png` (256 × 256) and `icon@2x.png` (512 × 512). These image assets are included under the canonical integration path. A missing Marketplace/HACS listing icon does not necessarily mean Home Assistant's installed integration icon is missing.
