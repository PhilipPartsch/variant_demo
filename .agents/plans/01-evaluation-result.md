# Result of plan 1: Evaluation of the open questions

Plan: [01-evaluation.md](01-evaluation.md) · Branch: `eval/open-questions`
(commits `54ad812`, `dcf3429` (F4 recheck), local only, not pushed) · Date: 2026-10-08

## 1. Summary

| | Count |
|---|---|
| Answered **works** | 23 (A1–A7, B1, C1, C3, C4, C5, D1, D2, D3, E1, E2, E4, E6, F3, G1, G2 + IDE parts of A2, A3, C1, E1) |
| Answered **works with workaround / rules** | 6 (B2, C2, E3 delayed Needs Index, F1, F2, F4) |
| **Blocked** | 0 |
| Moved to the first CI run on `main` (A§1.1) | G3 (ubc without licence), G4 (deploy to `gh-pages`), E5 (libclang on Linux), G5 (visual check of the compare page) |

All P1 questions are answered; none is blocked. The IDE check (U3) was done
on 2026-10-08 with CMake Tools and ubCode 0.35.0.

**Go / no-go for plan 2: GO.** The basic setup (plan 2) can start with the
decisions written into it (§6). The CI-only questions are verified by the
first CI run on `main`, each with a fallback (A§1.1).

## 2. Environment (A7)

| Tool | Version used | Note |
|---|---|---|
| ubc CLI | **0.35.0** (bundled with the ubCode extension) | the separately installed CLI is 0.33.0 — pin 0.35.0 everywhere |
| ubCode VS Code extension | 0.35.0 | |
| Sphinx | 8.2.3 | |
| sphinx-needs | **8.5.0** (latest release) | has `if`; **no `choose`** |
| sphinx-mounts | 0.2.0 | |
| sphinx-codelinks | 1.4.0 with `[libclang]` | libclang wheel works on macOS arm64 |
| kconfiglib | 14.1.0 | |
| CMake / Ninja | 4.4.2 / homebrew | |
| Python | 3.12 (`.venv`) | |
| BMS data | `rollout-demo-bms` `main`, exported with ubc 0.35.0 | 205 needs |

## 3. Answers

Products: **D** = `truck_diesel`, **N** = `truck_bev_nmc` (MCS, 800 V),
**B** = `bus_bev_lfp` (pantograph, 400 V). "Both" = ubc **and** `sphinx-build -W`
gave identical results (compared with `tools/eval_compare.py`).

### Group A — variant data and conditions

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| A1 | **works** with `[needs] variant_data_file` | `[variants] data_file` is read by **none** of the three tools (all `if`/`:variant:`/file rules lose their data) | keep `[needs] variant_data_file`; remove the `[variants]` option from M§1.4 |
| A2 | **works** (CLI and IDE) | `REQ_MCS` only in N; IDE (2026-10-08): known to ubCode in `truck_bev_nmc`, gone after switching to `truck_diesel` | keep `if` for need-bearing content |
| A3 | **works** (CLI and IDE) | complementary `if` blocks with the same ID: exactly one `REQ_ENERGY_SOURCE` per product, **no duplicate-ID warning** in `ubc check`, Sphinx `-W` or the ubCode editor; the active block follows the product (`bev` in N, `not bev` in D) | keep complementary `if` blocks as interim alternatives (M§5.1) |
| A4 | **works** (both) | named variant `<<bus: 250 kW, 450 kW>>`, inline `<<[var.vehicle.type == "bus"]: …>>` and `<{ var.meta.product }>` in fields give identical values | — |
| A5 | **works** (both) | identical docnames; toctree entries to excluded files reported as INFO, `-W` passes for D | needs `[source] dir = "docs"` in the root `ubproject.toml` and `sources_from_toml = "../ubproject.toml"` in `docs/conf.py` |
| A6 | **works** (both) | disabled choice `bms.chemistry = ""` evaluates without `variant_rule_unevaluable`; **bare boolean** `var.charging.mcs` → ubc excludes the rule with a warning, sphinx-mounts **aborts the build** | `== True` is mandatory (K§4.2 confirmed) |
| A7 | **answered** | see §2 | pin the versions of §2 |

