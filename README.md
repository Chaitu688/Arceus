# Cosmog Device Panel

A local web UI for managing Android devices running Pokémon Go with Cosmog. Connect devices over ADB (USB or TCP), update PoGo APKs, deploy Cosmog launcher updates, pull/push configs, tail logs, and reboot — all from a browser.

## Prerequisites

- **Python 3.12+** (no pip packages needed — stdlib only)
- **ADB** installed and on your PATH (`adb version` should work)
- Rooted Android devices with ADB debugging enabled

## Quick Start

```bash
git clone https://github.com/Chaitu688/Arceus.git cosmog-panel
cd cosmog-panel
./setup.sh
```

That's it — the panel starts automatically. Open the URL printed by setup.sh.

### Updating Pokémon Go

The panel downloads PoGo APKs and plugins directly from the mirror — **no manual file copying needed**:

1. Connect a device via ADB (TCP or USB)
2. Click **"Update PoGo"** on the device row
3. Pick a version from the version picker
4. The panel downloads the APKs + plugin, pushes them, and restarts Cosmog

### Updating Cosmog (optional)

Drop a Cosmog launcher ZIP in `cosmog_zips/` and click **"Update Cosmog"** on a connected device. The ZIP should contain:
- `com.nianticlabs.pokemongo` (launcher executable)
- `lib/libart.so` (and any other libraries)
- `config.toml` (optional — Cosmog config)

## Managed Folders

| Folder | Purpose |
|---|---|
| `cosmog_zips/` | Cosmog launcher ZIPs (newest `.zip` used by "Update Cosmog") |
| `base_apks/` | Auto-populated by "Update PoGo" from mirror |
| `split_apks/` | Auto-populated by "Update PoGo" from mirror |
| `plugin_libs/` | Auto-populated by "Update PoGo" from mirror |

## Configuration

### CLI flags

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | HTTP bind address. Use `0.0.0.0` to expose on LAN |
| `--port` | `8080` | HTTP port |
| `--workspace` | `.` | Workspace directory for managed folders and caches |
| `--remote-dir` | `/data/adb/cosmog2` | Cosmog install path on devices |
| `--base-apk` | (auto) | Override base APK path |
| `--split-apk` | (auto) | Override split APK path |
| `--plugin-so` | (auto) | Override plugin library path |

### Device config

Edit `known_devices.json` to persist network devices across restarts. Format:

```json
[
  {
    "host": "192.168.0.100",
    "port": "5555",
    "serial": "192.168.0.100:5555"
  }
]
```

### Cosmog config

The panel can pull/push `config.toml` from devices (Cosmog's config file). See `config.toml.example` for the expected format.

## Docker

```bash
docker compose up --build
```

This starts two containers:

| Container | Port | ADB |
|---|---|---|
| `cosmog-device-panel` | `8090` | Uses host ADB server via `ADB_SERVER_SOCKET` |
| `cosmog-device-panel-adb` | `8091` | Runs its own ADB daemon (USB passthrough) |

The `cosmog-panel-adb` container requires `--privileged` and `/dev/bus/usb` mounted for local USB devices.

> **Note:** `network_mode: host` is used for Linux. On Docker Desktop (Windows/macOS), host networking may not work — edit the compose file to use port mapping instead.

## WSL Setup

Running on Windows Subsystem for Linux? Here's how to handle ADB:

### Option A: Use Windows ADB from WSL (recommended)

1. Install ADB on Windows (e.g., via `winget install Google.PlatformTools`)
2. In WSL, set the ADB server socket to reach the Windows daemon:
   ```bash
   export ADB_SERVER_SOCKET=tcp:127.0.0.1:5037
   ```
3. The panel will now use the Windows ADB server — USB devices connected to Windows just work.

### Option B: Install ADB inside WSL

```bash
sudo apt install adb
```

This works for TCP-connected devices (`adb connect <ip>:5555`). USB devices connected directly to Windows won't be visible to WSL's ADB without USB passthrough (`usbipd`).

### Docker on WSL2

Docker Desktop integrates with WSL2. Use port mapping instead of `network_mode: host`:

```yaml
ports:
  - "8090:8090"
```

And for ADB access from the container, set `ADB_SERVER_SOCKET=tcp:host.docker.internal:5037` to reach the Windows ADB daemon.

## API

The panel exposes a JSON REST API alongside the web UI:

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | ADB version + device list |
| `/api/versions` | GET | Available PoGo versions from mirror |
| `/api/defaults` | GET | Current paths and settings |
| `/api/connect` | POST | Connect to `host:port` |
| `/api/connect_saved` | POST | Reconnect a saved device |
| `/api/update_pogo_version` | POST | Download + install a PoGo version |
| `/api/start_cosmog` | POST | Start Cosmog on device |
| `/api/stop_cosmog` | POST | Stop Cosmog on device |
| `/api/restart_cosmog` | POST | Restart Cosmog on device |
| `/api/cosmog_log` | POST | Tail last 200 lines of Cosmog log |
| `/api/pull_config` | POST | Pull `config.toml` from device |
| `/api/push_config` | POST | Push `config.toml` to device |
| `/api/reboot_device` | POST | Reboot device |

## Security

The panel has **no built-in authentication**. If you bind to `0.0.0.0` or expose it via a public domain, anyone who can reach the URL has full control over your devices (install APKs, run root commands, reboot). At minimum:

- Keep `--host 127.0.0.1` and use an SSH tunnel for remote access
- Or put it behind nginx/Caddy with HTTPS + basic auth
- Or use Cloudflare Tunnel with Cloudflare Access for identity-aware proxy
