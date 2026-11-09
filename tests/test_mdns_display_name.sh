#!/usr/bin/env bash
# Verify Unicode, punctuation, CRLF and fallback without Avahi.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$root/development-assets/scripts/batocera_mdns" "$tmp/batocera_mdns"

[[ "$(bash "$tmp/batocera_mdns" display-name)" == "$(hostname)" ]]

printf '%s\n' "銀龍's Emulation Box" > "$tmp/DISPLAY_NAME"
[[ "$(bash "$tmp/batocera_mdns" display-name)" == "銀龍's Emulation Box" ]]

: > "$tmp/DISPLAY_NAME"
[[ "$(bash "$tmp/batocera_mdns" display-name)" == "$(hostname)" ]]

printf '%s\r\n' "銀龍's Emulation Box" > "$tmp/DISPLAY_NAME"
[[ "$(bash "$tmp/batocera_mdns" display-name)" == "銀龍's Emulation Box" ]]

echo "Display-name tests passed"
