# Sphinx configuration of the CV platform. Everything need-related lives in the
# root ubproject.toml, shared with ubc / ubCode:
#   needs_from_toml            -> sphinx-needs  ([needs])
#   sources_from_toml          -> sphinx-mounts ([source], variant_sources)
#   src_trace_config_from_toml -> sphinx-codelinks ([codelinks])
# The active product comes from build/active/ (written at CMake configure).

project = "CV platform"
copyright = "PhilipPartsch, MIT licence"

extensions = ["sphinx_needs", "sphinx_mounts", "sphinx_codelinks"]

needs_from_toml = "../ubproject.toml"
sources_from_toml = "../ubproject.toml"
src_trace_config_from_toml = "../ubproject.toml"

needs_build_json = True

# Backward coverage (`coverage-*-back` in metamodel/schemas.json) is owed by a
# later workflow stage, so it is unmet while a stream is halfway down the V.
# sphinx-needs turns every schema severity into a Sphinx warning, and `-W`
# would fail the build. Suppress only that subtype, as the BMS does; `ubc check`
# and `ubc agent gaps` still report it.
suppress_warnings = ["sn_schema_warning.network_contains_too_few"]

exclude_patterns = ["_build"]
html_theme = "alabaster"
html_static_path = ["_static"]
