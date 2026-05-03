#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus Hermes skin into ~/.hermes/skins/oculus.yaml

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/hermes/skins/oculus.yaml"

if [ ! -f "$SRC" ]; then
  echo "Missing skin file: $SRC" >&2
  exit 1
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DST_DIR="$HERMES_HOME/skins"
DST="$DST_DIR/oculus.yaml"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

echo "Installed Hermes skin: $DST"

echo "Optional: activate it"
echo "  hermes config set display.skin oculus"
