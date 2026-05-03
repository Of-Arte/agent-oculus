#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus skill into Hermes so /agent oculus launches with native context.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/hermes-skill-oculus.md"

if [ ! -f "$SRC" ]; then
  echo "Missing skill source: $SRC" >&2
  exit 1
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DST_DIR="$HERMES_HOME/skills/oculus"
DST="$DST_DIR/SKILL.md"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

echo "Installed Hermes skill: $DST"
