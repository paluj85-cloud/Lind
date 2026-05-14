#!/bin/bash
# Lind — Full setup script for VPS
# Run as: sudo bash setup.sh
set -euo pipefail

echo "=== Lind Setup ==="
echo "Step 1/6: Installing Node.js 22 LTS..."
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
echo "Node.js: $(node --version)"

echo "Step 2/6: Installing Cline CLI globally..."
npm install -g cline
echo "Cline CLI: $(which cline)"

echo "Step 3/6: Installing ttyd..."
wget -q https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 -O /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd
echo "ttyd: $(ttyd --version)"

echo "Step 4/6: Creating 'lind' user..."
if ! id lind &>/dev/null; then
    useradd -r -s /bin/bash -m lind
    echo "User 'lind' created."
else
    echo "User 'lind' already exists."
fi

echo "Step 5/6: Installing systemd service and Nginx config..."
cp /opt/lind/systemd/lind-ttyd.service /etc/systemd/system/lind-ttyd.service
systemctl daemon-reload
systemctl enable --now lind-ttyd

cp /opt/lind/nginx/lind.adndexis.ru.conf /etc/nginx/sites-available/lind.adndexis.ru
ln -sf /etc/nginx/sites-available/lind.adndexis.ru /etc/nginx/sites-enabled/lind.adndexis.ru
nginx -t && systemctl restart nginx

echo "Step 6/6: Done! Verify:"
echo "  curl -u Paluj:Pas22073814 http://lind.adndexis.ru/cline"
echo "  systemctl status lind-ttyd"
