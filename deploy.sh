#!/bin/bash
# Run this on Orange Pi Zero 3 (Armbian) as root
set -e

DEST=/opt/printserver

# 1. Dependencies
apt install -y python3-pip python3-venv

# 2. Project directory
mkdir -p $DEST
cp app.py config.py epl.py requirements.txt .env $DEST/

# 3. Virtualenv + packages
python3 -m venv $DEST/venv
$DEST/venv/bin/pip install -r $DEST/requirements.txt

# 4. systemd service
cp printserver.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable printserver
systemctl restart printserver

echo ""
echo "=== Done. Test commands ==="
echo "# Blank label test:"
echo "  printf 'N\\nP1\\n' > /dev/usb/lp0"
echo ""
echo "# HTTP test:"
echo "  curl -X POST http://localhost:8050/print \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"length\":1200,\"qty\":1,\"profile_code\":\"П-60x60\",\"profile_name\":\"Стойка угловая\",\"order_title\":\"Перегородка офис 3 этаж\",\"order_number\":\"2024-042\",\"section_path\":\"Секция_А/Левая_часть\",\"color\":\"RAL 9010\"}'"
echo ""
echo "# Health check:"
echo "  curl http://localhost:8050/health"
echo ""
echo "# Logs:"
echo "  journalctl -u printserver -f"
