#!/usr/bin/env bash
# Run pytest using a project venv when present (recommended).
# Prefer .venv-py311 (matches CI Python 3.11+); a plain .venv may be an older
# Python without homeassistant — see TESTING.md.
# Falls back to python3 -m pytest.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "${ROOT}/.venv-py311/bin/python" ]]; then
  exec "${ROOT}/.venv-py311/bin/python" -m pytest "$@"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
  exec "${ROOT}/.venv/bin/python" -m pytest "$@"
else
  exec python3 -m pytest "$@"
fi
