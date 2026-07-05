#!/bin/sh
set -eu

if [ "${MANAGE_ADB:-0}" = "1" ]; then
  unset ADB_SERVER_SOCKET
  adb kill-server >/dev/null 2>&1 || true
  adb start-server
fi

mkdir -p /workspace/base_apks /workspace/split_apks /workspace/plugin_libs /workspace/cosmog_zips

exec python3 /workspace/device_panel.py \
  --host "${PANEL_HOST:-0.0.0.0}" \
  --port "${PANEL_PORT:-8090}" \
  --workspace /workspace
