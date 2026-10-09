"""Write the golden files of DOC-11 from the last tools/build_all.sh run.

Usage: update_golden.py   — then review the diff (plan 7 M-03); golden files
change only through a reviewed commit (T§2).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from conftest import PRODUCTS, ROOT, SITE, load_needs, local  # noqa: E402
from normalize import normalize  # noqa: E402

out = ROOT / "tools/tests/golden"
out.mkdir(exist_ok=True)
for p in PRODUCTS:
    needs = {i: normalize(n) for i, n in sorted(local(load_needs(SITE / p / "ubc.needs.json")).items())}
    (out / f"{p}.needs.json").write_text(json.dumps(needs, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    shutil.copy(ROOT / f"variants/{p}.json", out / f"{p}.variants.json")
    print(f"golden: {p}: {len(needs)} needs")
