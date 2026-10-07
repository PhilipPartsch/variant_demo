# ubCode Full Example

A guided tour of ubCode's main features in one project. It builds with both the
`ubc` CLI and an upstream Sphinx + Sphinx-Needs build (`ubc script sphinx`).
Build-variant data (`var.*`) resolves under ubCode today; in Sphinx it needs
Sphinx-Needs' variant support.

## What this project shows

- **Mixed RST + Markdown authoring.** Requirements live in reStructuredText
  (`index.rst`), specifications in `specifications.rst`, and tests in Markdown /
  MyST (`tests.md`). The `[parse.parsers.*]` tables in `ubproject.toml` route
  each file to the right parser; all needs are indexed together.
- **Multiple need types and links.** `req`, `spec`, and `test` types, linked
  with `implements` (spec → req) and `tests` (test → req/spec) for
  traceability.
- **Typed fields.** `[needs.fields.*]` declares fields with types and defaults.
- **Build variants ("150% model").** `variants.json` plus inline
  `[needs.variant_data]` drive `<<...>>` variant functions and `<{ var.* }>`
  variant-data references on fields that set `parse_variants = true`.
- **Reports.** A starter Jinja2 report lives under `reports/`.

## Build it

Run the configured scripts with `ubc script <name>`:

```bash
ubc script build       # index the project and report warnings
ubc script needs       # write needs.json
ubc script documents   # list source documents and their parser (rst / myst)
ubc script report      # render reports/needs_overview.html.j2
ubc script sphinx      # build HTML with Sphinx + Sphinx-Needs (needs uv)
```

## Explore further

```bash
# Query needs with a filter expression (requires an active license):
ubc query filter "type == 'spec'"

# Compare two build variants:
ubc build needs -o needs.linux.json
ubc build needs -c 'needs.variant_data.platform = "windows"' -o needs.windows.json
ubc diff --needs needs.linux.json --needs needs.windows.json
```
