#!/usr/bin/env bash
# Build every product (configs/*_defconfig) and run the once-per-repo checks
# (B§8). Saves build/active/ and build/compile_commands.json first and restores
# them at the end, so the IDE keeps showing the product selected in CMake Tools.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$ROOT"

saved="$(mktemp -d)"
[[ -d build/active ]] && cp -R build/active "$saved/active"
[[ -f build/compile_commands.json ]] && cp build/compile_commands.json "$saved/"
restore() {
  rm -rf build/active
  [[ -d "$saved/active" ]] && cp -R "$saved/active" build/active
  [[ -f "$saved/compile_commands.json" ]] && cp "$saved/compile_commands.json" build/compile_commands.json
  rm -rf "$saved"
}
trap restore EXIT

echo "ubc: $("$UBC" --version)"
failed=()
for dc in configs/*_defconfig; do
  p="$(basename "$dc" _defconfig)"
  tools/build_product.sh "$p" || failed+=("$p")
done

echo "== once-per-repo checks"
check() { local name="$1"; shift; if "$@"; then :; else failed+=("$name"); fi; }
check drift "$PYTHON" tools/kconfig2variants.py --all --vscode --check
check variants "$PYTHON" tools/check_variants.py
check kconfig "$PYTHON" tools/check_kconfig.py
check bms-pin "$PYTHON" tools/pin_bms.py --check
check skills "$PYTHON" tools/check_skill_mirrors.py

if ((${#failed[@]})); then
  echo "FAILED: ${failed[*]}"; exit 1
fi
echo "all products and checks passed — output in build/site/<product>/{sphinx,ubcode}/"
