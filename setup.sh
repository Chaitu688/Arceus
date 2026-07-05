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
ALREADY_RUNNING=0
COMPOSE_FILE="docker-compose.yml"
MODE=""

# Check if panel is already running
if command -v docker &>/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'cosmog-device-panel'; then
  ALREADY_RUNNING=1
  MODE="docker"
  echo "Panel already running (Docker)."
elif pgrep -f "device_panel.py" &>/dev/null; then
  ALREADY_RUNNING=1
  MODE="direct"
  echo "Panel already running (PID: $(pgrep -f device_panel.py))."
fi

if [ "$ALREADY_RUNNING" -eq 1 ]; then
  if [ "$IS_WSL" -eq 1 ]; then
    echo "   http://127.0.0.1:8090"
  else
    echo "   http://127.0.0.1:8080"
  fi
else
  if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    if [ "$IS_WSL" -eq 1 ]; then
      COMPOSE_FILE="docker-compose.wsl.yml"
      echo "Docker Desktop on WSL — using port mapping mode."
    fi
    echo "Starting with Docker..."
    docker compose -f "$COMPOSE_FILE" up --build -d
    MODE="docker"
    if [ "$IS_WSL" -eq 1 ]; then
      echo "Panel running at: http://127.0.0.1:8090"
    else
      echo "Panel running at:"
      echo "   - Host ADB:  http://127.0.0.1:8090"
      echo "   - Own ADB:   http://127.0.0.1:8091"
    fi
  else
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
fi

# --- Install auto-start on boot ---
echo ""

AUTO_START_INSTALLED=0

if command -v systemctl &>/dev/null && sudo -n true 2>/dev/null; then
  SERVICE_NAME="cosmog-panel"
  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

  if [ "$MODE" = "docker" ]; then
    sudo tee "$SERVICE_FILE" > /dev/null << SYSTEMD_EOF
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
SYSTEMD_EOF
  else
    ENV_LINE=""
    if [ "$IS_WSL" -eq 1 ]; then
      ENV_LINE="Environment=ADB_SERVER_SOCKET=tcp:127.0.0.1:5037"
    fi
    sudo tee "$SERVICE_FILE" > /dev/null << SYSTEMD_EOF
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
SYSTEMD_EOF
  fi

  sudo systemctl daemon-reload 2>/dev/null || true
  sudo systemctl enable "$SERVICE_NAME" 2>/dev/null || true
  AUTO_START_INSTALLED=1
  echo "Auto-start installed — panel will start on boot."
  echo "   sudo systemctl start|stop|restart|status $SERVICE_NAME"
fi

if [ "$AUTO_START_INSTALLED" -eq 0 ]; then
  if [ "$IS_WSL" -eq 1 ]; then
    BASHRC_LINE="cd $WORKSPACE && bash setup.sh # cosmog-panel"
    if grep -q 'cosmog-panel' ~/.bashrc 2>/dev/null; then
      echo "Auto-start already in ~/.bashrc — panel starts on WSL launch."
    else
      echo "$BASHRC_LINE" >> ~/.bashrc
      echo "Added auto-start to ~/.bashrc — panel starts whenever WSL opens."
    fi
  else
    echo "Auto-start not configured (sudo not available)."
    echo "Run './setup.sh' after reboots, or add it to your startup scripts."
  fi
fi

echo ""
