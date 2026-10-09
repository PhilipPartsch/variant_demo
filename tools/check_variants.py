"""Cross-product consistency checks of the variant model (M§8, M§9).

Usage: check_variants.py [--needs-dir build/site]

1. Condition registry: every `var.*` key used in a condition (named variants,
   `variant_sources` / mount `if`, `.. if::` blocks, `<<[...]: ...>>` variant
   functions) exists in the generated variant data of every product; no
   `var.build.*` keys (build settings are not variant data, K§0 P3).
2. No bare booleans: a boolean key is compared explicitly (`== True`).
3. Branch coverage: every condition is true in at least one product and false
   in at least one (M§0.4).
4. Code conditions: every `CONFIG_*` used in `#if` in src/ and tests/ is a
   Kconfig symbol (or choice option).
5. Alternatives complete (M§8 rule 5): a need ID defined more than once in the
   sources (complementary `if` blocks, `#if` / `#else` markers) exists in the
   needs.json of every product that contains the defining file. Needs the
   per-product exports `<needs-dir>/<product>/ubc.needs.json`; skipped for
   products not built yet.
"""

import argparse
import fnmatch
import json
import re
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import kconfiglib

ROOT = Path(__file__).resolve().parent.parent
VAR_KEY = re.compile(r"\bvar((?:\.[a-z_][a-z0-9_]*)+)")
ID_OPT = re.compile(r"^\s*:id:\s*(\S+)", re.M)
IF_DIRECTIVE = re.compile(r"^\s*\.\.\s+if::\s*(.+)$", re.M)
INLINE_COND = re.compile(r"<<\[([^\]]+)\]")
MARKER = re.compile(r"//\s*@need:\s*[^,]*,\s*([A-Z]+_[A-Z][A-Z0-9_]*)")
CODE_IF = re.compile(r"^\s*#\s*(?:el)?if\b(.*)$", re.M)
CONFIG = re.compile(r"\bCONFIG_([A-Z0-9_]+)")
INLINE_LITERAL = re.compile(r"``.+?``", re.S)


def ns(obj):
    return SimpleNamespace(**{k: ns(v) for k, v in obj.items()}) if isinstance(obj, dict) else obj


def lookup(data: dict, dotted: str):
    cur = data
    for part in dotted.strip(".").split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--needs-dir", type=Path, default=ROOT / "build/site")
    args = ap.parse_args()

    cfg = tomllib.loads((ROOT / "ubproject.toml").read_text())
    products = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "variants").glob("*.json"))}
    named = cfg.get("needs", {}).get("variants", {})
    docs_dir = ROOT / cfg.get("source", {}).get("dir", ".")
    errors: list[str] = []

    # --- collect conditions ------------------------------------------------------
    conditions: list[tuple[str, str]] = [(f"[needs.variants] {k}", v) for k, v in named.items()]
    rules = cfg.get("source", {}).get("variant_sources", [])
    conditions += [(f"variant_sources {r['files']}", r["if"]) for r in rules]
    conditions += [(f"mount {m.get('path', m)}", m["if"]) for m in cfg.get("source", {}).get("mounts", []) if "if" in m]
    rst_files = sorted(docs_dir.rglob("*.rst"))
    for f in rst_files:
        text = INLINE_LITERAL.sub("", f.read_text())  # ``<<[cond]: a, b>>`` in prose is an example, not a condition
        rel = f.relative_to(ROOT)
        conditions += [(f"{rel} .. if::", c.strip()) for c in IF_DIRECTIVE.findall(text)]
        conditions += [(f"{rel} <<[...]>>", c.strip()) for c in INLINE_COND.findall(text)]

    def resolve(cond: str) -> str:
        """Expand a bare named variant (`.. if:: bev`) to its condition."""
        return f"({named[cond]})" if cond in named else cond

    # --- 1-3: registry, bare booleans, branch coverage ---------------------------------
    for where, cond in conditions:
        expr = resolve(cond)
        for m in VAR_KEY.finditer(expr):
            key = m.group(1)
            if key.startswith(".build."):
                errors.append(f"{where}: build settings are not variant data: var{key}")
            for prod, data in products.items():
                try:
                    value = lookup(data, key)
                except KeyError:
                    errors.append(f"{where}: unknown key var{key} (product {prod})")
                    break
                if isinstance(value, bool) and not re.match(r"\s*(==|!=)", expr[m.end():]):
                    errors.append(f"{where}: bare boolean var{key}: compare explicitly (== True)")
                    break
        results = {}
        for prod, data in products.items():
            try:
                results[prod] = bool(eval(expr, {"__builtins__": {}}, {"var": ns(data), "True": True, "False": False}))
            except Exception as exc:  # noqa: BLE001 - report any unevaluable condition
                errors.append(f"{where}: cannot evaluate {cond!r}: {exc}")
                break
        else:
            if len(set(results.values())) < 2:
                errors.append(f"{where}: {cond!r} is {next(iter(results.values()))} in every product (no branch coverage)")

    # --- 4: CONFIG_* in code are Kconfig symbols ---------------------------------------
    kconf = kconfiglib.Kconfig(str(ROOT / "Kconfig"), warn_to_stderr=False)
    known = {s.name for s in kconf.unique_defined_syms}
    code_files = sorted(p for d in ("src", "tests") for p in (ROOT / d).rglob("*") if p.suffix in (".c", ".h"))
    for f in code_files:
        for line in CODE_IF.findall(f.read_text()):
            for sym in CONFIG.findall(line):
                if sym not in known:
                    errors.append(f"{f.relative_to(ROOT)}: CONFIG_{sym} is not a Kconfig symbol")

    # --- 5: alternatives complete ------------------------------------------------------
    defined: dict[str, list[Path]] = {}
    for f in rst_files:
        for nid in ID_OPT.findall(f.read_text()):
            defined.setdefault(nid, []).append(f)
    for f in code_files:
        for nid in MARKER.findall(f.read_text()):
            defined.setdefault(nid, []).append(f)
    shared = {nid: files for nid, files in defined.items() if len(files) > 1}

    def contains(prod: str, f: Path) -> bool:
        if f.suffix == ".rst":
            rel = f.relative_to(docs_dir).as_posix()
            data = ns(products[prod])
            for rule in rules:
                if any(fnmatch.fnmatch(rel, g) for g in rule["files"]):
                    if not eval(rule["if"], {"__builtins__": {}}, {"var": data, "True": True, "False": False}):
                        return False
            return True
        db = ROOT / "build/cmake" / prod / "compile_commands.json"
        return db.exists() and any(Path(e["file"]).resolve() == f.resolve() for e in json.loads(db.read_text()))

    checked = 0
    for prod in products:
        export = args.needs_dir / prod / "ubc.needs.json"
        if not export.exists():
            continue
        checked += 1
        d = json.loads(export.read_text())
        needs = d["versions"][d.get("current_version") or next(iter(d["versions"]))]["needs"]
        for nid, files in shared.items():
            if nid not in needs and any(contains(prod, f) for f in set(files)):
                errors.append(f"{prod}: alternative {nid} missing (defined in {sorted({str(f.relative_to(ROOT)) for f in files})})")

    for e in errors:
        print(f"check_variants: {e}", file=sys.stderr)
    print(f"check_variants: {len(conditions)} conditions, {len(products)} products, "
          f"{len(shared)} shared ids ({checked} product exports): {'FAILED' if errors else 'ok'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
