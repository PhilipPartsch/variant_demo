extensions = ["myst_parser", "sphinx_needs"]

needs_from_toml = "ubproject.toml"

# README.md is project documentation, not a needs document.
exclude_patterns = ["_build", "README.md"]

# Variant-data (`var.*`) support is on the Sphinx-Needs `master` branch but not
# in a released version yet, so a build against the released package cannot
# evaluate the `<<[var.* ...]>>` functions. Silence the expected resolution
# warnings until that release; the values already resolve correctly under `ubc`.
suppress_warnings = ["needs.dynamic_function"]
