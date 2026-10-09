"""Normalisation of needs.json exports for comparisons (DOC-10 parity, DOC-11 golden).

Known export differences that are not variant behaviour are removed:
- fields only one toolchain writes (Sphinx internals, ubc `__source__`);
- empty values: ubc omits empty links, Sphinx writes [] (plan 99 UB-06);
- `remote-url` / `local-url` have different meanings (CL-03) and contain the commit / local path;
- `doctype`, `section_name`, `sections`, `docname`, `lineno`: location details, not content;
- imported (`BMS_*`) needs: `content` (Sphinx rewrites ids in the text, SN-06) and
  `style` (Sphinx drops it, SN-07).
"""
VOLATILE = {"local-url", "remote-url", "doctype", "section_name", "sections", "docname", "lineno",
            "__source__", "runtime_s", "test_run_label"}


def norm_value(v):
    if v in (None, [], ""):
        return None
    if isinstance(v, list):
        return sorted(v)
    return v


EXTERNAL_DIFF = {"content", "style"}


def normalize(need: dict, keys=None) -> dict:
    keys = keys if keys is not None else need.keys()
    skip = VOLATILE | (EXTERNAL_DIFF if str(need.get("id", "")).startswith("BMS_") else set())
    out = {k: norm_value(need.get(k)) for k in keys if k not in skip}
    return {k: v for k, v in out.items() if v is not None}
