"""Pin a BMS release for the CV platform (B§5.3), or check the pin.

Pin (needs the BMS repository and ubc):
  pin_bms.py --bms <path to rollout-demo-bms> [--ubc <ubc>]
      Exports one needs.json per chemistry from the BMS docs (ubc build needs)
      and writes third_party/bms/<version>/{nmc,lfp}.needs.json, where
      <version> is the BMS [project] version.

Check (no BMS repository needed; run by tools/build_all.sh):
  pin_bms.py --check
      The version in cmake/bms.cmake, the folder third_party/bms/<version>/,
      the `current_version` of both files and the external-needs base_url in
      ubproject.toml agree.

Processing of each export:
- derive `docname` from ubc's `__source__` path (relative to the BMS docs), so
  links to the BMS docs point at real pages (the ubc export has no docname);
- drop `__source__` and clear codelinks `local-url` (absolute local paths must
  not be published);
- tag the BMS interface needs with `interface` (until the BMS does it, B§5.2.3);
- set `status = "imported"` (exempted from the CV workflow, B§7.2).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHEMISTRIES = {"nmc": "variants/nmc.json", "lfp": "variants/lfp.json"}
INTERFACE = {
    "REQ_POWER_DERATING", "REQ_ISOLATION_FAULT", "REQ_CELL_VOLTAGE_LIMITS",
    "REQ_SOC_ACCURACY", "REQ_SOC_INVALID_FLAG", "REQ_PACK_OVERCURRENT",
    "REQ_FAULT_REACTION_TIME", "REQ_HEATING_REQUEST", "REQ_COOLING_REQUEST",
}


def cmake_version() -> str:
    m = re.search(r'set\(CV_BMS_VERSION "([^"]+)"\)', (ROOT / "cmake/bms.cmake").read_text())
    return m.group(1)


def process(data: dict, docs_root: Path) -> dict:
    needs = data["versions"][data["current_version"]]["needs"]
    missing = INTERFACE - needs.keys()
    if missing:
        raise SystemExit(f"pin_bms: interface needs missing in the BMS export: {sorted(missing)}")
    for nid, need in needs.items():
        src = need.pop("__source__", None)
        if src and src.get("path"):
            try:
                need["docname"] = Path(src["path"]).resolve().relative_to(docs_root).with_suffix("").as_posix()
            except ValueError:
                pass  # code markers outside docs/: no page of their own
        if (need.get("local-url") or "").startswith("file://"):
            need["local-url"] = ""  # codelinks link to the exporting machine
        if nid in INTERFACE:
            need["tags"] = sorted(set(need.get("tags", [])) | {"interface"})
        need["status"] = "imported"
    return data


def pin(bms: Path, ubc: str) -> int:
    docs = (bms / "docs").resolve()
    version = tomllib.loads((docs / "ubproject.toml").read_text())["project"]["version"]
    out = ROOT / "third_party/bms" / version
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for chem, vfile in CHEMISTRIES.items():
            raw = Path(tmp) / f"{chem}.json"
            subprocess.run(
                [ubc, "build", "needs", "--source-maps", "-c", f"needs.variant_data_file = '{vfile}'", "-o", str(raw)],
                cwd=docs, check=True, stdout=subprocess.DEVNULL,
            )
            data = process(json.loads(raw.read_text()), docs)
            text = json.dumps(data, indent=2, sort_keys=True) + "\n"
            if str(Path.home()) in text:
                raise SystemExit(f"pin_bms: {chem}: export still contains local paths")
            (out / f"{chem}.needs.json").write_text(text)
            print(f"pin_bms: {out.relative_to(ROOT)}/{chem}.needs.json ({len(data['versions'][data['current_version']]['needs'])} needs)")
    if version != cmake_version():
        print(f"pin_bms: now set CV_BMS_VERSION to {version} in cmake/bms.cmake and the base_url in ubproject.toml")
    return 0


def check() -> int:
    version = cmake_version()
    bad = []
    folder = ROOT / "third_party/bms" / version
    for chem in CHEMISTRIES:
        f = folder / f"{chem}.needs.json"
        if not f.exists():
            bad.append(f"{f.relative_to(ROOT)} missing")
            continue
        data = json.loads(f.read_text())
        if data["current_version"] != version:
            bad.append(f"{f.relative_to(ROOT)}: current_version {data['current_version']} != {version}")
        needs = data["versions"][data["current_version"]]["needs"]
        untagged = sorted(i for i in INTERFACE if "interface" not in needs.get(i, {}).get("tags", []))
        if untagged:
            bad.append(f"{f.relative_to(ROOT)}: interface needs not tagged: {untagged}")
        if any(n.get("status") != "imported" for n in needs.values()):
            bad.append(f"{f.relative_to(ROOT)}: needs without status 'imported'")
    others = [p.name for p in (ROOT / "third_party/bms").iterdir() if p.is_dir() and p.name != version]
    if others:
        bad.append(f"third_party/bms: unused pinned versions {others}")
    ext = tomllib.loads((ROOT / "ubproject.toml").read_text())["needs"]["external_needs"]
    if not any(f"/{version}/" in e.get("base_url", "") + "/" for e in ext):
        bad.append(f"ubproject.toml: no external_needs base_url contains /{version}/")
    for b in bad:
        print(f"pin_bms: {b}", file=sys.stderr)
    print(f"pin_bms: BMS {version}: {'FAILED' if bad else 'ok'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bms", type=Path, help="path to the BMS repository (rollout-demo-bms)")
    ap.add_argument("--ubc", default=os.environ.get("UBC", "ubc"))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return check()
    if not args.bms:
        ap.error("--bms or --check required")
    return pin(args.bms, args.ubc)


if __name__ == "__main__":
    sys.exit(main())
