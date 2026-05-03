#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus Hermes plugin into ~/.hermes/plugins/oculus
# so it can be enabled with: hermes plugins enable oculus

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/.hermes/plugins/oculus"

if [ ! -d "$SRC_DIR" ]; then
  echo "Missing plugin dir: $SRC_DIR" >&2
  exit 1
fi

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
DST_DIR="$HERMES_HOME/plugins/oculus"

mkdir -p "$HERMES_HOME/plugins"
rm -rf "$DST_DIR"
cp -R "$SRC_DIR" "$DST_DIR"

echo "Installed Hermes plugin to: $DST_DIR"

echo "Next steps:"
echo "  1) Enable plugin: hermes plugins enable oculus"
echo "  2) In your oculus profile env, set OCULUS_WORKDIR to this repo path."
echo "     Example: OCULUS_WORKDIR=$REPO_ROOT"

echo "  3) Start Hermes and enable the plugin toolset 'oculus' (if not already)"
echo "     via: /tools  (or hermes tools)"
