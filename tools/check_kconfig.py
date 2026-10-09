"""Kconfig hygiene of the CV feature model (K§4, K§0 P3).

Usage: check_kconfig.py

1. Every visible symbol (with a prompt, not a choice option) and every choice
   has a `help` text.
2. No `tristate`, every symbol has a namespace (`A__B`) — as the generator.
3. No build settings in the variant model: no namespace `BUILD__` / `KIT__`.
4. No dead symbols: every symbol or choice is used somewhere — as `var.*` in
   the docs / ubproject.toml, or as `CONFIG_*` in code, CMake or the Kconfig
   dependencies of another symbol.
"""
import re
import sys
from pathlib import Path

import kconfiglib

ROOT = Path(__file__).resolve().parent.parent
BUILD_NAMESPACES = ("BUILD__", "KIT__", "TOOLCHAIN__")


def text_corpus() -> str:
    parts = [(ROOT / "ubproject.toml").read_text()]
    for pattern in ("docs/**/*.rst", "src/**/*.[ch]", "tests/**/*.[ch]", "cmake/*.cmake", "**/CMakeLists.txt"):
        parts += [p.read_text() for p in ROOT.glob(pattern) if "build" not in p.parts]
    return "\n".join(parts)


def main() -> int:
    kconf = kconfiglib.Kconfig(str(ROOT / "Kconfig"), warn_to_stderr=False)
    errors: list[str] = []
    choice_syms = {s for c in kconf.unique_choices for s in c.syms}
    corpus = text_corpus()
    deps = " ".join(str(n.dep) for n in kconf.node_iter() if n.item is not kconfiglib.MENU)

    def used(name: str) -> bool:
        var = "var." + ".".join(name.lower().split("__"))
        return (var in corpus or re.search(rf"\bCONFIG_{name}(__\w+)?\b", corpus) is not None
                or re.search(rf"\b{name}(__\w+)?\b", deps) is not None)

    for c in kconf.unique_choices:
        if not any(n.help for n in c.nodes):
            errors.append(f"choice {c.name}: no help text")
        if not used(c.name):
            errors.append(f"choice {c.name}: used nowhere (dead)")
    for s in kconf.unique_defined_syms:
        if s in choice_syms:
            continue
        if s.orig_type == kconfiglib.TRISTATE:
            errors.append(f"{s.name}: tristate not allowed")
        if "__" not in s.name:
            errors.append(f"{s.name}: no namespace")
        if s.name.startswith(BUILD_NAMESPACES):
            errors.append(f"{s.name}: build settings are not variant data (K§0 P3)")
        if any(n.prompt for n in s.nodes) and not any(n.help for n in s.nodes):
            errors.append(f"{s.name}: no help text")
        if not used(s.name):
            errors.append(f"{s.name}: used nowhere (dead)")
    for e in errors:
        print(f"check_kconfig: {e}", file=sys.stderr)
    print(f"check_kconfig: {len(kconf.unique_defined_syms)} symbols, {len(kconf.unique_choices)} choices: "
          f"{'FAILED' if errors else 'ok'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
