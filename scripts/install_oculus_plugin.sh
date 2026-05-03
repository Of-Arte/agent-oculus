#!/usr/bin/env bash
set -euo pipefail

# Installs the Oculus Hermes plugin into ~/.hermes/plugins/oculus
# so it can be enabled with: hermes plugins enable oculus

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/hermes/plugin/oculus"

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

echo "Note: ./scripts/install_agent_pack.sh will also enable the plugin + set OCULUS_WORKDIR automatically (when Hermes is installed)."
echo "Manual enable (if needed):"
echo "  hermes plugins enable oculus"
echo "Manual env (if needed):"
echo "  hermes -p oculus config env-path"
echo "  OCULUS_WORKDIR=$REPO_ROOT"
echo "If tools don't appear in-session: /tools -> enable 'oculus'"