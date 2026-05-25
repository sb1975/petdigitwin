#!/usr/bin/env bash
# PetDigiTwin — Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.petdigitwin.pid"
PORT="${PORT:-8080}"

stop_by_pid_file() {
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping PetDigiTwin (PID $PID)..."
            kill "$PID"
            # Wait up to 5 seconds for graceful shutdown
            for i in $(seq 1 10); do
                sleep 0.5
                kill -0 "$PID" 2>/dev/null || break
            done
            # Force kill if still alive
            kill -0 "$PID" 2>/dev/null && kill -9 "$PID" && echo "Force stopped."
            rm -f "$PID_FILE"
            echo "PetDigiTwin stopped."
            return 0
        else
            echo "PID $PID is no longer running."
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

stop_by_port() {
    CONFLICT_PID=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P 2>/dev/null | awk 'NR>1 {print $2}' | head -1)
    if [[ -n "$CONFLICT_PID" ]]; then
        echo "Found process $CONFLICT_PID on port $PORT. Stopping..."
        kill "$CONFLICT_PID"
        sleep 1
        kill -0 "$CONFLICT_PID" 2>/dev/null && kill -9 "$CONFLICT_PID"
        rm -f "$PID_FILE"
        echo "PetDigiTwin stopped (via port scan)."
        return 0
    fi
    return 1
}

# Try PID file first, fall back to port scan
if ! stop_by_pid_file; then
    if ! stop_by_port; then
        echo "PetDigiTwin does not appear to be running."
    fi
fi
