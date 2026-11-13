#!/usr/bin/env bash
# Start a local Mnemosyne Calculus demonstration with Ollama and Gemma.
# Supported unattended path: macOS or Linux with Docker/Compose already running.
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_NAME="${MNEMOSYNE_MODEL:-gemma4:12b}"
WEB_PORT="${MNEMOSYNE_WEB_PORT:-3100}"
API_PORT="${MNEMOSYNE_API_PORT:-8100}"
WEB_URL="http://localhost:$WEB_PORT"
BUNDLED_TEXTBOOK_ARCHIVE="$ROOT_DIR/assets/apex-calculus-5e.pdf.zip"
BUNDLED_TEXTBOOK_SHA256="98db405b9c7207f890cddf78e1406a34898099d300c338119194d4706d9ea8ce"
PRIVATE_TEXTBOOK="$ROOT_DIR/.local-content/apex-novideo.pdf"

info() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nError: %s\n' "$*" >&2; exit 1; }
DOCKER_CMD=(docker)
docker_cmd() { "${DOCKER_CMD[@]}" "$@"; }

ensure_port_available() {
  local port="$1" label="$2" owner
  if command -v nc >/dev/null 2>&1 && nc -z 127.0.0.1 "$port" >/dev/null 2>&1; then
    owner="$(docker_cmd ps --filter "publish=$port" --format '{{.Label "com.docker.compose.project"}}' 2>/dev/null | head -n 1)"
    [[ "$owner" == "mnemosyne-calculus-demo" ]] && return
    fail "Port $port is already in use ($label). Choose another port, for example: MNEMOSYNE_${label}_PORT=3200 ./bootstrap-demo.sh"
  fi
}

install_docker_macos() {
  local architecture download_dir disk_image mount_point
  architecture="$(uname -m)"
  case "$architecture" in
    arm64) architecture="arm64" ;;
    x86_64) architecture="amd64" ;;
    *) fail "Unsupported macOS architecture: $architecture" ;;
  esac
  command -v hdiutil >/dev/null 2>&1 || fail "hdiutil is required to install Docker Desktop on macOS."
  download_dir="$(mktemp -d)"
  disk_image="$download_dir/Docker.dmg"
  mount_point="$download_dir/Docker"
  mkdir -p "$mount_point"
  info "Installing Docker Desktop for macOS (administrator approval is required)"
  curl -fL "https://desktop.docker.com/mac/main/$architecture/Docker.dmg" -o "$disk_image"
  hdiutil attach "$disk_image" -nobrowse -mountpoint "$mount_point" >/dev/null
  sudo "$mount_point/Docker.app/Contents/MacOS/install" --accept-license --user "$(id -un)"
  hdiutil detach "$mount_point" >/dev/null
  rm -rf "$download_dir"
}

install_docker_linux() {
  command -v sudo >/dev/null 2>&1 || fail "Docker Engine installation on Linux requires sudo."
  info "Installing Docker Engine and Docker Compose for Linux (administrator approval is required)"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER" || true
  sudo systemctl enable --now docker 2>/dev/null || true
}

ensure_docker() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    return
  fi

  case "$(uname -s)" in
    Darwin)
      if ! command -v docker >/dev/null 2>&1; then
        install_docker_macos
      fi
      info "Starting Docker Desktop"
      open -a Docker >/dev/null 2>&1 || fail "Docker Desktop was installed but could not be launched. Open it from Applications, then rerun this script."
      ;;
    Linux)
      if ! command -v docker >/dev/null 2>&1; then
        install_docker_linux
      fi
      if ! docker info >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
        DOCKER_CMD=(sudo docker)
      fi
      ;;
    *) fail "Use bootstrap-demo.ps1 on Windows. Automatic Docker installation from this shell is supported only on macOS and Linux." ;;
  esac

  info "Waiting for Docker"
  for attempt in $(seq 1 90); do
    if docker_cmd info >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done
  fail "Docker did not become ready. On Linux, sign out and back in after installation, then rerun. On macOS, complete Docker Desktop's first-run setup and rerun."
}

