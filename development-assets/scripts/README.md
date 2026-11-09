# Supporting scripts

These are **Batocera-side development/deployment assets**, not part of the Home Assistant integration and not installed by HACS.

## Batocera Avahi discovery service

[`batocera_mdns`](batocera_mdns) publishes a DNS-SD service named `_batocera._tcp.local.` on port 1234. Its TXT fields are automatically determined at startup:

| Field | Source |
| --- | --- |
| `api`, `api_version` | Static protocol labels used by the HA integration |
| `mac` | Default IPv4 network interface's `/sys/class/net/…/address` |
| `model` | DMI product name, Device Tree model, or architecture |
| `arch` | `uname -m` |
| `interface` | Interface on the default IPv4 route |
| `wol` | `enabled`, `disabled`, `unsupported` or `unknown` |
| `wol_supported` | `true`, `false` or `unknown` |
| `wol_modes` | Supported wake modes reported by `ethtool` |

### Prerequisites

Batocera v38+ user services, running `avahi-daemon`, and `avahi-publish-service`. `ethtool` is optional; without it the WoL status remains `unknown`. In EmulationStation, enable **Public Web Access** for the HTTP API. Use only on a trusted network: the API and mDNS TXT metadata are unauthenticated.

### Install on Batocera

From an SSH session on Batocera:

```bash
mkdir -p /userdata/system/services
curl -fsSL https://raw.githubusercontent.com/bronzedragon/home-assistant-batocera/main/development-assets/scripts/batocera_mdns \
  -o /userdata/system/services/batocera_mdns
chmod +x /userdata/system/services/batocera_mdns

# Check prerequisites and run once to verify:
command -v avahi-publish-service
pidof avahi-daemon
command -v ethtool
bash -n /userdata/system/services/batocera_mdns
batocera-services list user
batocera-services enable batocera_mdns
batocera-services start batocera_mdns
/userdata/system/services/batocera_mdns status
cat /run/batocera_mdns.log
```

Batocera requires service filenames without a dot or `.sh` extension. If the new service does not appear in its UI, reboot the Batocera machine. For upgrades, replace the script and restart it:

```bash
batocera-services stop batocera_mdns
batocera-services start batocera_mdns
```

To verify discovery from another Linux system on the same mDNS network:

```bash
avahi-browse -rt _batocera._tcp
```

### Important WoL behavior

The script **detects but never enables** Wake-on-LAN. It inspects the interface used by the default IPv4 route, which may be Wi-Fi or an Ethernet adapter that is not capable of waking the machine. The actual ability to wake from shutdown also depends on firmware, power settings, and network topology. TXT records are refreshed when the service restarts; Home Assistant must retain the MAC before shutdown.

The service maintains `/run/batocera_mdns.pid` and `/run/batocera_mdns.log`; these are transient runtime files, not persistent configuration files.
