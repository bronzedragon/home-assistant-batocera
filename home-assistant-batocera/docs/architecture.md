# Architecture (draft)

## Components

- Home Assistant custom integration, installed in `custom_components/batocera/`.
- EmulationStation HTTP API on TCP 1234 for library discovery and gameplay actions (subject to version checks).
- Wake-on-LAN for boot requests; SSH for orderly shutdown and reboot.
- Optional MQTT event bridge for real-time state changes.

## Data model

- One HA device per Batocera host.
- A small set of device-level entities for connectivity, current game/system and counts.
- Game catalogue cached in memory, rather than one entity per game.
- Action to launch a game by a validated identifier/path after confirmation of endpoint semantics.

## Validation checklist

- [ ] Verify `/caps` and version-specific available endpoints.
- [ ] Verify `/systems` response schema.
- [ ] Verify per-system games response and pagination/size.
- [ ] Verify current game state and stop/launch semantics.
- [ ] Verify host machine power-management commands.
- [ ] Verify API authentication/network access expectations.