### Group B — links

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| B1 | **works** (both) | link variant per list item: `<<bev: BMS_REQ_POWER_DERATING>>, <<bev: BMS_REQ_PACK_OVERCURRENT>>`; non-matching item dropped. Representation differs: empty = `None` (ubc) vs `[]` (Sphinx) | write multi-target link variants **per item**; normalise `None`/`[]` in comparisons |
| B2 | **works with workaround** | links to prefixed external needs resolve in both. Sphinx fills the backlink `allocated_from` on the external need, **ubc does not** (empty in its needs.json). Links to the BMS docs pointed to `__error__.html` because the ubc export has **no `docname`** | pin script derives `docname` from ubc's `__source__` (F-2); BMS-usage report from Sphinx needtable; ubc backlink → feedback to useblocks |

### Group C — external needs (BMS import)

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| C1 | **works** (CLI and IDE) | `BMS_*` IDs resolve in ubc and Sphinx and via MCP (F3); IDE hover on `BMS_REQ_POWER_DERATING` shows the imported need | — |
| C2 | **works with workaround / deferred (P3)** | ubc: `-c 'needs.external_needs = [{… base_url = …/lfp}]'` works. Sphinx: `needs_from_toml` **overrides** a `needs_external_needs` set in `conf.py`, so the URL cannot follow the product there | defer; options: one `base_url` per BMS version, or generate the external-needs block at configure time |
| C3 | **works** (both) | empty stub `{"current_version":"0.1.0","project":"bms","versions":{"0.1.0":{"needs":{}}}}` → clean build for D | — |
| C4 | **works** (both) | rule with `select` on `is_external == false`: 0 findings on `BMS_*`; without it ~20 false violations | — |
| C5 | **works** (both) | network rule on `allocates` targets reports the non-interface allocation in both tools; sphinx-needs only accepts the array form **with `items`**: `{"type":"array","items":{"type":"string"},"contains":{"type":"string","const":"interface"}}` | use that form (no CI script fallback needed) |

### Group D — CMake Tools and IDE

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| D1 | **works** (after a one-time kit selection) | First observation: without a kit, selecting a variant did not configure, and `build/active/` still held a CLI product. After **CMake: Select a Kit** → project kit `cv-platform` (no fixed compiler; CMake chose `/usr/bin/cc`), every **variant switch reconfigures automatically** (CMake Tools log: `cmake.setVariant` → configure → copy `compile_commands.json`, 2026-10-08 01:35–01:36). Result: `build/cmake/truck_bev_nmc/` (Debug, Ninja), `build/active/*` = `truck_bev_nmc`. Decision: build type always `Debug`, no `buildType` axis (commit `95ac708`) | B§6.3: first open = select kit once; project kit confirmed |
| D2 | **works** | after switching `truck_bev_nmc` → `truck_diesel`, ubCode re-indexes the changed `build/active/variants.json` without manual reload: `REQ_MCS` disappears, the `not bev` block of `REQ_ENERGY_SOURCE` becomes active. BMS hover in `truck_diesel` not checked separately; the CLI confirms 0 `BMS_*` needs for diesel (C3) | — |
| D3 | **works** (visible) | CLI: a broken defconfig fails configure and removes the active copies — except the `VARIANT` marker (fix in plan 2). IDE (2026-10-08): after `rm build/active/variants.json`, ubCode reports on `docs/index.rst`: *'variant' role used but no variant data is available: 'meta.product'* / *'bms.chemistry'* — the missing data is **visible**, not silent After a variant switch / configure, the file is recreated and the warnings disappear (row 7) | keep the `:variant:` product marker on the landing page as the sanity indicator (B§6.3) |

