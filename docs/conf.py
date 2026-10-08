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

exclude_patterns = ["_build"]
html_theme = "alabaster"
html_static_path = ["_static"]
