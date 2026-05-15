#!/usr/bin/env bash
# Lind — Cline CLI launcher (tmux attach-only)
# This script is executed by ttyd when a user connects.
# It ONLY attaches to an existing tmux session (managed by lind-tmux.service).
# If the session doesn't exist, it waits for it to be created.

export TERM=xterm-256color
export PATH="/usr/bin:/usr/local/bin:$PATH"
export HOME=/opt/lind
export TMUX_TMPDIR="/opt/lind/tmux"

TMUX_SOCKET="/opt/lind/tmux/default"
SESSION_NAME="lind"

# Load bash aliases (sudo wrappers for systemctl, apt, docker, etc.)
if [ -f /opt/lind/.bashrc ]; then
    source /opt/lind/.bashrc
fi

# Load API key from file
if [ -z "${CLINE_API_KEY:-}" ]; then
    if [ -f /opt/lind/.cline_api_key ]; then
        export CLINE_API_KEY=$(cat /opt/lind/.cline_api_key)
    fi
fi

cd /opt/lind

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ⚜  Lind — AI Terminal  ⚜                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Wait until tmux session is available
MAX_WAIT=15
for i in $(seq 1 $MAX_WAIT); do
    if tmux -S "$TMUX_SOCKET" has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "[~] Подключаемся к сессии '$SESSION_NAME'..."
        exec tmux -S "$TMUX_SOCKET" attach-session -t "$SESSION_NAME"
    fi
    echo "[.] Ждём tmux-сессию ($i/$MAX_WAIT)..."
    sleep 1
done

echo "[!] Сессия '$SESSION_NAME' не найдена за ${MAX_WAIT}с."
echo "[!] Проверьте: sudo systemctl status lind-tmux"
echo "[!] Терминал будет закрыт через 10 секунд."
sleep 10
exit 1