### Group E — code analysis

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| E1 | **works** (CLI and IDE) | per product exactly the active branch: D `IMPL_EVAL_DIESEL`; N `IMPL_EVAL_BEV, _MCS, _HDR_MCS, _CHG`; B `IMPL_EVAL_BEV, _CHG`; IDE: `IMPL_EVAL_ENERGY` visible in the `code_trace.rst` preview and the Needs Index | — |
| E2 | **works** (both) | header marker in `#if CONFIG_CHARGING__MCS` only in N (fallback `includes = ["build/active", …]`) | — |
| E3 | **works, with delay** | after the switch `truck_bev_nmc` → `truck_diesel`, the `code_trace.rst` preview showed the diesel code needs at once, the ubCode Needs Index first still showed the old state; after the next reconfigure (row 7) `IMPL_EVAL_ENERGY` points to `energy.c` line 11 = the `#else` (fuel) branch | B§6.3: if the Needs Index lags, run **CMake: Configure** once (or switch the product); report the lag to useblocks |
| E4 | **works** (both) | no `chg` markers in D (component not built, `code_trace.rst` excluded) | — |
| E6 (added) | **works** (both) | same need ID `IMPL_EVAL_ENERGY` in `#if CONFIG_POWERTRAIN__TYPE__BEV` and `#else`, switched by `compile_commands = "build/compile_commands.json"`: exactly one need per product — D from `#else` (fuel, line 11), N / B from `#if` (SoC, line 8); same in ubc and Sphinx, no duplicate warning. Negative probe without `#if` / `#else`: ubc `needs.duplicate`, Sphinx `duplicate_id` (commit `73dfb17`) | code showcase C§5.1; V12b, DOC-09b, NEG-16 |
| E5 | **macOS works**; Linux moved to the first CI run (A§1.1); Windows not targeted | libclang wheel loads on macOS arm64 | Linux verified by the first CI run on `main` |

### Group F — AI workflow

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| F1 | **works with workaround** | two stages producing `arch` and an `allocates` trace to external needs pass `config-validate`. But **imported needs are counted as CV work**: 40 review gaps + 1 trace gap on `BMS_*` needs | pin script sets `status = "imported"` on every BMS need; `[workflow] exempt_status = ["imported"]` → BMS gaps disappear, coverage counts CV needs only |
| F2 | **works with workaround** | `-c "needs.variant_data_file = …"` switches docs and BMS import, but **not** the code analysis (active `compile_commands.json`); overriding nested codelinks settings via `-c` replaces the whole project table and breaks discovery | run per-product gates **after configuring that product** (`build_product.sh`, CI matrix), not via `-c` alone |
| F3 | **works** | `ubc serve mcp` → `query_cypher` returns `BMS_REQ_POWER_DERATING` (active product) | — |
| F4 | **works with rules** (rechecked) | First run created the skill only in `.agents/skills/` → doctor error. Recheck with all three host locations: `ubc agent doctor` is **ok**. Doctor requires only `.claude/skills/<name>/SKILL.md`; it does **not** check the `.agents/skills/` and `.github/agents/` copies of project skills and does not detect drift between them (mirror checks exist only for manifest-owned skills). Project skills are not in the install manifest, so `ubc agent update` leaves them alone (per its documentation). **Author skills resolve per stage** (`bms_allocation` → `draft-allocation`), but **review skills resolve per need type**: with two stages producing `arch`, the last stage's review skill is used for **all** `arch` needs | custom author skill `draft-allocation`, identical in `.claude/skills/`, `.agents/skills/`, `.github/agents/`; review stays `review-arch` (allocation criteria in `arch.toml`); `tools/check_skill_mirrors.py` keeps the three copies in sync (CI). A separate review skill would need a dedicated need type (`bms_ifc`) |

### Group G — automation

