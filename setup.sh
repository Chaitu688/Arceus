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
echo "3. Start the panel:"
echo "   - Direct:   python3 device_panel.py"
echo "   - Docker:   docker compose up --build"
echo ""
echo "4. Open http://127.0.0.1:8080"
echo ""
echo "WSL users: see README.md for ADB setup notes."
