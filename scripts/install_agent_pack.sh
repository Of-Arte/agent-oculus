#!/usr/bin/env bash
set -euo pipefail

# Installs the local agent pack manifest into the current user's Hermes home.
# This enables Hermes CLI /agent oculus.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/oculus.agent-pack.yaml"

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

echo "Also install the Hermes skill (native scope + intent mapping):"
echo "  ./scripts/install_oculus_skill.sh"

echo "Next steps:"
echo "  1) Create profile (one-time): hermes profile create oculus"
echo "  2) Launch from anywhere: /agent oculus  (inside Hermes CLI)"