case "${1:-}" in
  -h|--help)
    printf 'Usage: ./bootstrap-demo.sh\n\nOptional environment variables:\n  MNEMOSYNE_MODEL=gemma4:12b   Ollama model to pull and use\n  APEX_TEXTBOOK_PDF=/path/book.pdf   Use a local lawful APEX PDF instead of the bundled archive\n'
    exit 0
    ;;
  "") ;;
  *) fail "Unknown argument: $1 (use --help)" ;;
esac

command -v curl >/dev/null 2>&1 || fail "curl is required to install and check Ollama."
ensure_docker
docker_cmd compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required. Update Docker Desktop/Engine, then rerun this script."
ensure_port_available "$WEB_PORT" "WEB"
ensure_port_available "$API_PORT" "API"

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
  if [[ "$APEX_TEXTBOOK_PDF" != "$PRIVATE_TEXTBOOK" ]]; then
    info "Adding the local textbook PDF to the private demo folder"
    cp "$APEX_TEXTBOOK_PDF" "$PRIVATE_TEXTBOOK"
  fi
elif [[ ! -f "$PRIVATE_TEXTBOOK" ]]; then
  [[ -f "$BUNDLED_TEXTBOOK_ARCHIVE" ]] || fail "The bundled APEX textbook archive is missing. Restore assets/apex-calculus-5e.pdf.zip from Git."
  command -v unzip >/dev/null 2>&1 || fail "unzip is required to unpack the bundled textbook. Install it, then rerun this script."
  info "Verifying and unpacking the bundled APEX Calculus textbook"
  if command -v shasum >/dev/null 2>&1; then
    printf '%s  %s\n' "$BUNDLED_TEXTBOOK_SHA256" "$BUNDLED_TEXTBOOK_ARCHIVE" | shasum -a 256 -c - >/dev/null || fail "The bundled textbook archive checksum did not match. Re-clone the repository."
  elif command -v sha256sum >/dev/null 2>&1; then
    printf '%s  %s\n' "$BUNDLED_TEXTBOOK_SHA256" "$BUNDLED_TEXTBOOK_ARCHIVE" | sha256sum -c - >/dev/null || fail "The bundled textbook archive checksum did not match. Re-clone the repository."
  fi
  unzip -p "$BUNDLED_TEXTBOOK_ARCHIVE" apex-novideo.pdf >"$PRIVATE_TEXTBOOK.part" || fail "Could not unpack the bundled textbook archive."
  mv "$PRIVATE_TEXTBOOK.part" "$PRIVATE_TEXTBOOK"
fi

export PROTOTYPE_DEFAULT_MODEL="$MODEL_NAME"
export MNEMOSYNE_WEB_PORT="$WEB_PORT"
export MNEMOSYNE_API_PORT="$API_PORT"
cd "$ROOT_DIR"
info "Building and starting Mnemosyne (first build can take several minutes)"
docker_cmd compose up -d --build

info "Waiting for the API"
for attempt in $(seq 1 90); do
  if curl --silent --fail --max-time 2 "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl --silent --fail --max-time 3 "http://localhost:$API_PORT/health" >/dev/null 2>&1 || {
  docker_cmd compose logs --tail=80 api >&2 || true
  fail "The API did not become ready."
}

info "Seeding the Calculus course"
docker_cmd compose exec -T api python -m app.seed

info "Waiting for the web app"
for attempt in $(seq 1 60); do
  if curl --silent --fail --max-time 2 "$WEB_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl --silent --fail --max-time 3 "$WEB_URL" >/dev/null 2>&1 || {
  docker_cmd compose logs --tail=80 web >&2 || true
  fail "The web app did not become ready."
}

info "Mnemosyne is ready at $WEB_URL"
case "$(uname -s)" in
  Darwin) open "$WEB_URL" >/dev/null 2>&1 || true ;;
  Linux) command -v xdg-open >/dev/null 2>&1 && xdg-open "$WEB_URL" >/dev/null 2>&1 || true ;;
esac
