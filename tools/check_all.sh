#!/usr/bin/env bash
# Once-per-repository checks (B§8): generated files up to date, variant
# conditions, Kconfig hygiene, BMS pin, skill mirrors. Called by
# tools/build_all.sh and by the CI `checks` job. The variant check also runs
# the alternatives check when product exports exist in build/site/.
set -uo pipefail
source "$(dirname "$0")/env.sh"
cd "$ROOT"

failed=()
check() { local name="$1"; shift; if "$@"; then :; else failed+=("$name"); fi; }
check drift "$PYTHON" tools/kconfig2variants.py --all --vscode --check
check variants "$PYTHON" tools/check_variants.py
check kconfig "$PYTHON" tools/check_kconfig.py
check bms-pin "$PYTHON" tools/pin_bms.py --check
check skills "$PYTHON" tools/check_skill_mirrors.py

if ((${#failed[@]})); then
  echo "FAILED checks: ${failed[*]}"; exit 1
fi
