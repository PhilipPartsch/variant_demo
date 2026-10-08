#!/usr/bin/env bash
# Build one product end to end (B§8) — the same command locally and in CI:
#   CMake configure (variant data, BMS needs, compile database) + build + CTest
#   -> ubc check -> ubc build needs -> ubCode HTML -> sphinx-needs HTML (-W)
# Output: build/site/<product>/{ubcode,sphinx}/, {ubc,sphinx}.needs.json, logs.
#
# Usage: tools/build_product.sh <product>      (configs/<product>_defconfig)
# The build writes build/active/ for this product; tools/build_all.sh restores
# the IDE's product afterwards.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$ROOT"

p="${1:?usage: $0 <product>}"
[[ -f "configs/${p}_defconfig" ]] || { echo "unknown product '$p' (no configs/${p}_defconfig)" >&2; exit 2; }
site="build/site/$p"; logs="$site/logs"
rm -rf "$site"; mkdir -p "$logs"

step() { # step <name> <command...>: run, log, stop on failure with the log tail
  local name="$1"; shift
  if "$@" >"$logs/$name.log" 2>&1; then
    echo "  ok    $name"
  else
    echo "  FAIL  $name (log: $logs/$name.log)"; tail -n 30 "$logs/$name.log"; exit 1
  fi
}

echo "== $p"
step configure cmake -S . -B "build/cmake/$p" -G Ninja -DVARIANT="$p" -DCMAKE_BUILD_TYPE=Debug
step build cmake --build "build/cmake/$p"
step ctest ctest --test-dir "build/cmake/$p" --output-on-failure
# What CMake Tools does with cmake.copyCompileCommands: codelinks reads the active copy.
cp "build/cmake/$p/compile_commands.json" build/compile_commands.json
step ubc-check "$UBC" check
step ubc-needs "$UBC" build needs -o "$site/ubc.needs.json"
step ubc-html "$UBC" build html -o "$site/ubcode"
step sphinx "$SPHINX" -E -W --keep-going -b html docs "$site/sphinx"
cp "$site/sphinx/needs.json" "$site/sphinx.needs.json"
"$PYTHON" - "$site" <<'PY'
import json, sys
from pathlib import Path
site = Path(sys.argv[1])
def ids(f):
    d = json.loads(f.read_text())
    v = d["versions"]
    return set(v[d.get("current_version") or next(iter(v))]["needs"])
u, s = ids(site / "ubc.needs.json"), ids(site / "sphinx.needs.json")
bms = sum(i.startswith("BMS_") for i in u)
print(f"  {'ok  ' if u == s else 'FAIL'}  parity: {len(u)} needs ({bms} BMS_*) ubc / {len(s)} sphinx")
if u != s:
    print("        only ubc:", sorted(u - s)[:10], " only sphinx:", sorted(s - u)[:10])
    sys.exit(1)
PY
