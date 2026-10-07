extensions = ["myst_parser", "sphinx_needs"]

needs_from_toml = "ubproject.toml"

import tomllib
from pathlib import Path

_ub = tomllib.loads(Path(__file__).with_name("ubproject.toml").read_text())
exclude_patterns = [*_ub.get("source", {}).get("extend_exclude", [])]


# Variant-data (`var.*`) support is on the Sphinx-Needs `master` branch but not
# in a released version yet, so a build against the released package cannot
# evaluate the `<<[var.* ...]>>` functions. Silence the expected resolution
# warnings until that release; the values already resolve correctly under `ubc`.
suppress_warnings = ["needs.dynamic_function"]