| ID | Answer | Evidence | Decision |
|---|---|---|---|
| G1 | **works** | `ubc build html` per product after configuring it; values per product correct (D 450 kW, B 250 kW, `REQ_MCS` only in N). Exit code non-zero on any warning (default `deny`) | build after configure; keep the strict `deny` in CI |
| G2 | **works** | ubCode HTML uses only relative paths; served under `/<product>/ubcode/` over HTTP (200) | — |
| G3 | **moved to the first CI run on `main` (A§1.1)** — not testable without pushing | ubCode README: *"available free of charge with all features for public open source projects"*; useblocks docs: detection via a publicly reachable Git repo **and an OSI-approved licence**. `PhilipPartsch/variant_demo` is public but has **no licence file** (`licenseInfo: null`). `useblocks/ubc-action` is **Linux only** | add an OSI licence on `main`, then the CI dry run |
| G4 | **configured; deploy test moved to the first CI run (A§1.1)** | Publishing via the **`gh-pages` branch with one folder per variant** (your decision). `gh-pages` = empty orphan commit `ce0f2fc` on `origin`. Pages **enabled** (2026-10-08): source `gh-pages` / root, status `built`, HTTPS enforced, `https://philippartsch.github.io/variant_demo/`. Build type `legacy` → Jekyll runs, so the first deploy must write `.nojekyll`. Default workflow token is `read` → the `pages` job requests `contents: write` | B§3.4 R4–R8; A§2.1 |
| G5 | **works technically**; visual check moved to the first CI deploy (A§1.1) | same-origin compare page with two iframes; all 2,105 relative references resolve except 9 (F-7) | open `build/site/index.html` via a local server to look at it |

## 4. Additional findings (not asked, but decisive)

| # | Finding | Consequence |
|---|---|---|
| F-1 | Imported needs of an **undeclared type are dropped**, **undeclared fields are stripped** — in both tools (50 BMS test results lost, `chemistry` stripped) | the CV metamodel must declare **all** BMS types, links and the BMS fields it keeps (`chemistry`, test-result and gap fields, `code_url`); plus `local-url` via codelinks `set_local_url` |
| F-2 | The ubc `needs.json` export carries **no `docname`** but a `__source__` block with **absolute local paths** | pin script: derive `docname` from `__source__.path` relative to the BMS `docs/`, then drop `__source__` (`tools/eval_pin_bms.py`) |
| F-3 | Text written with the `:variant:` role stays **unresolved** in the exported `content`; only fields are resolved (`chemistry` NMC/LFP) | CV can show chemistry-specific **values** only if the BMS exposes them as **fields** (e.g. `cell_v_min`, `cell_v_max`) — BMS-side change |
| F-4 | kconfiglib **silently ignores** a defconfig assignment with unmet dependencies (MCS on a 400 V bus) | generator compares every assigned value with the resolved value and fails (implemented) |
| F-5 | With the codelinks preprocessor and an explicit `compile_commands.json`, a **`.c` file without a DB entry is skipped** (both tools); headers are fine | tests (and every traced `.c` file) must be built by CMake |
| F-6 | codelinks: `set_remote_url = true` requires `remote_url_pattern` per project; ubc warns that the default marker start `@` collides with Doxygen in C | `remote_url_pattern = "https://github.com/PhilipPartsch/variant_demo/blob/{commit}/{path}#L{line}"`; `start_sequence = "@need:"` |
| F-7 | sphinx-codelinks 1.4.0 writes source pages with a broken CSS path (`_static/_static/source_tracing/ub_sct.css`) | cosmetic; report upstream |
| F-8 | The per-product `-W` build **catches a test marker that verifies a gated swreq** (D: `TEST_EVAL_ENERGY` → missing `SWREQ_EVAL_BEV`) | confirms coding rule C§5.3; markers are gated like their targets |
| F-9 | `exempt_status = ["imported"]` needs the value `imported` | add `imported` to the `status` values of the CV metamodel |
| F-10 | `useblocks/ubc-action` supports **Linux only** | nightly macOS / Windows runs (A§2.2) need another ubc installation route or run Sphinx only |
| F-11 | ubc reports an info `variant_sources_sphinx_unsupported` on every check | informational; Sphinx honours the rules with sphinx-mounts 0.2.0 |
| F-12 | Skills live in **three host locations** with identical content (`.claude/skills/<n>/SKILL.md`, `.agents/skills/<n>/SKILL.md`, `.github/agents/<n>.agent.md`); the install manifest records all three with the same hash | every skill change touches all three; `tools/check_skill_mirrors.py` enforces it (13 skills in sync; a changed copy is reported) |
| F-13 | `ubc agent review-brief <type>` lists **imported** needs (`BMS_ARCH_*`) as review targets — it ignores `exempt_status`; the gate `verdict-check` does honour it | noise for reviewing agents; reviewer instruction: skip `BMS_*`; feedback to useblocks |

