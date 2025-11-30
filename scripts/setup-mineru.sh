#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -d mineru_env ]; then
  echo "mineru_env already exists, skipping setup."
  exit 0
fi

echo "Creating MinerU environment..."
uv venv mineru_env
# Use the venv's python directly to install mineru
uv pip install --python mineru_env/bin/python "mineru"

echo "MinerU environment ready. MinerU binary can be found at mineru_env/bin/mineru"


