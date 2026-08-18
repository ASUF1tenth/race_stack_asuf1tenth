#!/bin/bash
set -e

echo "=========================================================="
echo "    ASU F1TENTH Host Device Setup (udev rules installer)  "
echo "=========================================================="
echo "Configuring persistent serial ports:"
echo "  - ESP32-C3 (IMU & Steering) -> /dev/esp"
echo "  - FESC (BLDC Motor)         -> /dev/fesc"
echo "  - RPLiDAR (Laser Scanner)   -> /dev/rplidar"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RULE_SRC="${SCRIPT_DIR}/99-f1tenth.rules"

if [ ! -f "$RULE_SRC" ]; then
    echo "[ERROR] Could not find rule file at: $RULE_SRC"
    exit 1
fi

echo "Copying rules to /etc/udev/rules.d/99-f1tenth.rules (requires sudo)..."
sudo cp "$RULE_SRC" /etc/udev/rules.d/99-f1tenth.rules

echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "[SUCCESS] udev rules installed and triggered!"
echo "Active device symlinks:"
ls -la /dev/esp /dev/fesc /dev/rplidar 2>/dev/null || echo "Note: Plugged devices will now automatically link to /dev/esp, /dev/fesc, and /dev/rplidar"
echo "=========================================================="