## 5. Pending — needs you

| # | What | Why |
|---|---|---|
| U1 | ~~Choose an OSI licence~~ **MIT** chosen; `LICENSE` committed and **pushed** on `main` (`6ef4c49`, 2026-10-08); GitHub detects `MIT`; `eval/open-questions` rebased onto it | condition for free ubc use in a public project (G3) — fulfilled |
| U2 | ~~Push `eval/open-questions` with a CI workflow~~ **declined** — the repository stays clean; evaluation branches stay local. Pages **enabled** by you. G3, G4 (deploy) and E5 (Linux) are verified by the first CI run on `main` (A§1.1); the repository settings are described step by step in B§3.4 | G3, G4, E5 (Linux) |
| U3 | ~~Manual IDE check~~ **done** 2026-10-08 — results in D1, D2, D3, E3 and the IDE parts of A2, A3, C1, E1 | — |

## 6. Plan updates to apply

Applied to the plans together with this result (see each plan):

| Plan | Update |
|---|---|
| M§1.4 | `[variants]` is not read by any tool → use `[needs] variant_data_file` only |
| M§4 | multi-target link variants are written per item; answered |
| K§4.2 / K§6 | bare boolean rejected (confirmed); generator must check assigned vs resolved values (F-4) |
| B§2.3 / B§3 | `[source] dir = "docs"`, `sources_from_toml` / `needs_from_toml` / `src_trace_config_from_toml = "../ubproject.toml"` |
| B§4.1–4.3 | declare all BMS types, links and kept fields (F-1); `status` gets `imported` (F-9); "not taken over" table removed for `chemistry` |
| B§4.4 | interface rule in the `items` + `contains` form (C5) |
| B§5.2 / B§5.3 | pin script: `docname` from `__source__`, drop `__source__`, tag `interface`, `status = "imported"` (F-2, F1); BMS should expose chemistry values as fields (F-3); `base_url` per product deferred (C2) |
| B§6.2 | `start_sequence = "@need:"`, `remote_url_pattern`, tests built by CMake (F-5, F-6); remove the `VARIANT` marker on configure failure |
| B§7.2 / B§7.4 | `bms_allocation`: author skill `draft-allocation` (three host locations), review `review-arch`; allocation criteria in `arch.toml`; skill mirror check (F4, F-12) |
| B§7.5 | `exempt_status = ["imported"]`; per-product gates after configure (F2) |
| C§5 | markers with `@need:` |
| A§1 / A§2.2 | ubc 0.35.0; Linux-only action (F-10); licence prerequisite (U1); skill mirror check in `checks` (F-12) |
| A§1 / A§1.1 / A§2.1 / A§3 | publishing via the `gh-pages` branch, one folder per variant, `.nojekyll`, concurrency group (G4); first-run verification of G3 / G4 / E5 / G5 on `main` (A§1.1) |
| B§3.4 | GitHub repository setup R1–R14 (state 2026-10-08, target, verification) |
| 00 / V§1 / T§ L7 | `eval/*` branches local only, never pushed; mechanism regression runs locally |
| T§3 | test for the skill mirror check (F-12) |

## 7. Artefacts on the branch

`ubproject.toml`, `docs/` (conf + 9 pages), `metamodel/schemas.json`,
`Kconfig`, `configs/*_defconfig`, `tools/kconfig2variants.py`,
`tools/eval_pin_bms.py`, `tools/eval_build.sh`, `tools/eval_compare.py`,
`CMakeLists.txt`, `src/`, `tests/`, `third_party/bms/local/`, `.vscode/`.
`kconfig2variants.py`, `eval_pin_bms.py`, the CMake active-copy logic and the
`ubproject.toml` snippets are ready to be copied into plan 2.
