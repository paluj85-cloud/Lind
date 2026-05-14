#!/usr/bin/env bash
# Lind — Cline CLI launcher
# This script is executed by ttyd when a user connects

export TERM=xterm-256color
export PATH="/usr/bin:/usr/local/bin:$PATH"

# Load API key from environment (set by systemd)
if [ -z "${CLINE_API_KEY:-}" ]; then
    if [ -f /opt/lind/.cline_api_key ]; then
        export CLINE_API_KEY=$(cat /opt/lind/.cline_api_key)
    fi
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ⚜  Lind — AI Terminal  ⚜                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

exec cline
