# Home Assistant Batocera

Custom Home Assistant integration for Batocera Linux (in development).

## Goals

- Discover and monitor Batocera hosts.
- Wake via Wake-on-LAN; gracefully shut down and reboot via authenticated SSH.
- Discover EmulationStation systems and games using the HTTP API.
- Expose console selection and game launch/stop controls.
- Optionally consume MQTT events for live game and console state.

## Status

**Planning / API validation.** This repository is a project scaffold, not a working Home Assistant integration yet.

## Architecture

- `custom_components/batocera/`: future Home Assistant integration
- `docs/`: API notes, architecture and milestones

## Security

Keep the EmulationStation HTTP service on a trusted local network. Avoid storing passwords or private keys in the repository. Prefer SSH key authentication.

## Next steps

1. Confirm Batocera version and API support (`/caps`, `/systems`, `/runningGame`).
2. Implement async API client and config flow.
3. Add data coordinator and power state entities.
4. Add systems and games browsing, launch/stop actions.
5. Add optional MQTT event support and HACS metadata.
