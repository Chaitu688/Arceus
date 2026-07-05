#!/usr/bin/env bash
set -euo pipefail

echo "=== Cosmog Device Panel Setup ==="
echo ""

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKSPACE"

# Create managed folders
echo "Creating managed folders..."
mkdir -p base_apks split_apks plugin_libs cosmog_zips cosmog_updates downloads device_configs

# Copy example files if real ones don't exist
if [ ! -f known_devices.json ]; then
  cp known_devices.example.json known_devices.json
  echo "Created known_devices.json from example"
fi

# Docker setup
DOCKER_MODE=0
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  echo "Docker detected."
  read -r -p "Build and start with Docker? [Y/n]: " DOCKER_CHOICE
  if [[ "${DOCKER_CHOICE,,}" != "n" ]]; then
    DOCKER_MODE=1
  fi
else
  echo "Docker not available — will run directly with Python."
fi

echo ""
echo "Setup complete. Next steps:"
echo ""
echo "1. Place your asset files in the managed folders:"
echo "   - Put your base APK in:      $WORKSPACE/base_apks/"
echo "   - Put your split APK in:     $WORKSPACE/split_apks/"
echo "   - Put your plugin .so in:    $WORKSPACE/plugin_libs/"
echo "   - Put your Cosmog ZIP in:    $WORKSPACE/cosmog_zips/"
echo ""
echo "2. Edit known_devices.json with your device IPs (optional)"
echo ""

if [ "$DOCKER_MODE" -eq 1 ]; then
  echo "Building and starting Docker containers..."
  docker compose up --build -d
  echo ""
  echo "Panel is running:"
  echo "   - Host ADB:   http://127.0.0.1:8090"
  echo "   - Own ADB:    http://127.0.0.1:8091"
  echo ""
  echo "To stop:  docker compose down"
  echo "To view:  docker compose logs -f"
else
  echo "Start the panel:"
  echo "   python3 device_panel.py"
  echo ""
  echo "Then open http://127.0.0.1:8080"
fi
echo ""
echo "WSL users: see README.md for ADB setup notes."
