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
echo "Asset folders ready. PoGo updates download automatically from the mirror."
echo "To update PoGo: connect a device, click 'Update PoGo', pick a version."
echo ""
echo "Optional: drop a Cosmog ZIP in: $WORKSPACE/cosmog_zips/"
echo "Then click 'Update Cosmog' on a connected device."
echo ""

# --- Start the panel ---
STARTED=0
COMPOSE_FILE="docker-compose.yml"
MODE=""

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
  if [ "$IS_WSL" -eq 1 ]; then
    COMPOSE_FILE="docker-compose.wsl.yml"
    echo "Docker Desktop on WSL — using port mapping mode."
  fi
  echo "Starting with Docker..."
  docker compose -f "$COMPOSE_FILE" up --build -d
  STARTED=1
  MODE="docker"
  if [ "$IS_WSL" -eq 1 ]; then
    echo "Panel running at: http://127.0.0.1:8090"
  else
    echo "Panel running at:"
    echo "   - Host ADB:  http://127.0.0.1:8090"
    echo "   - Own ADB:   http://127.0.0.1:8091"
  fi
fi

if [ "$STARTED" -eq 0 ]; then
  echo "Starting panel directly..."
  MODE="direct"
  if [ "$IS_WSL" -eq 1 ]; then
    echo "Make sure Windows ADB is running (adb -a nodaemon server in PowerShell)."
    export ADB_SERVER_SOCKET=tcp:127.0.0.1:5037
  fi
  nohup python3 "$WORKSPACE/device_panel.py" > /dev/null 2>&1 &
  echo "Panel running at: http://127.0.0.1:8080"
  echo "PID: $!"
fi

# --- Install systemd service for auto-start on boot ---
echo ""

if command -v systemctl &>/dev/null; then
  SERVICE_NAME="cosmog-panel"
  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

  if [ "$MODE" = "docker" ]; then
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Cosmog Device Panel (Docker)
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER
WorkingDirectory=$WORKSPACE
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down

[Install]
WantedBy=multi-user.target
EOF
  else
    ENV_LINE=""
    if [ "$IS_WSL" -eq 1 ]; then
      ENV_LINE="Environment=ADB_SERVER_SOCKET=tcp:127.0.0.1:5037"
    fi
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Cosmog Device Panel
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKSPACE
$ENV_LINE
ExecStart=/usr/bin/python3 $WORKSPACE/device_panel.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
  fi

  sudo systemctl daemon-reload
  sudo systemctl enable "$SERVICE_NAME"
  echo "Auto-start installed — panel will start on boot."
  echo ""
  echo "Manual control:"
  echo "   sudo systemctl start|stop|restart|status $SERVICE_NAME"
else
  echo "systemd not available — auto-start on boot not configured."
  echo "Add './setup.sh' to your startup scripts manually."
fi

echo ""
