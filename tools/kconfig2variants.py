"""Kconfig -> variant data generator (K§6).

Usage:
  kconfig2variants.py <Kconfig> <defconfig> <outdir>
      One product (called by CMake at configure time). Writes <outdir>/
      variants.json, autoconf.h, autoconf.cmake and .config.
  kconfig2variants.py --all [--vscode] [--check]
      Every configs/*_defconfig -> variants/<product>.json; with --vscode also
      .vscode/cmake-variants.json and the product list of .vscode/tasks.json.
      With --check nothing is written: the run
      fails if a committed file differs from what would be generated, or if
      the `product` field enum in ubproject.toml does not list every product.

Conventions (K§4): `__` nests (no level may be a Python keyword), named choices become lower-case strings,
disabled symbols are emitted with a typed "off" value (false / ""),
`meta.product` = defconfig name. Any Kconfig warning fails the run, including
an assignment kconfiglib cannot honour (unmet `depends on`).
"""

import argparse
import json
import keyword
import sys
import tomllib
from pathlib import Path

import kconfiglib

ROOT = Path(__file__).resolve().parent.parent


def nest(target: dict, name: str, value) -> None:
    parts = name.lower().split("__")
    # sphinx-needs evaluates conditions as Python: `var.hv.class` is a syntax
    # error there (ubc accepts it), so no level may be a Python keyword.
    bad = [p for p in parts if keyword.iskeyword(p)]
    if bad:
        raise SystemExit(f"kconfig2variants: {name}: {bad} is a Python keyword, unusable in var.* conditions")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def load(kconfig: Path, defconfig: Path) -> kconfiglib.Kconfig:
    kconf = kconfiglib.Kconfig(str(kconfig), warn_to_stderr=False)
    kconf.warn_assign_undef = True  # a misspelt symbol in a defconfig is an error, not ignored
    kconf.load_config(str(defconfig))
    for sym in kconf.unique_defined_syms:
        if sym.user_value is not None:
            want = sym.user_value if isinstance(sym.user_value, str) else kconfiglib.TRI_TO_STR[sym.user_value]
            if want != sym.str_value:
                kconf.warnings.append(f"{sym.name} was assigned {want!r} but got {sym.str_value!r} (unmet dependency)")
    if kconf.warnings:
        raise SystemExit("\n".join(f"kconfig2variants: {defconfig.name}: {w}" for w in kconf.warnings))
    return kconf


def variant_data(kconf: kconfiglib.Kconfig, product: str) -> dict:
    data: dict = {}
    choice_options = set()
    for choice in kconf.unique_choices:
        if not choice.name:
            raise SystemExit("kconfig2variants: choices must be named")
        sel = choice.selection
        nest(data, choice.name, sel.name[len(choice.name) + 2 :].lower() if sel else "")
        choice_options.update(s.name for s in choice.syms)
    for sym in kconf.unique_defined_syms:
        if sym.name in choice_options:
            continue
        if "__" not in sym.name:
            raise SystemExit(f"kconfig2variants: symbol without namespace: {sym.name}")
        if sym.orig_type == kconfiglib.TRISTATE:  # `type` reports bool without `modules`
            raise SystemExit(f"kconfig2variants: tristate not allowed: {sym.name}")
        if sym.type == kconfiglib.BOOL:
            value = sym.str_value == "y"
        elif sym.type in (kconfiglib.INT, kconfiglib.HEX):
            value = int(sym.str_value or "0", 0)
        else:
            value = sym.str_value
        nest(data, sym.name, value)
    nest(data, "META__PRODUCT", product)
    return data


def to_json(data) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def autoconf_cmake(kconf: kconfiglib.Kconfig) -> str:
    lines = []
    for sym in kconf.unique_defined_syms:
        v = sym.str_value
        if sym.type == kconfiglib.BOOL:
            v = "ON" if v == "y" else "OFF"
        lines.append(f'set(CONFIG_{sym.name} "{v}")')
    return "\n".join(lines) + "\n"


def write(path: Path, text: str) -> None:
    """Write only when the content changes (keeps timestamps for CMake / IDE)."""
    if not path.exists() or path.read_text() != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def product_of(defconfig: Path) -> str:
    return defconfig.name.removesuffix("_defconfig")


