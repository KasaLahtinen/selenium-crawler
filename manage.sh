#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "=========================================="
echo "  Selenium Crawler & IRC Bot Manager      "
echo "  (Podman Compose Edition)                "
echo "=========================================="
echo ""

# 1. Check for configuration files
if [ ! -f "Gemini-IRC-bot/config.yaml" ]; then
    echo "[ERROR] Missing Gemini-IRC-bot/config.yaml"
    echo "Please create the configuration file before running."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found. Ensure GEMINI_API_KEY is set!"
fi

# 2. Configure Podman to use cgroupfs and file logging to bypass DBus/systemd errors
cat <<EOF > "$BASE_DIR/containers.conf"
[engine]
cgroup_manager = "cgroupfs"
events_logger = "file"
EOF
export CONTAINERS_CONF="$BASE_DIR/containers.conf"

if [ "$1" == "stop" ] || [ "$1" == "down" ]; then
    echo "[INFO] Stopping and removing the Podman container stack..."
    podman-compose down
    exit 0
fi

# 3. Start services using podman-compose
echo "[INFO] Spinning up the Podman container stack..."
if command -v podman-compose &> /dev/null; then
    podman-compose up -d --build
else
    echo "[ERROR] podman-compose is not installed or not in PATH!"
    echo "Please install it (e.g., pip3 install podman-compose or sudo apt install podman-compose)."
    exit 1
fi

echo ""
echo "[SUCCESS] All services are running in the background via Podman!"
echo " - View Bot logs: podman-compose logs -f bot"
echo " - View API logs: podman-compose logs -f api"
echo " - Stop services: ./manage.sh stop"
