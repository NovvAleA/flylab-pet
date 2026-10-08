#!/bin/sh
set -eu

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
PID_FILE="$RUNTIME_DIR/flylab-desktop-fly.pid"
LOCK_FILE="$RUNTIME_DIR/flylab-desktop-fly.lock"
LOG_FILE="$RUNTIME_DIR/flylab-desktop-fly.log"

toggle_fly() {
    if [ -r "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        case "$pid" in
            ''|*[!0-9]*) pid='' ;;
        esac
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            exit 0
        fi
        rm -f "$PID_FILE"
    fi

    # Detach from the short-lived desktop launcher, otherwise some shells send
    # SIGHUP as soon as the click handler exits.
    nohup "$APP_DIR/run.sh" 9>&- >>"$LOG_FILE" 2>&1 </dev/null &
    echo "$!" >"$PID_FILE"
}

# Avoid launching two flies when the dock icon is double-clicked.
(
    flock -n 9 || exit 0
    toggle_fly
) 9>"$LOCK_FILE"
