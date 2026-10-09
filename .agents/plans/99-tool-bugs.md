# Plan 99: Bugs and gaps in the useblocks tools

Collected while building the CV platform (plans 1–4). Only **useblocks tools**;
Sphinx, kconfiglib, CMake / CMake Tools and libclang are out of scope. Kept up
to date by every later plan — add new entries at the end of the tool's section.

Each entry: summary, **marker** (`branch@commit` + file:line where it can be
reproduced in this repository), input, wrong output (and what was expected),
the workaround used here, and two alternative solutions.

Markers point only to pushed branches: `main` and `content/cv-platform`
(`eval/*` branches stay local by rule; findings first seen there are
reproduced on a pushed commit).

## 1. useblocks tools

Checked on [useblocks.com](https://useblocks.com) and the
[useblocks reference list](https://x-as-code.useblocks.com/reference/index.html), 2026-10-09.

| Tool | Kind | Version here | Used | Section |
|---|---|---|---|---|
| ubCode (VS Code extension) + `ubc` CLI | commercial | 0.35.0 | yes | §3 |
| Pharaoh (agentic engineering, `ubc agent`, `.pharaoh/`) | commercial | in ubc 0.35.0 | yes | §4 |
| Sphinx-Needs | open source | 8.5.0 | yes | §5 |
| Sphinx-Codelinks ("Codelinks") | open source | 1.4.0 | yes | §6 |
| sphinx-mounts (not on the website list; package by "team useblocks", `github.com/useblocks/sphinx-mounts`) | open source | 0.2.0 | yes | §7 |
| useblocks/ubc-action | GitHub Action | — | planned (plan 6) | §8 |
| Sphinx-Data-Viewer | open source | 0.1.5 | indirectly (sphinx-needs dependency) | no findings |
| ubTrace | commercial | — | no | — |
| ubConnect | commercial | — | no | — |
| Sphinx-Test-Reports | open source | — | no (candidate to replace `tools/import_test_results.py`) | — |
| Sphinx-Modeling, Sphinx-Collections, Sphinx-Preview, Sphinx-SimplePDF, Sphinx-EMF, Bazel-Drives-Sphinx, libpdf | open source | — | no | — |

## 2. Overview

Severity: **high** = wrong result without notice or blocks a use case;
**medium** = wrong or inconsistent, workaround exists; **low** = cosmetic,
documentation, convenience.

| ID | Tool | Severity | Summary |
|---|---|---|---|
| UB-01 | ubc | medium | export has no `docname`, but absolute local paths (`__source__`, codelinks `local-url`) |
| UB-02 | ubc | high | one `null` in a declared non-nullable field drops the whole external-needs source |
| UB-03 | ubc | medium | Python keyword in a `var.*` key accepted; Sphinx cannot evaluate it |
| UB-04 | ubc | medium | `[variants] data_file` is silently ignored |
| UB-05 | ubc | medium | `-c` override of a nested table replaces the whole table |
| UB-06 | ubc | low | empty link lists omitted from `needs.json` (Sphinx writes `[]`) |
| UB-07 | ubc | medium | backlinks on external needs not filled (`allocated_from`) |
| UB-08 | ubc | low | `needs.builder_filter` ignored |
| UB-09 | ubc | medium | `:variant:` role text stays unresolved in the exported `content` |
| UB-10 | ubc | low | info `variant_sources_sphinx_unsupported` is outdated / misleading |
| UB-11 | ubCode | low | Needs Index lags behind a variant switch |
| UB-12 | ubc + Sphinx-Needs | medium | `if` does not resolve named variants (`[needs.variants]`) |
| UB-13 | ubc + Sphinx-Needs | medium | imported needs of an undeclared type dropped, undeclared fields stripped, silently |
| PH-01 | Pharaoh | **high** | verdicts stored per need id only: alternatives with one id overwrite each other |
| PH-02 | Pharaoh | **high** | review fingerprint ignores resolved field values and link variants |
| PH-03 | Pharaoh | medium | fingerprint follows parents one level only (children / decisions flip, grandchildren not) |
| PH-04 | Pharaoh | medium | backward trace of two stages with the same link + target is attributed to one stage |
| PH-05 | Pharaoh | medium | workflow traces apply per need type; no per-stage filter |
| PH-06 | Pharaoh | medium | `agent status` / `next` count imported (`exempt_status`) needs as stage output |
| PH-07 | Pharaoh | low | `review-brief` lists imported (`exempt_status`) needs as review targets |
| PH-08 | Pharaoh | low | `agent audit` omits `value`, `tags` and `refines` / `allocates` in `trace` |
| PH-09 | Pharaoh | low | `doctor` checks only the `.claude` copy of project skills |
| PH-10 | Pharaoh | low | brief / skills: `submit_command` without `-p`, `stale` bucket undocumented |
| SN-01 | Sphinx-Needs | medium | every schema severity is a Sphinx warning; `-W` fails on `warning` rules |
| SN-02 | Sphinx-Needs | medium | `needs_from_toml` overrides `needs_external_needs` from `conf.py` |
| SN-03 | Sphinx-Needs | low | `needs.json` drops external needs by default (`builder_filter`), unlike ubc |
| SN-04 | Sphinx-Needs | low | duplicate need id raises an exception (traceback) instead of a located warning |
| SN-05 | Sphinx-Needs | low | schema `contains` on a list field rejected without `items` (ubc accepts) |
| CL-01 | Sphinx-Codelinks | medium | fails in a git worktree ("git root is not found") |
| CL-02 | Sphinx-Codelinks | medium | `.c` file without compile-database entry silently skipped |
| CL-03 | Sphinx-Codelinks + ubc | low | `remote-url` / `local-url` differ between Sphinx and ubc |
| CL-04 | Sphinx-Codelinks | low | source pages reference `_static/_static/…` (CSS 404) |
| SM-01 | sphinx-mounts + ubc | medium | bare boolean condition: sphinx-mounts aborts the build, ubc warns and drops the rule |
| UA-01 | ubc-action | low | Linux runners only |

## 3. ubc / ubCode

### UB-01 Export without `docname`, with absolute local paths

- **Tool:** ubc 0.35.0 (`ubc build needs --source-maps`)
- **Marker:** `main@e744d72` `tools/pin_bms.py:54-61` (workaround); input
  from `rollout-demo-bms@38c9f30` (`docs/`).
- **Summary:** the needs export has no `docname`; instead every need carries a
  `__source__` block and codelinks needs a `local-url`, both with absolute
  paths of the exporting machine.
- **Input:** `cd rollout-demo-bms/docs && ubc build needs --source-maps -o nmc.json`
- **Wrong output:**
  ```json
  "REQ_CELL_VOLTAGE_LIMITS": { "__source__": {"path": "/Users/<user>/…/docs/specs/cell-protection/requirements.rst", …} }
  "IMPL_CHARGE_INTEGRATION": { "local-url": "file:///Users/<user>/…/src/state_estimation/coulomb_counter.py#L30" }
  ```
  Expected: `"docname": "specs/cell-protection/requirements"` (as sphinx-needs
  writes it); no local paths in an artifact meant to be shared. Consumers using
  `needs_external_needs` link to `__error__.html` without `docname`.
- **Workaround:** `tools/pin_bms.py` derives `docname`, drops `__source__`, clears `local-url`.
- **Solution A:** write `docname` (and relative `lineno`) like sphinx-needs; keep
  `__source__` only with an explicit `--source-maps`, with paths relative to the project root.
- **Solution B:** an export option `--portable` (default for `ubc build needs`)
  that strips machine-specific fields and makes paths relative.

### UB-02 One `null` value drops the whole external-needs source

- **Tool:** ubc 0.35.0
- **Marker:** `main@e744d72` `ubproject.toml:312` (`[needs.fields.code_url]`,
  workaround) with `third_party/bms/0.1.0/nmc.needs.json`.
- **Summary:** a declared field with `nullable = false` and an imported need
  whose value is `null` makes ubc reject **all** needs of the source.
- **Input:**
  ```toml
  [needs.fields.code_url]
  default = ""
  nullable = false
  ```
  plus `[[needs.external_needs]] json_path = "build/active/bms.needs.json"` (205 needs, `needs_schema` with `code_url.default = null`).
- **Wrong output:**
  `warning[needs.external] root['versions']['0.1.0']['needs_schema']['properties']['code_url']['default'] could not be read: Value cannot be converted to string: null; the source contributed no needs` → 0 of 205 needs.
  Expected: per-need diagnostic, value replaced by the default (or the one need skipped); the other needs imported.
- **Workaround:** `code_url` declared without `nullable = false`.
- **Solution A:** coerce `null` to the field default for external needs and report one `info` per field.
- **Solution B:** validate per need: skip / report only the offending need, never the whole source.

### UB-03 Python keyword in a `var.*` key accepted

- **Tool:** ubc 0.35.0 (vs Sphinx-Needs 8.5.0)
- **Marker:** `main@0c27fc5` `Kconfig:50` (`choice HV__CLASS` → `var.hv.class`, renamed in
  `07806d7`); use `var.hv.class` in any field variant, e.g. in
  `content/cv-platform@25b77bd` `docs/vehicle/requirements.rst:65`.
- **Summary:** ubc evaluates `var.hv.class`; sphinx-needs evaluates conditions as
  Python, where `class` is a keyword → syntax error. The two tools disagree silently.
- **Input:** `:value: <<[var.hv.class == "v800"]: 800, 400>>` with `{"hv": {"class": "v800"}}`
- **Wrong output:** ubc: `800` (no warning). Sphinx: `WARNING: Error while resolving dynamic values for field 'value' … invalid syntax [needs.dynamic_function]`.
  Expected: the same result in both, or the same diagnostic.
- **Workaround:** symbol renamed (`HV__VOLTAGE`, fix `07806d7`); the generator rejects keywords.
- **Solution A:** ubc warns on Python keywords (and other non-identifiers) in `var.*` paths, matching the Sphinx grammar.
- **Solution B:** both tools accept item access (`var.hv["class"]`) and document it as the escape for such keys.

### UB-04 `[variants] data_file` silently ignored

- **Tool:** ubc 0.35.0 (also the ubCode extension and Sphinx-Needs)
- **Marker:** `main@e744d72` `ubproject.toml:37` — replace `[needs] variant_data_file` by the `[variants]` form below.
- **Summary:** a `[variants]` table with `data_file` (seen in docs/examples) is
  read by none of the tools; all `if` / `:variant:` / `variant_sources` rules lose their data without a config error.
- **Input:**
  ```toml
  [variants]
  data_file = "build/active/variants.json"
  ```
- **Wrong output:** no config diagnostic; `'variant' role used but no variant data is available: 'meta.product'`; `if` blocks evaluate as unknown.
  Expected: either the key works, or `unknown key [variants]` / "use `[needs] variant_data_file`".
- **Workaround:** `[needs] variant_data_file` only.
- **Solution A:** report unknown top-level / table keys of `ubproject.toml` against the published schema.
- **Solution B:** accept `[variants] data_file` as an alias of `[needs] variant_data_file` in all three tools.

### UB-05 `-c` override replaces the whole nested table

- **Tool:** ubc 0.35.0
- **Marker:** `main@e744d72` `ubproject.toml:326` (`[codelinks.projects.vcu]`).
- **Summary:** overriding one nested key with `-c` replaces the complete table,
  so all sibling keys of the project disappear.
- **Input:** `ubc check -c "codelinks.projects.vcu.analyse.preprocessor.compile_commands = 'build/cmake/truck_diesel_eu/compile_commands.json'"`
- **Wrong output:** the `vcu` project loses `source_discover`, `oneline_comment_style`, … → no code needs.
  Expected: deep merge — only `compile_commands` changes.
- **Workaround:** gates run after configuring the product (active copies), no `-c` for codelinks.
- **Solution A:** deep-merge dotted-key overrides into the loaded config.
- **Solution B:** a separate `--set key=value` (merge) next to `-c <toml>` (replace), clearly documented.

### UB-06 Empty link lists omitted from `needs.json`

- **Tool:** ubc 0.35.0 (vs Sphinx-Needs 8.5.0)
- **Marker:** `content/cv-platform@25b77bd` `docs/subsystems/vcu/architecture.rst:21` (`ARCH_VCU_POWER_MGMT`), product `truck_diesel_eu`.
- **Summary:** a link field without targets (also after a link variant resolved to nothing) is missing in ubc's export; Sphinx writes `[]`.
- **Input:** `:allocates: <<bev: BMS_REQ_POWER_DERATING>>` in a diesel product.
- **Wrong output:** ubc: key `allocates` absent; Sphinx: `"allocates": []`. Same for `refines: []` etc.
- **Workaround:** comparisons treat absent = `[]` (`tools/eval_expect.py`).
- **Solution A:** ubc writes every declared link with `[]` (as Sphinx).
- **Solution B:** both tools honour one `needs_json_remove_defaults`-style switch and document the format.

### UB-07 Backlinks on external needs not filled

- **Tool:** ubc 0.35.0 (Sphinx-Needs fills them)
- **Marker:** `content/cv-platform@25b77bd` `docs/subsystems/bms/integration.rst` (column `allocated_from`), any BEV product.
- **Summary:** CV needs `allocates` imported `BMS_REQ_*` needs; Sphinx shows the incoming `allocated_from` on the external need, ubc leaves it empty.
- **Input:** `BB_POWER_LIMITS` with `:allocates: BMS_REQ_POWER_DERATING`; needtable column `allocated_from`.
- **Wrong output:** ubCode HTML / ubc `needs.json`: `BMS_REQ_POWER_DERATING.allocated_from` empty. Sphinx: `['BB_POWER_LIMITS', 'ARCH_VCU_POWER_MGMT']`.
- **Workaround:** the BMS usage report relies on the Sphinx output.
- **Solution A:** compute backlinks for external needs like for local ones.
- **Solution B:** if intentional, document it and offer a filter (`allocated_from` via a query function) usable in needtables.

### UB-08 `needs.builder_filter` ignored

- **Tool:** ubc 0.35.0
- **Marker:** `main@e744d72` `ubproject.toml` (`builder_filter = ""` in `[needs]`).
- **Summary:** ubc always exports all needs including external ones; the sphinx-needs option `builder_filter` has no effect.
- **Input:** `ubc build needs -c 'needs.builder_filter = "is_external==False"'`
- **Wrong output:** 205 needs (all external) exported. Expected: 0 (as Sphinx).
- **Workaround:** `builder_filter = ""` so that Sphinx matches ubc (SN-03).
- **Solution A:** honour `builder_filter` in `ubc build needs`.
- **Solution B:** report it as unsupported (`info`) so the difference is visible.

### UB-09 `:variant:` role text unresolved in the exported `content`

- **Tool:** ubc 0.35.0 (`ubc build needs`, also `agent audit` bodies)
- **Marker:** `main@e744d72` `third_party/bms/0.1.0/nmc.needs.json` (`REQ_CELL_VOLTAGE_LIMITS.content`).
- **Summary:** text using the `:variant:` role is exported raw; only fields are resolved. A consumer of the export cannot see the per-variant values.
- **Input:** BMS `REQ_CELL_VOLTAGE_LIMITS`: ``… below :variant:`pack.cell_v_min` …`` exported for `variants/nmc.json`.
- **Wrong output:** `"content": "… below :variant:`pack.cell_v_min` …"`. Expected: the value of `pack.cell_v_min` from `variants/nmc.json` (resolved for the exported variant), or a separate resolved field.
- **Workaround:** none; values must be exposed as fields by the producing project.
- **Solution A:** resolve roles in `content` when exporting a concrete variant (option `--resolve-variants`).
- **Solution B:** export `content` raw plus `content_resolved`.

### UB-10 Outdated info `variant_sources_sphinx_unsupported`

- **Tool:** ubc 0.35.0
- **Marker:** `main@e744d72`, any `ubc check`.
- **Summary:** every check prints that Sphinx does not honour `variant_sources` and that `sphinx-build -W` should not be run — sphinx-mounts 0.2.0 does honour them, and `-W` passes.
- **Input:** `[[source.variant_sources]]` rules, `sources_from_toml` in `conf.py`.
- **Wrong output:** `info[config.variant_sources_sphinx_unsupported] … do not run sphinx-build -W on this project`.
- **Workaround:** ignored.
- **Solution A:** detect `sphinx_mounts` (version) in `conf.py` and drop the info.
- **Solution B:** word it as "requires sphinx-mounts ≥ 0.2.0" and show it once (`ubc check --explain`), not on every run.

### UB-11 Needs Index lags behind a variant switch

- **Tool:** ubCode extension 0.35.0
- **Marker:** `content/cv-platform@25b77bd` `src/vcu/energy_display.c:8/17` (first seen in plan 1, E-R E3).
- **Summary:** after a CMake Tools variant switch the `code_trace.rst` preview shows the new product's code needs at once, the Needs Index still the old ones.
- **Input:** switch `truck_bev_nmc_eu` → `truck_diesel_eu` (new `build/compile_commands.json`, `build/active/*`).
- **Wrong output:** Needs Index: `IMPL_VCU_ENERGY_DISPLAY` still at line 8 (SoC). Expected: line 17 (fuel) as in the preview.
- **Workaround:** run **CMake: Configure** once more.
- **Solution A:** watch the `compile_commands` file(s) of every codelinks project and re-analyse on change.
- **Solution B:** a command "ubCode: Re-index" plus re-index on `variant_data_file` change.

### UB-12 `if` does not resolve named variants

- **Tool:** ubc 0.35.0 and Sphinx-Needs 8.5.0
- **Marker:** `content/cv-platform@25b77bd` `ubproject.toml` (`[needs.variants]` with `mcs`), `docs/vehicle/requirements.rst` (`.. if::` blocks).
- **Summary:** named variants work in `<<mcs: a, b>>` but not in `.. if:: mcs`; the same name means two things.
- **Input:** `[needs.variants] mcs = "var.charging.mcs == True"` and `.. if:: mcs`
- **Wrong output:** `warning[if.invalid_expression] 'if' directive expression could not be evaluated: 'mcs' — Unknown variant key: var.mcs`. Expected: the named condition.
- **Workaround:** spelled-out conditions in every `if`.
- **Solution A:** resolve bare names in `if` (and `variant_sources` / mount `if`) against `[needs.variants]` first.
- **Solution B:** explicit syntax, e.g. `.. if:: variant('mcs')`, in both tools.

### UB-13 Imported needs of undeclared types / fields silently lost

- **Tool:** ubc 0.35.0 and Sphinx-Needs 8.5.0
- **Marker:** `main@e744d72` `ubproject.toml:132` — remove the `test_result` type.
- **Summary:** external needs whose type is not declared are dropped, undeclared fields stripped, without a diagnostic.
- **Input:** BMS export with 52 `test_result` needs; CV without `[[needs.types]] directive = "test_result"`.
- **Wrong output:** 153 of 205 needs; `chemistry` missing when undeclared; no warning. Expected: one warning per dropped type / stripped field.
- **Workaround:** the CV metamodel declares the full BMS vocabulary.
- **Solution A:** warn per external source with counts of dropped needs / stripped fields.
- **Solution B:** keep unknown types / fields read-only (as "external type") instead of dropping them.

## 4. Pharaoh (`ubc agent`)

### PH-01 Verdicts stored per need id only

- **Tool:** ubc 0.35.0 (`agent verdict-submit`, `verdict-check`)
- **Marker:** `content/cv-platform@25b77bd` `docs/vehicle/requirements.rst:16` and `:27`
  (`REQ_ENERGY_SOURCE`, two complementary `if` blocks), `.pharaoh/verdicts/REQ_ENERGY_SOURCE.json`.
- **Summary:** `.pharaoh/verdicts/<ID>.json` holds one verdict; alternatives with
  the same id (one per product) overwrite each other, so `verdict-check` can
  never be green in all products.
- **Input:** review `REQ_ENERGY_SOURCE` under `truck_bev_nmc_eu` (state of
  charge), then under `truck_diesel_eu` (fuel level).
- **Wrong output:** after both submits: diesel `ok: true`; every BEV product `outdated: [REQ_ENERGY_SOURCE]`, `ok: false`. Re-reviewing BEV flips diesel. Now 8 outdated in N / B, 2 in A.
  Expected: both variants keep their verdict.
- **Workaround:** none; gaps imported honestly (`docs/_global/gaps.rst`).
- **Solution A:** key verdicts by id + reviewed fingerprint (several verdicts per file, `verdict-check` picks the one matching the current fingerprint).
- **Solution B:** key by id + variant (e.g. hash of the active variant data or `meta.product`), `<ID>@<variant>.json`.

### PH-02 Review fingerprint ignores resolved values and link variants

- **Tool:** ubc 0.35.0
- **Marker:** `content/cv-platform@25b77bd` `docs/vehicle/requirements.rst:65`
  (`:value: <<mcs: 1000 kW, 350 kW>>`), `docs/subsystems/vcu/architecture.rst:21`
  (`:allocates: <<bev: BMS_REQ_POWER_DERATING>>`).
- **Summary:** the fingerprint covers the raw source, not the per-product
  resolved `value` or links — a verdict judged on 1000 kW counts as fresh for 350 kW.
- **Input:** review `REQ_MAX_CHARGE_POWER` under `truck_bev_nmc_eu` (1000 kW), brief under `bus_bev_lfp_eu` (350 kW).
- **Wrong output:** bus brief lists it in `fresh_skipped` (same fingerprint `e70c…`). Same for `ARCH_VCU_POWER_MGMT` (link gone in diesel) and `BB_*` (allocated BMS content differs NMC / LFP).
  Expected: re-review when the reviewed content differs.
- **Workaround:** none.
- **Solution A:** fingerprint the resolved need (fields after variant functions, links after link variants) — together with PH-01 A.
- **Solution B:** fingerprint raw source + the values of all `var.*` keys the need references.

### PH-03 Fingerprint follows parents only one level

- **Tool:** ubc 0.35.0
- **Marker:** `content/cv-platform@25b77bd` `docs/subsystems/vcu/architecture.rst`
  (`ARCH_VCU_ENERGY_DISPLAY`), `docs/_global/decisions.rst:34` (`:affects: ARCH_CHG_INLET`),
  `docs/subsystems/vcu/software_requirements.rst` (`SWREQ_VCU_ENERGY_DISPLAY`).
- **Summary:** a need's fingerprint includes its direct parent, so a
  single-definition child of an alternative flips between products; one level
  further down it does not. Inconsistent and amplifies PH-01.
- **Input:** `ARCH_VCU_ENERGY_DISPLAY` (one definition) satisfies `REQ_ENERGY_SOURCE` (alternative).
- **Wrong output:** `ARCH_VCU_ENERGY_DISPLAY` fingerprint `f4db…` (BEV) vs `517e…` (diesel) → outdated after each product; `DEC_CHARGING_INLET_PRIORITY` flips with `ARCH_CHG_INLET`; `SWREQ_VCU_ENERGY_DISPLAY` (grandchild) does not.
  Expected: a documented, consistent rule.
- **Workaround:** none.
- **Solution A:** fingerprint only the need itself; signal parent changes separately (`parent_changed`).
- **Solution B:** include the full upstream chain, consistently, and combine with PH-01 so variants do not collide.

### PH-04 Backward trace attributed to one of two stages

- **Tool:** ubc 0.35.0 (`agent gaps`)
- **Marker:** `main@c10bbd7` `ubproject.toml` (stage `bms_allocation`, `satisfies` trace `direction = "both"`, fixed in `9abdd2c`) with the content of `content/cv-platform@25b77bd`.
- **Summary:** stages `archs` (`arch` satisfies `req`, both) and `bms_allocation`
  (`bms_block` satisfies `req`, both) share link + target; the backward
  obligation of every req is attributed to `bms_allocation` only.
- **Input:** `REQ_DOOR_DRIVE_INTERLOCK` satisfied by `ARCH_VCU_DOOR_INTERLOCK` (arch), no `bms_block`.
- **Wrong output:** `{'id': 'REQ_DOOR_DRIVE_INTERLOCK', 'link': 'satisfies', 'have': 0, 'need': 1, 'category': 'trace_backward'}` — the arch link is not counted. Expected: `have: 1` (arch stage satisfied), or one obligation per stage reported separately.
- **Workaround:** `bms_allocation` trace `direction = "outgoing"`.
- **Solution A:** evaluate backward obligations per stage (count only the producing type of that stage) and report the stage in the gap.
- **Solution B:** `config-validate` warns when two stages declare the same (link, up, direction both).

### PH-05 Workflow traces apply per need type

- **Tool:** ubc 0.35.0
- **Marker:** `main@37257e1` `ubproject.toml` (stage `bms_allocation` producing `arch`) with an `arch` in `docs/subsystems/bms/architecture.rst`.
- **Summary:** `[[workflow.stages.trace]]` has only `link`, `up`, `direction`,
  `min`; a stage producing a type shared with another stage cannot opt out of
  the other stage's downstream obligations.
- **Input:** black-box `arch` in stage `bms_allocation`; stage `swreqs` has `refines` up `arch` direction both.
- **Wrong output:** permanent gap `{'id': 'ARCH_BMS_EVAL', 'link': 'refines', 'category': 'trace_backward'}`; both stages count all 17 `arch`.
- **Workaround:** dedicated type `bms_block` (`e744d72`).
- **Solution A:** a `select` / `filter` per stage (e.g. by route path or docname) deciding which needs belong to it.
- **Solution B:** attribute needs to the stage whose route they live in; traces apply per stage, not per type.

### PH-06 Stage counts include imported needs

- **Tool:** ubc 0.35.0 (`agent status`, `agent next`)
- **Marker:** `main@e744d72`, product `truck_bev_nmc_eu` configured (no CV content).
- **Summary:** needs with a status in `exempt_status` (`imported`) are excluded
  from gaps but counted as stage output.
- **Input:** `[workflow] exempt_status = ["imported"]`, 205 imported `BMS_*` needs, no CV needs.
- **Wrong output:** `user_stories=done/5 reqs=done/20 …`; `agent next` → stage `bms_allocation` (or `done`). Expected: `user_stories=ready/0`, next `user_stories` (as in the diesel product).
- **Workaround:** check with `-c 'needs.external_needs = []'` or in the diesel product.
- **Solution A:** apply `exempt_status` to stage counts and `next`.
- **Solution B:** exclude `is_external` needs from all workflow counts by default.

### PH-07 `review-brief` lists exempt needs

- **Tool:** ubc 0.35.0
- **Marker:** `content/cv-platform@25b77bd`, `ubc agent review-brief arch -p .` under `truck_bev_nmc_eu`.
- **Summary:** `review_needs` contains the 15 imported `BMS_ARCH_*` needs; `verdict-check` correctly ignores them.
- **Wrong output:** `"review_needs": ["BMS_ARCH_…", …, "ARCH_VCU_…"]`. Expected: only non-exempt, local needs.
- **Workaround:** reviewer instruction "skip `BMS_*`".
- **Solution A:** apply `exempt_status` in `review-brief`.
- **Solution B:** list them separately as `exempt` for transparency.

### PH-08 `agent audit` omits fields and links

- **Tool:** ubc 0.35.0
- **Marker:** `content/cv-platform@25b77bd`, `ubc agent audit --id SWREQ_CHG_SESSION_START -p .` / `--id REQ_MAX_CHARGE_POWER`.
- **Summary:** `audit` shows neither the (resolved) `value` nor `tags`; `trace.outgoing` lacks `refines` and `allocates`, `trace.incoming` lacks `refines_back` (they appear only under `links`).
- **Wrong output:** reviewers had to use `ubc query filter … --field value` and read `build/active/bms.needs.json`.
- **Solution A:** include all declared fields (resolved) and all links in `trace`.
- **Solution B:** `--fields all` / `--links all` options, documented in the review skills.

### PH-09 `doctor` checks only the `.claude` copy of project skills

- **Tool:** ubc 0.35.0 (`agent doctor`)
- **Marker:** `main@e744d72` `.claude/skills/draft-allocation/SKILL.md` — delete or change `.agents/skills/draft-allocation/SKILL.md`.
- **Summary:** for skills outside the install manifest, `doctor` requires `.claude/skills/<n>/SKILL.md` but does not check the `.agents/skills/` and `.github/agents/` copies or their drift.
- **Wrong output:** `doctor ok` with a missing / different `.agents` copy.
- **Workaround:** `tools/check_skill_mirrors.py`.
- **Solution A:** mirror check for every skill found in any host location.
- **Solution B:** `ubc agent skill add <path>` registering project skills in the manifest (then the existing mirror check applies).

### PH-10 Brief and skill documentation gaps

- **Tool:** ubc 0.35.0 + installed `review-*` skills (vmodel v9)
- **Marker:** `content/cv-platform@25b77bd`, any `review-brief`.
- **Summary:** `submit_command` omits `-p <project>` although the skills require it; `verdict-check` returns a `stale` bucket (verdict of a need absent in the product) not described in the skills; exit code 1 whenever `ok` is false.
- **Solution A:** include `-p` in `submit_command`; document `stale` (useful for product lines).
- **Solution B:** `verdict-check --variant-aware` treating `stale` explicitly as "not applicable".

## 5. Sphinx-Needs

### SN-01 Every schema severity is a Sphinx warning

- **Tool:** Sphinx-Needs 8.5.0
- **Marker:** `content/cv-platform@25b77bd` `docs/conf.py:24` (workaround).
- **Summary:** `warning` and `info` schema results become Sphinx warnings, so `sphinx-build -W` fails on rules meant as non-blocking (backward coverage while a stream is in progress).
- **Input:** schema rule `coverage-req-satisfies-back` with `"severity": "warning"`, a req without arch yet.
- **Wrong output:** `WARNING: Need 'REQ_…' has schema warnings … [sn_schema_warning.network_contains_too_few]` → build failed with `-W`.
- **Workaround:** `suppress_warnings = ["sn_schema_warning.network_contains_too_few"]` (as the BMS).
- **Solution A:** map severities: `violation` → warning (fails `-W`), `warning` / `info` → log only; configurable `needs_schema_warn_level`.
- **Solution B:** a per-rule `fail_build` flag.

### SN-02 `needs_from_toml` overrides `needs_external_needs` in `conf.py`

- **Tool:** Sphinx-Needs 8.5.0
- **Marker:** `main@e744d72` `ubproject.toml:48-50` and `docs/conf.py`.
- **Summary:** a `needs_external_needs` computed in `conf.py` (e.g. per-chemistry `base_url`) is replaced by the TOML value.
- **Input:** `conf.py`: `needs_external_needs = [{"json_path": …, "base_url": f".../{chemistry}"}]` with `needs_from_toml = "../ubproject.toml"`.
- **Wrong output:** the TOML `base_url` is used. Expected: `conf.py` wins (or merge), as for other Sphinx options.
- **Workaround:** one `base_url` per BMS version.
- **Solution A:** let `conf.py` override TOML (documented precedence).
- **Solution B:** variant functions in `base_url` (`<<[var.bms.chemistry == 'lfp']: …/lfp, …/nmc>>`), supported by ubc as well.

### SN-03 `needs.json` drops external needs by default

- **Tool:** Sphinx-Needs 8.5.0
- **Marker:** `main@e744d72` `ubproject.toml` (`builder_filter = ""` is the workaround).
- **Summary:** default `builder_filter = "is_external==False"`; ubc exports external needs → per-product exports differ (0 vs 205).
- **Workaround:** `builder_filter = ""`.
- **Solution A:** align the default with ubc (or ubc with Sphinx) and document it.
- **Solution B:** see UB-08 — both tools honour the same option.

### SN-04 Duplicate id raises an exception

- **Tool:** Sphinx-Needs 8.5.0
- **Marker:** `content/cv-platform@25b77bd` `src/vcu/energy_display.c:7,16,25` — remove `#if` / `#else` / `#endif` around the two `IMPL_VCU_ENERGY_DISPLAY` markers (and rename one function).
- **Wrong output:** traceback ending `sphinx_needs.exceptions.InvalidNeedException: A need with ID 'IMPL_VCU_ENERGY_DISPLAY' already exists. [duplicate_id]`. Expected: a located warning `file:line` (ubc: `warning[needs.duplicate]`), build continues with `--keep-going`.
- **Solution A:** catch `InvalidNeedException` for code-derived needs and emit a warning with the source location.
- **Solution B:** let sphinx-codelinks check ids before creating needs.

### SN-05 Schema `contains` without `items` rejected

- **Tool:** Sphinx-Needs 8.5.0 (ubc accepts)
- **Marker:** `main@e744d72` `metamodel/schemas.json:979` (`alloc-target-interface`) — remove `"items": {"type": "string"}`.
- **Input:** `"tags": {"type": "array", "contains": {"type": "string", "const": "interface"}}`
- **Wrong output:** sphinx-needs rejects the schema; ubc validates it. Expected: same acceptance (valid JSON Schema).
- **Solution A:** accept `contains` without `items`.
- **Solution B:** ubc applies the same restriction and reports it.

## 6. Sphinx-Codelinks

### CL-01 Fails in a git worktree

- **Tool:** Sphinx-Codelinks 1.4.0 (`set_remote_url = true`)
- **Marker:** any commit, e.g. `main@cda14bc`: `git worktree add ../wt main && cd ../wt && tools/build_product.sh truck_diesel_eu`.
- **Wrong output:** `src/eng.rst: WARNING: git root is not found in the parent of …/wt` (×4) → `-W` fails. In a worktree `.git` is a file, not a directory.
- **Workaround:** build in the main checkout.
- **Solution A:** use `git rev-parse --show-toplevel` / accept a `.git` file.
- **Solution B:** a config option for the repository root / commit (also for CI checkouts without `.git`).

### CL-02 `.c` file without compile-database entry skipped silently

- **Tool:** Sphinx-Codelinks 1.4.0 and ubc 0.35.0 (preprocessor with explicit `compile_commands`)
- **Marker:** `main@e744d72` `tests/CMakeLists.txt` — remove `add_executable(test_vcu …)`.
- **Wrong output:** markers of `tests/vcu/test_vcu.c` disappear without a message. Expected: a warning "file not in compile database".
- **Workaround:** every traced `.c` file is built by CMake.
- **Solution A:** warn per skipped file.
- **Solution B:** fall back to `includes` / `defines` (as for headers) with an info.

### CL-03 `remote-url` / `local-url` differ between Sphinx and ubc

- **Tool:** Sphinx-Codelinks 1.4.0 and ubc 0.35.0
- **Marker:** `content/cv-platform@25b77bd`, any product, `IMPL_VCU_ENERGY_DISPLAY` in `build/site/<p>/{ubc,sphinx}.needs.json`.
- **Wrong output:** ubc: `remote-url = https://github.com/…/blob/<commit>/src/vcu/energy_display.c#L8`, `local-url = file:///Users/<user>/…`; Sphinx: `remote-url = src/vcu/energy_display.c#L8`, `local-url = ../../vcu/energy_display.c#L8`. Expected: same values; no absolute paths in an export.
- **Solution A:** both tools apply `remote_url_pattern` and write relative `local-url`.
- **Solution B:** `local-url` only in HTML, never in `needs.json`.

### CL-04 Broken CSS path on source pages

- **Tool:** Sphinx-Codelinks 1.4.0
- **Marker:** `content/cv-platform@25b77bd`, `build/site/<p>/sphinx/` source pages.
- **Wrong output:** reference to `_static/_static/source_tracing/ub_sct.css` (404). Expected: `_static/source_tracing/ub_sct.css`.
- **Solution A:** register the CSS with a path relative to `_static`.
- **Solution B:** use `app.add_css_file()` with the package static dir.

## 7. sphinx-mounts

### SM-01 Bare boolean condition: abort vs warning

- **Tool:** sphinx-mounts 0.2.0 (vs ubc 0.35.0)
- **Marker:** `main@e744d72` `ubproject.toml:62` — change a rule to `if = "var.charging.mcs"`.
- **Wrong output:** sphinx-mounts aborts the build; ubc warns and excludes the rule. Expected: the same behaviour (and both accept `var.charging.mcs`, or both reject it with the same message).
- **Workaround:** always `== True` (enforced by `tools/check_variants.py`).
- **Solution A:** accept bare booleans in both.
- **Solution B:** same diagnostic code and severity in both (error), pointing to `== True`.

## 8. useblocks/ubc-action

### UA-01 Linux runners only

- **Tool:** useblocks/ubc-action
- **Marker:** — (plan 6, A§2.2; not used yet).
- **Summary:** the action installs ubc only on Linux runners; macOS / Windows jobs cannot run `ubc`.
- **Solution A:** support macOS / Windows (the extension already ships ubc for them).
- **Solution B:** document a manual install route (download URL per platform, checksum).
