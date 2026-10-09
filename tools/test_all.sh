#!/usr/bin/env bash
# Run the tests L1-L6 of plan 5 (T§1) — the same command CI calls.
#   1. tools/build_all.sh: every product with both toolchains + once-per-repo checks
#      (L3, L4 and L6 read its outputs in build/site/<product>/)
#   2. pytest tools/tests: L1 tooling, L2 build integration, L3 docs per product,
#      L4 content, L5 negative / mutation, L6 C code
# Extra pytest arguments are passed through, e.g. `tools/test_all.sh -k doc0`.
# SKIP_BUILD=1 reuses the outputs of the last build_all run.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$ROOT"

if [[ "${SKIP_BUILD:-0}" != 1 ]]; then
  tools/build_all.sh
fi
"$PYTHON" -m pytest -q -rxs tools/tests "$@"
