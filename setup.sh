#!/usr/bin/env bash
set -euo pipefail

echo "=== Cosmog Device Panel Setup ==="
echo ""

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKSPACE"

# Detect WSL
IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null || [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
  IS_WSL=1
  echo "WSL detected."
fi

# Create managed folders
echo "Creating managed folders..."
mkdir -p base_apks split_apks plugin_libs cosmog_zips cosmog_updates downloads device_configs

# Copy example files if real ones don't exist
if [ ! -f known_devices.json ]; then
  cp known_devices.example.json known_devices.json
  echo "Created known_devices.json from example"
fi

echo ""
echo "1. Place your asset files in the managed folders:"
echo "   - Base APK in:      $WORKSPACE/base_apks/"
echo "   - Split APK in:     $WORKSPACE/split_apks/"
echo "   - Plugin .so in:    $WORKSPACE/plugin_libs/"
echo "   - Cosmog ZIP in:    $WORKSPACE/cosmog_zips/"
echo ""

# --- Start the panel ---
STARTED=0

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  if [ "$IS_WSL" -eq 1 ]; then
    COMPOSE_FILE="docker-compose.wsl.yml"
    echo "Docker Desktop on WSL — will use port mapping mode."
  else
    COMPOSE_FILE="docker-compose.yml"
  fi
  echo "Starting with Docker..."
  docker compose -f "$COMPOSE_FILE" up --build -d
  STARTED=1
  if [ "$IS_WSL" -eq 1 ]; then
    echo ""
    echo "Panel running at: http://127.0.0.1:8090"
  else
    echo ""
    echo "Panel running at:"
    echo "   - Host ADB:  http://127.0.0.1:8090"
    echo "   - Own ADB:   http://127.0.0.1:8091"
  fi
  echo ""
  echo "To stop:  docker compose -f $COMPOSE_FILE down"
  echo "To view:  docker compose -f $COMPOSE_FILE logs -f"
fi

if [ "$STARTED" -eq 0 ]; then
  echo "Starting panel directly..."
  if [ "$IS_WSL" -eq 1 ]; then
    echo "Make sure Windows ADB is running (adb -a nodaemon server in PowerShell)."
    export ADB_SERVER_SOCKET=tcp:127.0.0.1:5037
  fi
  nohup python3 "$WORKSPACE/device_panel.py" > /dev/null 2>&1 &
  echo ""
  echo "Panel running at: http://127.0.0.1:8080"
  echo "PID: $!"
  echo ""
  echo "To stop:  kill $!"
fi

echo ""
