# Device Panel

`device_panel.py` is a local web UI for the ADB workflow in `/home/chaitu/joltik-master/commands`.

It supports:

- remote `adb connect`
- keeping saved network devices visible after restart
- simple device overview: name, IP/ID, status, PoGo version, memory
- one-click actions per connected device:
  - update PoGo from the newest files in the managed asset folders
  - update Cosmog from the newest ZIP in the managed Cosmog folder
  - restart Cosmog
  - reboot the device

## Run

```bash
python3 /home/chaitu/cosmog/device_panel.py
```

Open:

```text
http://127.0.0.1:8080
```

## Docker

You can run the panel in Docker, but it still needs access to an ADB server.

Recommended approach:

1. Run the host ADB server normally.
2. On Linux, run the container with host networking so it can reach the host ADB server on `127.0.0.1:5037`.

Using Docker Compose from `/home/chaitu/cosmog`:

```bash
docker compose up --build
```

This now starts both containers:

- `cosmog-panel`: host-managed ADB on `http://127.0.0.1:8090`
- `cosmog-panel-adb`: container-managed ADB on `http://127.0.0.1:8091`

Then open either:

```text
http://127.0.0.1:8090
http://127.0.0.1:8091
```

Notes:

- `cosmog-panel` uses `ADB_SERVER_SOCKET=tcp:127.0.0.1:5037`
- `cosmog-panel-adb` starts its own local ADB daemon and listens on a separate panel port
- The compose file uses `network_mode: host` for Linux
- `/home/chaitu/cosmog` is mounted as `/workspace`
- `/home/chaitu/joltik-master` is mounted read-only for the existing asset paths
- The host must already have an ADB server running for `cosmog-panel`
- The container now runs `/workspace/device_panel.py`, so Python code changes can be picked up with `docker compose restart` instead of a full rebuild

### Container-managed ADB

If you want the container itself to run the ADB server and talk to USB devices directly, use `cosmog-panel-adb` at `http://127.0.0.1:8091`.

That service:

- starts `adb` inside the container
- unsets `ADB_SERVER_SOCKET` before starting the daemon so `adb start-server` creates a local server inside the container
- uses `network_mode: host`
- mounts `/dev/bus/usb`
- runs the container as `privileged`

Tradeoffs:

- more permissions
- more fragile than host-managed ADB
- USB reconnect behavior depends on Docker and the host

For remote `adb connect` over TCP, this mode can still work, but local USB passthrough is the main reason to use it.

## Managed folders

On startup the panel creates these folders under the workspace:

- `/home/chaitu/cosmog/base_apks/`
- `/home/chaitu/cosmog/split_apks/`
- `/home/chaitu/cosmog/plugin_libs/`
- `/home/chaitu/cosmog/cosmog_zips/`

Put your latest files there:

- newest `.apk` in `base_apks/` is used as the base APK
- newest `.apk` in `split_apks/` is used as the split APK
- newest `.so` in `plugin_libs/` is used as the plugin library
- newest `.zip` in `cosmog_zips/` is used for Cosmog update

Cosmog ZIP extractions are still unpacked under `/home/chaitu/cosmog/cosmog_updates/`.

## Notes

- The install and config-write actions use `su -c` on the device.
- Pulled configs are cached under `/home/chaitu/cosmog/device_configs/`.
- The panel binds to `127.0.0.1:8080` by default.
