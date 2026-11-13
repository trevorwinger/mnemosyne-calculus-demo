#!/usr/bin/env bash
# Start a local Mnemosyne Calculus demonstration with Ollama and Gemma.
# Supported unattended path: macOS or Linux with Docker/Compose already running.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_NAME="${MNEMOSYNE_MODEL:-gemma3:4b}"
WEB_URL="http://localhost:3000"

info() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }

case "${1:-}" in
  -h|--help)
    printf 'Usage: ./bootstrap-demo.sh\n\nOptional environment variables:\n  MNEMOSYNE_MODEL=gemma3:4b   Ollama model to pull and use\n  APEX_TEXTBOOK_PDF=/path/book.pdf   Copy a lawful APEX PDF before seeding\n'
    exit 0
    ;;
  "") ;;
  *) fail "Unknown argument: $1 (use --help)" ;;
esac

command -v curl >/dev/null 2>&1 || fail "curl is required to install and check Ollama."
command -v docker >/dev/null 2>&1 || fail "Install Docker Desktop (macOS/Windows) or Docker Engine with the Compose plugin (Linux), start it, then rerun this script."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required. Update Docker Desktop/Engine, then rerun this script."
docker info >/dev/null 2>&1 || fail "Docker is installed but its daemon is not running. Start Docker Desktop, wait for it to finish starting, then rerun this script."

case "$(uname -s)" in
  Darwin|Linux) ;;
  *) fail "Automatic Ollama installation is supported by this script on macOS and Linux. On Windows, use WSL2 or install Ollama from https://ollama.com/download, then rerun from WSL2." ;;
esac

if ! command -v ollama >/dev/null 2>&1; then
  info "Installing Ollama"
  curl -fsSL https://ollama.com/install.sh | sh
fi

if ! curl --silent --fail --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
  info "Starting Ollama"
  nohup ollama serve >"${TMPDIR:-/tmp}/mnemosyne-ollama.log" 2>&1 &
  for attempt in $(seq 1 30); do
    if curl --silent --fail --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi
curl --silent --fail --max-time 3 http://localhost:11434/api/tags >/dev/null 2>&1 || fail "Ollama did not start. Inspect ${TMPDIR:-/tmp}/mnemosyne-ollama.log and run `ollama serve` manually."

info "Pulling $MODEL_NAME (the first download can take several minutes)"
ollama pull "$MODEL_NAME"

mkdir -p "$ROOT_DIR/.local-content"
if [[ -n "${APEX_TEXTBOOK_PDF:-}" ]]; then
  [[ -f "$APEX_TEXTBOOK_PDF" ]] || fail "APEX_TEXTBOOK_PDF does not point to a readable file."
  if [[ "$APEX_TEXTBOOK_PDF" != "$ROOT_DIR/.local-content/apex-novideo.pdf" ]]; then
    info "Adding the local textbook PDF to the private demo folder"
    cp "$APEX_TEXTBOOK_PDF" "$ROOT_DIR/.local-content/apex-novideo.pdf"
  fi
fi

export PROTOTYPE_DEFAULT_MODEL="$MODEL_NAME"
cd "$ROOT_DIR"
info "Building and starting Mnemosyne (first build can take several minutes)"
docker compose up -d --build

info "Waiting for the API"
for attempt in $(seq 1 90); do
  if curl --silent --fail --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl --silent --fail --max-time 3 http://localhost:8000/health >/dev/null 2>&1 || {
  docker compose logs --tail=80 api >&2 || true
  fail "The API did not become ready."
}

info "Seeding the Calculus course"
docker compose exec -T api python -m app.seed

info "Waiting for the web app"
for attempt in $(seq 1 60); do
  if curl --silent --fail --max-time 2 "$WEB_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl --silent --fail --max-time 3 "$WEB_URL" >/dev/null 2>&1 || {
  docker compose logs --tail=80 web >&2 || true
  fail "The web app did not become ready."
}

info "Mnemosyne is ready at $WEB_URL"
case "$(uname -s)" in
  Darwin) open "$WEB_URL" >/dev/null 2>&1 || true ;;
  Linux) command -v xdg-open >/dev/null 2>&1 && xdg-open "$WEB_URL" >/dev/null 2>&1 || true ;;
esac
