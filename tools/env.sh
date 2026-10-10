# Shared settings of the build entry points (sourced, not executed).
# UBC: the ubc executable; default is the ubc bundled with the ubCode extension
# (version-matched to the IDE), else `ubc` on PATH. PYTHON / SPHINX: the
# repository venv (.venv), else PATH.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${UBC:-}" ]]; then
  # no ubCode extension (e.g. CI): ls fails; must not abort callers using `set -euo pipefail`
  UBC="$(ls -d "$HOME"/.vscode/extensions/useblocks.ubcode-*/server/cli/ubc 2>/dev/null | sort -V | tail -1 || true)"
  [[ -x "$UBC" ]] || UBC="$(command -v ubc || true)"
fi
[[ -x "$UBC" ]] || { echo "ubc not found: set UBC=<path to ubc>" >&2; exit 1; }
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"; SPHINX="$ROOT/.venv/bin/sphinx-build"
else
  PYTHON="$(command -v python3)"; SPHINX="$(command -v sphinx-build)"
fi
export UBC PYTHON SPHINX ROOT
