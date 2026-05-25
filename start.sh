#!/usr/bin/env bash
# PetDigiTwin — Start Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8080}"
PID_FILE="$SCRIPT_DIR/.petdigitwin.pid"
LOG_FILE="$SCRIPT_DIR/.petdigitwin.log"

# ── Guard: already running ───────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    EXISTING_PID=$(cat "$PID_FILE")
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "PetDigiTwin is already running (PID $EXISTING_PID)"
        echo "  Web UI  → http://localhost:$PORT/web"
        echo "  API     → http://localhost:$PORT/api/query"
        echo "  Stop it → ./stop.sh"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# ── Virtual environment ───────────────────────────────────────────────────────
if [[ ! -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi
source "$SCRIPT_DIR/.venv/bin/activate"

# ── Dependencies ─────────────────────────────────────────────────────────────
echo "Checking dependencies..."
pip install -r requirements.txt -q

# ── .env sanity check ────────────────────────────────────────────────────────
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "ERROR: .env file not found. Copy .env.example and fill in your credentials."
    exit 1
fi

# Load env to validate required keys
set -a; source "$SCRIPT_DIR/.env"; set +a

if [[ -z "$MONGODB_URI" ]]; then
    echo "ERROR: MONGODB_URI is not set in .env"
    exit 1
fi
if [[ -z "$GOOGLE_API_KEY" ]]; then
    echo "ERROR: GOOGLE_API_KEY is not set in .env"
    exit 1
fi

# ── Port conflict check ───────────────────────────────────────────────────────
CONFLICT_PID=$(lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P 2>/dev/null | awk 'NR>1 {print $2}' | head -1)
if [[ -n "$CONFLICT_PID" ]]; then
    echo "Port $PORT is already in use by PID $CONFLICT_PID."
    read -r -p "Kill it and continue? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        kill "$CONFLICT_PID"
        sleep 1
    else
        echo "Aborted. Choose a different PORT= value or stop the other process first."
        exit 1
    fi
fi

# ── Start app in background ────────────────────────────────────────────────────
echo "Starting PetDigiTwin on port $PORT..."
USE_VERTEX_SDK="${USE_VERTEX_SDK:-false}" \
    nohup python app.py > "$LOG_FILE" 2>&1 &
APP_PID=$!
echo "$APP_PID" > "$PID_FILE"

# ── Wait for startup ──────────────────────────────────────────────────────────
echo -n "Waiting for server"
for i in $(seq 1 20); do
    sleep 0.5
    if curl -s "http://localhost:$PORT/" >/dev/null 2>&1; then
        echo " ready!"
        break
    fi
    echo -n "."
    if [[ $i -eq 20 ]]; then
        echo ""
        echo "ERROR: Server did not start in time. Check logs: $LOG_FILE"
        exit 1
    fi
done

echo ""
echo "PetDigiTwin is running (PID $APP_PID)"
echo ""
echo "  Web Tester  → http://localhost:$PORT/web"
echo "  Health      → http://localhost:$PORT/"
echo "  API Docs:"
echo "    GET  /api/pets"
echo "    GET  /api/volunteers"
echo "    GET  /api/foods"
echo "    GET  /api/knowledge?condition=joint_pain"
echo "    POST /api/query   body: {\"query\":\"...\",\"pet_id\":\"pet_001\"}"
echo ""
echo "  Logs        → tail -f $LOG_FILE"
echo "  Stop        → ./stop.sh"
