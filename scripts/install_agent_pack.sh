#!/usr/bin/env bash
set -euo pipefail

# Installs the local agent pack manifest into the current user's Hermes home.
# This enables Hermes CLI /agent oculus.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/hermes/agent-packs/oculus.yaml"

if [ ! -f "$SRC" ]; then
  echo "Missing manifest: $SRC" >&2
  exit 1
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DST_DIR="$HERMES_HOME/agent-packs"
DST="$DST_DIR/oculus.yaml"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

echo "Installed agent pack: $DST"

# Optional: install the skill + plugin so Hermes boots with the right scope and tools.
# We do this here because users expect one command.
if [ -x "$REPO_ROOT/scripts/install_oculus_skill.sh" ]; then
  "$REPO_ROOT/scripts/install_oculus_skill.sh" || true
fi

if [ -x "$REPO_ROOT/scripts/install_oculus_plugin.sh" ]; then
  "$REPO_ROOT/scripts/install_oculus_plugin.sh" || true
fi

if [ -x "$REPO_ROOT/scripts/install_oculus_skin.sh" ]; then
  "$REPO_ROOT/scripts/install_oculus_skin.sh" || true
fi

# If Hermes is installed, we can do the last-mile setup automatically.
if command -v hermes >/dev/null 2>&1; then
  # Create profile if missing (ignore errors if it already exists)
  hermes profile create oculus >/dev/null 2>&1 || true

  # Enable plugin (ignore if already enabled)
  hermes plugins enable oculus >/dev/null 2>&1 || true

  # Set OCULUS_WORKDIR in the oculus profile env so the plugin can import tools/*.
  ENV_PATH="$(hermes -p oculus config env-path 2>/dev/null | tail -n 1 || true)"
  if [ -n "$ENV_PATH" ]; then
    mkdir -p "$(dirname "$ENV_PATH")"
    touch "$ENV_PATH"
    if grep -q '^OCULUS_WORKDIR=' "$ENV_PATH"; then
      # replace in-place
      perl -pi -e "s|^OCULUS_WORKDIR=.*$|OCULUS_WORKDIR=$REPO_ROOT|" "$ENV_PATH" || true
    else
      echo "OCULUS_WORKDIR=$REPO_ROOT" >> "$ENV_PATH"
    fi
  fi
fi

echo ""
echo "Done. Quick start:" 
echo "  1) Start Hermes: hermes"
echo "  2) In-session: /agent oculus"
echo "  3) If tools aren't visible: /tools -> enable 'oculus'"
echo ""
echo "Optional polish:" 
echo "  - Activate Oculus skin: hermes config set display.skin oculus"
