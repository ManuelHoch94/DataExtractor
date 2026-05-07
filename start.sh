#!/usr/bin/env bash
# Start the DataExtractor backend (and frontend when available).
#
# Usage:
#   ./start.sh
#   BACKEND_PORT=9000 FRONTEND_DIR=../my-frontend ./start.sh

set -euo pipefail

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_DIR="${FRONTEND_DIR:-frontend}"

# ── Colours ──────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

step()  { echo -e "\n${CYAN}>>> $*${NC}"; }
ok()    { echo -e "    ${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "    ${YELLOW}[!] $*${NC}"; }
fail()  { echo -e "    ${RED}[X] $*${NC}"; exit 1; }

# ── .env check ───────────────────────────────────────────────────────────────
step "Checking configuration"

if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        warn ".env created from .env.example – fill in your API key and re-run."
        exit 1
    else
        fail ".env not found. Create one with OPENAI_API_KEY=sk-..."
    fi
fi

if ! grep -qE "(OPENAI_API_KEY|ANTHROPIC_API_KEY)=sk-" .env; then
    warn ".env found but no API key detected."
else
    ok ".env looks good"
fi

# ── Python / deps ─────────────────────────────────────────────────────────────
step "Installing backend dependencies"
python3 -m pip install -e "." -q || fail "pip install failed."
ok "Dependencies up to date"

# ── Backend ───────────────────────────────────────────────────────────────────
step "Starting backend on http://localhost:${BACKEND_PORT}"

python3 -m uvicorn main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload &
BACKEND_PID=$!
ok "Backend PID ${BACKEND_PID}"
echo "    Swagger UI : http://localhost:${BACKEND_PORT}/docs"
echo "    Health     : http://localhost:${BACKEND_PORT}/api/v1/health"

# ── Frontend ──────────────────────────────────────────────────────────────────
step "Checking frontend"

if [[ ! -d "${FRONTEND_DIR}" ]]; then
    warn "Frontend directory '${FRONTEND_DIR}' not found – skipping."
else
    step "Starting frontend from '${FRONTEND_DIR}'"
    cd "${FRONTEND_DIR}"

    if [[ -f "pnpm-lock.yaml" ]]; then PM="pnpm"
    elif [[ -f "yarn.lock" ]];     then PM="yarn"
    elif [[ -f "package.json" ]];  then PM="npm"
    else
        warn "No package.json found – skipping frontend."; PM=""
    fi

    if [[ -n "${PM}" ]]; then
        ${PM} run dev &
        FRONTEND_PID=$!
        ok "Frontend PID ${FRONTEND_PID} (${PM})"
    fi
    cd - > /dev/null
fi

# ── Shutdown trap ─────────────────────────────────────────────────────────────
cleanup() {
    echo -e "\n${CYAN}Shutting down...${NC}"
    kill "${BACKEND_PID}" 2>/dev/null || true
    [[ -n "${FRONTEND_PID:-}" ]] && kill "${FRONTEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo -e "\n${GREEN} DataExtractor is running. Press Ctrl+C to stop.${NC}\n"
wait
