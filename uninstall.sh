#!/bin/sh
set -eu

DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
INSTALL_DIR="$DATA_HOME/flylab-pet"
PID_FILE="${XDG_RUNTIME_DIR:-/tmp}/flylab-desktop-fly.pid"

if [ -r "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    case "$pid" in ''|*[!0-9]*) pid='' ;; esac
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

rm -rf "$INSTALL_DIR"
rm -f "$DATA_HOME/applications/flylab-desktop-fly.desktop"
BIN_DIR=${FLYLAB_BIN_DIR:-"$HOME/.local/bin"}
rm -f "$BIN_DIR/flylab-pet"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DATA_HOME/applications" >/dev/null 2>&1 || true
fi

echo "FlyLab Pet удалён. Настройки ~/.config/flylab сохранены."