def one(kconfig: Path, defconfig: Path, outdir: Path) -> int:
    kconf = load(kconfig, defconfig)
    data = variant_data(kconf, product_of(defconfig))
    write(outdir / "variants.json", to_json(data))
    outdir.mkdir(parents=True, exist_ok=True)
    kconf.write_config(str(outdir / ".config"))
    kconf.write_autoconf(str(outdir / "autoconf.h"))
    write(outdir / "autoconf.cmake", autoconf_cmake(kconf))
    return 0


def describe(d: dict) -> str:
    """Human-readable label for the CMake Tools variant picker."""
    parts = [d["vehicle"]["type"].capitalize(), d["powertrain"]["type"].upper() if d["powertrain"]["type"] == "bev" else "diesel"]
    if d["bms"]["enabled"]:
        parts.append(d["bms"]["chemistry"].upper())
        parts.append(d["hv"]["voltage"].removeprefix("v") + " V")
    if d["charging"]["mcs"]:
        parts.append("MCS")
    if d["charging"]["pantograph"]:
        parts.append("pantograph")
    parts.append(d["market"]["region"].upper())
    return ", ".join(parts)


def all_products(vscode: bool, check: bool) -> int:
    kconfig = ROOT / "Kconfig"
    defconfigs = sorted((ROOT / "configs").glob("*_defconfig"))
    expected: dict[Path, str] = {}
    datas = {}
    for dc in defconfigs:
        data = variant_data(load(kconfig, dc), product_of(dc))
        datas[product_of(dc)] = data
        expected[ROOT / "variants" / f"{product_of(dc)}.json"] = to_json(data)
    if vscode:
        default = "truck_bev_nmc_eu" if "truck_bev_nmc_eu" in datas else next(iter(datas))
        choices = {
            p: {"short": p, "long": describe(d), "settings": {"VARIANT": p}} for p, d in datas.items()
        }
        expected[ROOT / ".vscode" / "cmake-variants.json"] = to_json(
            {"variant": {"default": default, "description": "Product (configs/<product>_defconfig)", "choices": choices}}
        )
        tasks_path = ROOT / ".vscode" / "tasks.json"
        tasks = json.loads(tasks_path.read_text())
        for inp in tasks.get("inputs", []):
            if inp.get("id") == "product":
                inp["options"] = list(datas)
        expected[tasks_path] = json.dumps(tasks, indent=2) + "\n"
    stale = sorted(set((ROOT / "variants").glob("*.json")) - set(expected))
    if not check:
        for path, text in expected.items():
            write(path, text)
        for path in stale:
            path.unlink()
        print(f"kconfig2variants: {len(datas)} products written")
        return 0
    bad = [str(p.relative_to(ROOT)) for p, t in expected.items() if not p.exists() or p.read_text() != t]
    bad += [f"{p.relative_to(ROOT)} (no defconfig)" for p in stale]
    toml = tomllib.loads((ROOT / "ubproject.toml").read_text())
    enum = toml["needs"]["fields"]["product"]["schema"]["enum"]
    if sorted(x for x in enum if x) != sorted(datas):
        bad.append(f"ubproject.toml [needs.fields.product] enum {enum} != products {sorted(datas)}")
    for b in bad:
        print(f"kconfig2variants: out of date: {b}", file=sys.stderr)
    if bad:
        print("kconfig2variants: run `tools/kconfig2variants.py --all --vscode` and commit", file=sys.stderr)
        return 1
    print(f"kconfig2variants: {len(datas)} products up to date")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="every configs/*_defconfig -> variants/")
    ap.add_argument("--vscode", action="store_true", help="also .vscode/cmake-variants.json")
    ap.add_argument("--check", action="store_true", help="fail on drift, write nothing")
    ap.add_argument("files", nargs="*", metavar="<Kconfig> <defconfig> <outdir>")
    args = ap.parse_args()
    if args.all:
        return all_products(args.vscode, args.check)
    if len(args.files) != 3:
        ap.error("expected <Kconfig> <defconfig> <outdir> or --all")
    return one(*(Path(f) for f in args.files))


if __name__ == "__main__":
    sys.exit(main())
