# Plan 2: Basic setup of the repository

Step 2 of the [roadmap](00-roadmap.md) for the **commercial vehicle (CV) platform** — one platform,
configured as truck or bus, diesel or battery-electric — where the
battery-electric variants **use the existing BMS product** (`rollout-demo-bms`),
imported with `needs_external_needs`.

The CV platform is built **in this repository** (`variant_demo`,
`origin` = `https://github.com/PhilipPartsch/variant_demo`), replacing the
current feature-tour demo (§3.2). No new repository is created.

This plan prepares the **structured, empty repository**: configuration,
metamodel, build, IDE, BMS import, AI workflow and local build entry points.
It starts after the evaluation ([01-evaluation.md](01-evaluation.md), `E§`) and
applies its decisions. Afterwards:

- [03-mechanism-evaluation.md](03-mechanism-evaluation.md) (`V§`) proves every
  variant mechanism on a side branch; bugs it finds are fixed **here, on
  `main`**;
- [04-content.md](04-content.md) (`C§`) fills the structure;
- [05-test.md](05-test.md) (`T§`) tests it;
- [06-automation.md](06-automation.md) (`A§`) runs builds and tests in CI and
  publishes all products to GitHub Pages.

Builds on:

- [variant-mechanisms.md](variant-mechanisms.md) (`M§`) — how documents consume
  `var.*` (fields, links, `if`, `variant_sources`, mounts)
- [kconfig-variant-configuration.md](kconfig-variant-configuration.md) (`K§`) —
  Kconfig feature model, generator, CMake and VS Code / CMake Tools selection

The open questions were answered by plan 1; see
[01-evaluation-result.md](01-evaluation-result.md) (`E-R`). Answers are written
into this plan; the few items still open are listed in §11.

## 0. Goals and definition of done

Goals:

1. A repository in which **every product configuration** configures, builds and
   produces its documentation — before any real content exists.
2. Variant selection in **CMake Tools** switches CV docs, BMS needs and code
   analysis together.
3. The **BMS stays independent**: the CV platform consumes its published
   artifacts, it does not rebuild it.
4. The **AI workflow** is installed and points the agents at the first stage.

Definition of done (handover to plans 3 and 4):

| # | Criterion |
|---|---|
| D1 | All four products (§2.2) configure in CMake Tools and on the CLI. |
| D2 | `docs` target builds with `sphinx-build -W` for every product; skeleton pages render; `<{ var.meta.product }>` shows the product. |
| D3 | `ubc build` / `ubc check` pass for every product. |
| D4 | BEV products see the imported `BMS_*` needs of the right chemistry; the diesel product sees none. |
| D5 | Codelinks preprocessor analyses the (stub) C sources of every built component. |
| D6 | `ubc agent next` names the first workflow stage (`user_stories`). |
| D7 | The local entry point (§8) runs D1–D5 for every product and the drift / consistency checks pass — the same entry point CI will call (A§). |
| D8 | The setup is pushed to `origin` (`PhilipPartsch/variant_demo`) and merged to `main` (§10, step 10). |

Non-goals: mechanism evaluation (V§), content (C§), tests (T§), CI and GitHub
Pages (A§); building BMS **code** into the CV platform; publishing to ubTrace.

## 1. Product structure

```
CV Platform (this repository)
├── Vehicle Control Unit (VCU)      own, all variants: drive modes, power management
├── Charging Controller (CHG)       own, BEV only: CCS / MCS / pantograph
├── Engine Interface (ENG)          own, diesel only: small stub
└── Battery Management System (BMS) external product, BEV only — needs via needs_external_needs
```

| Subsystem | Owner | Present in | Integration |
|---|---|---|---|
| VCU | CV platform | all | own docs + C code |
| CHG | CV platform | BEV | own docs + C code, gated by file variant |
| ENG | CV platform | diesel | own docs + small C stub, gated by file variant |
| BMS | BMS team (`rollout-demo-bms`) | BEV | imported `needs.json`, per chemistry |

CV code is written in **C** (built with CMake), so the codelinks preprocessor
(libclang) can evaluate `#if CONFIG_*` blocks per variant (§6.2).

## 2. Variant model (Kconfig, per K§4)

### 2.1 Feature model

| Symbol (namespace `__`) | Type | Constraint | Purpose |
|---|---|---|---|
| `VEHICLE__TYPE` | choice: `TRUCK`, `BUS` | — | truck vs bus requirements |
| `POWERTRAIN__TYPE` | choice: `DIESEL`, `BEV` | — | decides BMS / CHG / ENG |
| `BMS__ENABLED` | bool (hidden) | `default y if POWERTRAIN__TYPE__BEV` | single switch "uses the BMS" |
| `BMS__CHEMISTRY` | choice: `NMC`, `LFP` | `depends on BMS__ENABLED` | selects the BMS variant |
| `HV__CLASS` | choice: `V400`, `V800` | `depends on POWERTRAIN__TYPE__BEV` | charging capability, isolation context |
| `CHARGING__MCS` | bool | `depends on HV__CLASS__V800` | megawatt charging (trucks) |
| `CHARGING__PANTOGRAPH` | bool | `depends on VEHICLE__TYPE__BUS` | opportunity charging (city bus) |
| `MARKET__REGION` | choice: `EU`, `NA` | — | regulations, charging standard |

Subsystem fragments (`src/<x>/Kconfig`, namespaces `VCU__`, `CHG__`, `ENG__`)
start empty and are filled with the content (C§5).

Generated `var.*` (K§4.3): `var.vehicle.type`, `var.powertrain.type`,
`var.bms.enabled`, `var.bms.chemistry`, `var.hv.class`, `var.charging.mcs`,
`var.charging.pantograph`, `var.market.region`, `var.meta.product`.

Build kit / build type are **not** in the model (K§0 P3). The build type is
**always `Debug`** and not offered as a choice (decision 2026-10-08).

### 2.2 Product configurations (`configs/*_defconfig`)

| Product | Vehicle | Powertrain | BMS | Chemistry | HV | MCS | Pantograph | Market |
|---|---|---|---|---|---|---|---|---|
| `truck_diesel_eu` | truck | diesel | no | — | — | — | — | EU |
| `truck_bev_nmc_eu` | truck | BEV | **yes** | NMC | 800 V | yes | — | EU |
| `bus_bev_lfp_eu` | bus | BEV | **yes** | LFP | 400 V | — | yes | EU |
| `truck_bev_lfp_na` | truck | BEV | **yes** | LFP | 800 V | no | — | NA |

Every condition is true in ≥1 and false in ≥1 product (M§0.4). Both BMS
variants (NMC, LFP) are used; one product does not use the BMS at all.

### 2.3 Variant hooks in `ubproject.toml`

Prepared here, used by the content (C§4):

```toml
# Named variants over generated keys (M§1.6)
[needs.variants]
bev  = "var.powertrain.type == 'bev'"
bus  = "var.vehicle.type == 'bus'"
mcs  = "var.charging.mcs == True"

# Sources live in docs/; rule globs are anchored there (E-R A5)
[source]
dir = "docs"

# Variant data: only [needs] variant_data_file is read by all three tools (E-R A1)
[needs]
variant_data_file = "build/active/variants.json"

# File variants (M§6)
[[source.variant_sources]]
if = "var.powertrain.type == 'bev'"
files = ["subsystems/chg/**", "subsystems/bms/**"]

[[source.variant_sources]]
if = "var.powertrain.type == 'diesel'"
files = ["subsystems/eng/**"]

[[source.variant_sources]]
if = "var.market.region == 'na'"
files = ["region/na/**"]

[[source.variant_sources]]
if = "var.market.region == 'eu'"
files = ["region/eu/**"]
```

Fields with `parse_variants = true` are declared in §4.3.

## 3. Folder structure

Concretises K§3. **Docs and source are separate top-level trees**, and every
subsystem uses the **same name** in all of them (`vcu`, `chg`, `eng`).

```
variant_demo/                      this repository
├── ubproject.toml                 ubCode / sphinx-needs / codelinks / workflow config (project root)
├── Kconfig                        top-level feature model: vehicle, powertrain, BMS, HV, market
├── CMakeLists.txt                 VARIANT, generator, component selection, docs target
├── cmake/
│   ├── kconfig.cmake              runs kconfig2variants at configure time (K§7)
│   ├── bms.cmake                  selects the BMS needs.json for the variant (§5.3)
│   └── docs.cmake                 `docs` target: sphinx-build per variant
├── configs/
│   ├── truck_diesel_eu_defconfig
│   ├── truck_bev_nmc_eu_defconfig
│   ├── bus_bev_lfp_eu_defconfig
│   ├── truck_bev_lfp_na_defconfig
│   └── fragments/                 optional shared fragments (market, …)
├── variants/                      GENERATED variant data, committed + drift-checked (K§6)
│   └── <product>.json
├── docs/                          Sphinx source directory: documentation only
│   ├── conf.py                    `needs_from_toml`, `sources_from_toml`, `src_trace_config_from_toml` = "../ubproject.toml"
│   ├── index.rst                  shows <{ var.meta.product }>
│   ├── vehicle/                   user_stories.rst, requirements.rst       (all variants)
│   ├── system/                    system overview + component diagram (no needs)
│   ├── subsystems/                one folder per workflow stream (§7.2)
│   │   ├── vcu/                   architecture.rst, software_requirements.rst, code_trace.rst (all variants)
│   │   ├── chg/                   same                                      (BEV only, variant_sources)
│   │   ├── eng/                   same                                      (diesel only, variant_sources)
│   │   └── bms/                   architecture.rst (allocates BMS needs), integration page (BEV only)
│   ├── _global/                   risks.rst, decisions.rst, test_results.rst, gaps.rst
│   ├── region/{eu,na}/            market annexes                           (variant_sources)
│   ├── reports/                   traceability / coverage / BMS usage pages (C§7)
│   └── _static/
├── reports/                       `ubc report` templates (not Sphinx pages)
├── metamodel/                     not Sphinx source; read via ubproject.toml
│   ├── schemas.json               schema rules (§4.4)
│   └── quality/                   review criteria per type (§7.3)
│       ├── requirement.toml  arch.toml  feat.toml  decision.toml
├── src/                           production source only (C)
│   ├── vcu/
│   │   ├── Kconfig                VCU options (namespace VCU__), rsourced from top Kconfig
│   │   ├── CMakeLists.txt
│   │   ├── include/vcu/*.h
│   │   └── *.c                    codelinks markers: impl needs
│   ├── chg/                       same structure (namespace CHG__)
│   └── eng/                       same structure (namespace ENG__)
├── tests/                         test source only, mirrors src/
│   ├── vcu/  chg/  eng/           codelinks markers: test needs
│   └── CMakeLists.txt
├── third_party/
│   └── bms/<version>/{nmc,lfp}.needs.json   pinned BMS release artifacts (§5.3)
├── tools/
│   ├── kconfig2variants.py        generator (K§6)
│   ├── import_test_results.py     JUnit → test_result needs, per product (§4.3)
│   └── import_gaps.py             gate gaps → gap needs, per product (§4.3)
├── .agents/
│   ├── skills/                    AI workflow skills (§7.4), installed by `ubc agent install`
│   └── plans/                     these plans — local only, gitignored, may be removed later
├── .github/agents/                same skills as GitHub agents
├── .pharaoh/                      review verdicts + agent install manifest (§7.4)
├── .mcp.json                      `ubc serve mcp` for AI agents
├── .vscode/                       CMake Tools integration (K§8)
│   ├── cmake-variants.json        GENERATED variant picker
│   ├── cmake-kits.json            build kits (build-only)
│   ├── settings.json
│   ├── tasks.json
│   └── extensions.json
└── build/                         gitignored
    ├── cmake/<product>/           one CMake build dir per product — always Debug, shared by IDE and CLI
    │   ├── kconfig/               variants.json, autoconf.h, autoconf.cmake, .config
    │   └── compile_commands.json
    ├── compile_commands.json      active copy (cmake.copyCompileCommands)        §6.2
    ├── active/
    │   ├── variants.json          active variant data (K§7 6.6)
    │   ├── autoconf.h             active Kconfig header (codelinks fallback)     §6.2
    │   └── bms.needs.json         active BMS needs (§5.3)
    └── docs/<product>/            HTML per product (independent of the kit)
```

### 3.1 Folder rules

| Rule | Why |
|---|---|
| `docs/` contains **only** documentation; `src/` and `tests/` contain **only** code. | Clear ownership, clean Sphinx source dir, no code parsed as docs. |
| One `ubproject.toml` at the **repository root**. | ubc finds it from `docs/`, `src/` and `tests/` without redirect files; codelinks paths and `build/` paths resolve relative to one place. (The BMS demo keeps it in `docs/` and needs redirect files — avoided here.) |
| Subsystem names are identical in `docs/subsystems/<x>`, `src/<x>`, `tests/<x>`, Kconfig namespace `<X>__`, codelinks project `<x>`. | One name per subsystem; variant gating and traceability are predictable. |
| A subsystem's `Kconfig` lives with its **code** (`src/<x>/Kconfig`). | The code owner owns the options the code reacts to. |
| Variant-specific docs live in **directories**, not mixed into shared files. | Simple `variant_sources` globs (M§6). |
| Everything generated goes to `build/` (gitignored) — except `variants/*.json` and `.vscode/cmake-variants.json`, which are committed and drift-checked. | Reviewable configuration, no stale artifacts in git. |
| Imported products live under `third_party/<product>/<version>/`. | Version pin is visible in the path and in review. |
| Plans live in `.agents/plans/`: gitignored, and excluded from ubc and Sphinx with `.agents`. | Plans are working notes, not product documentation; they may be removed when the work is done. |

### 3.2 Existing repository content

The repository currently holds a small feature-tour demo. Before restructuring,
the current state of `main` is tagged `pre-cv-platform`, so nothing is lost.

| Existing | Becomes |
|---|---|
| `ubproject.toml` (root) | stays at the root, rewritten per §2.3, §4–§7; existing `[scripts]` adapted, existing `[workflow]` replaced by §7.2 |
| `conf.py` (root) | moves to `docs/conf.py`, `needs_from_toml = "../ubproject.toml"`; the `suppress_warnings` workaround is kept only if evaluation A7 (E§3) still requires it |
| `index.rst`, `requirements.rst`, `specifications.rst`, `tests.md` | removed (feature-tour content); preserved by the tag `pre-cv-platform` |
| `variants.json` | replaced by the generated `variants/<product>.json` (K§6) |
| `quality/*.toml` | moved to `metamodel/quality/`, merged with the BMS criteria and `variant_consistency` (§7.3) |
| `reports/needs_overview.html.j2` | stays in `reports/` as `ubc report` template |
| `.agents/`, `.github/agents/`, `.pharaoh/` | regenerated with `ubc agent install --detect` after the new `[workflow]` (§7.4) — **keep `.agents/plans/`**: back it up or check it is untouched after the reinstall |
| `.claude/` | unchanged (local Claude Code settings) |
| `README.md` | rewritten for the CV platform (build, product selection); no links to the local plans |
| `.agents/plans/` | unchanged; local only (gitignored) |
| `.gitignore` | `build/` added (next to `_build/`); `third_party/bms/**/*.needs.json` must stay tracked |
| `_build/`, root `needs.json` | obsolete (ignored); output moves to `build/` |

### 3.3 Skeleton content

The setup creates every file of the tree with **structure only**, so that D2
and D5 can pass before content exists:

| Path | Skeleton |
|---|---|
| `docs/**/*.rst` | title, short purpose sentence, toctree entries; no needs |
| `docs/subsystems/<x>/code_trace.rst` | the `src-trace` directives for the subsystem's codelinks projects |
| `docs/subsystems/bms/integration.rst` | a needtable of imported `BMS_*` needs (proves D4) |
| `docs/_global/*.rst` | empty sections; generated files written by the importers |
| `src/<x>/*.c`, `tests/<x>/*.c` | one compilable stub per subsystem, no markers |
| `src/<x>/Kconfig` | `menu` with no symbols yet |

### 3.4 GitHub repository setup

The repository stays **clean**: only `main` and `gh-pages` live on `origin`.
Work branches are pushed only for their pull request and deleted on merge;
evaluation branches (`eval/*`) stay **local** and are never pushed.

State read with `gh api` on 2026-10-08, target, and how to get there:

| # | Setting | State 2026-10-08 | Target | How / verify |
|---|---|---|---|---|
| R1 | Visibility | public | public (needed for free ubc use and free Pages) | `gh api repos/PhilipPartsch/variant_demo --jq .visibility` |
| R2 | Default branch | `main` | `main` | `--jq .default_branch` |
| R3 | Licence | **MIT**, pushed on `main` (`6ef4c49`, 2026-10-08), detected by GitHub | done — ubc treats the project as open source only with an OSI licence (E-R G3) | `--jq .license.spdx_id` → `MIT` ✓ |
| R4 | GitHub Pages | **enabled**: source branch `gh-pages`, path `/`, HTTPS enforced, URL `https://philippartsch.github.io/variant_demo/`, status `built` | unchanged | `gh api repos/PhilipPartsch/variant_demo/pages` |
| R5 | Pages build type | `legacy` (Jekyll runs on every push to `gh-pages`) | keep, but the first deploy writes **`.nojekyll`** so `_static/` and `_sources/` are served (A§3.1) | open `…/variant_demo/<product>/sphinx/_static/` after the first deploy |
| R6 | `gh-pages` branch | empty orphan commit `ce0f2fc` | written only by the CI `pages` job (A§2.1) | `git ls-remote origin gh-pages` |
| R7 | Actions | enabled, all actions allowed, SHA pinning not required | allow **GitHub-owned actions plus selected**: `useblocks/ubc-action`, `astral-sh/setup-uv`; **require SHA pinning** | Settings → Actions → General → Actions permissions; `gh api repos/PhilipPartsch/variant_demo/actions/permissions` |
| R8 | Default workflow token | `read`, cannot approve PRs | keep `read`; only the `pages` job requests `permissions: contents: write` in the workflow file | `gh api repos/PhilipPartsch/variant_demo/actions/permissions/workflow` |
| R9 | Branch protection `main` | none | ruleset: pull request required, required status checks = `checks` + every `build (<product>)` job, block force pushes and deletion | Settings → Rules → Rulesets → New branch ruleset (target `main`) |
| R10 | Branch protection `gh-pages` | none | ruleset: block deletion; force pushes allowed (for the squash job, A§3.1) | ruleset with target `gh-pages` |
| R11 | Delete head branches on merge | off | **off** (decision 2026-10-09: user keeps merged branches; delete manually) | Settings → General → Pull Requests; `--jq .delete_branch_on_merge` → `true` |
| R12 | Secrets | none | none (no ubc licence for a public OSI-licensed project, E-R G3) | Settings → Secrets and variables → Actions is empty |
| R13 | About / homepage | — | description "CV platform: variant management with Kconfig, sphinx-needs, sphinx-mounts and ubCode"; website = the Pages URL; topics `sphinx-needs`, `ubcode`, `kconfig`, `variant-management` | Settings → General / About |
| R14 | `.gitignore` | `_build/`, `build/`, `.venv`, `.agents/plans/` | add `build/` explicitly if missing; keep `.agents/plans/` ignored (plans are local) | `git check-ignore -v build/x .venv/x .agents/plans/x` |

Order: R3 and R14 go into the first setup commit; R7, R8, R11, R13 are set
before the first push of `setup/cv-platform`; R9 and R10 are set **after** the
CI jobs exist (plan 6), because the required checks must be selectable.

## 4. Metamodel

**Principle:** take over the BMS metamodel (types, links, fields, schema
structure) unchanged wherever possible, so traceability, reports and AI skills
read the same in both products. Add only what the CV platform needs:
one cross-product link, product-aware evidence fields, and rules for imported
needs.

Global settings, as in the BMS:

```toml
[needs]
id_required = true
id_regex = "^[A-Z]+_[A-Z][A-Z0-9_]*$"   # also matches imported, prefixed BMS ids (BMS_REQ_…)
schema_definitions_from_json = "metamodel/schemas.json"
```

### 4.1 Need types

| Type | Prefix | Taken from BMS | CV use | Location (§3) |
|---|---|---|---|---|
| `user_story` | `US_` | yes | vehicle-level user stories | `docs/vehicle/user_stories.rst` |
| `req` | `REQ_` | yes | vehicle / system requirements | `docs/vehicle/requirements.rst` |
| `arch` | `ARCH_` | yes | system architecture elements, one or more per subsystem; for the BMS a black-box element | `docs/subsystems/<x>/architecture.rst` |
| `swreq` | `SWREQ_` | yes | software requirements of CV-owned subsystems (VCU, CHG, ENG) | `docs/subsystems/<x>/software_requirements.rst` |
| `impl` | `IMPL_` | yes | one-line marker in C source | `src/<x>/**` |
| `test` | `TEST_` | yes | one-line marker in C test source | `tests/<x>/**` |
| `test_result` | `TRES_` | yes | imported test results, **per product** | `docs/_global/test_results.rst` (generated) |
| `risk` | `RISK_` | yes | vehicle-level risks | `docs/_global/risks.rst` |
| `decision` | `DEC_` | yes | design decisions (Context / Alternatives / Consequences / Rationale) | `docs/_global/decisions.rst` |
| `gap` | `GAP_` | yes | workflow gaps from the gates, **per product** | `docs/_global/gaps.rst` (generated) |

Imported BMS needs keep **their** types (`req`, `arch`, …) and get the prefix
`BMS_` (§5.3); they are read-only in the CV project.

Keep the BMS colours and styles per type, so diagrams of both products look the
same.

### 4.2 Links

| Link | From → To | Incoming | Taken from BMS | `parse_variants` |
|---|---|---|---|---|
| `traces_to` | req → user_story | `traces_from` | yes | no |
| `satisfies` | arch → req | `satisfied_by` | yes | no |
| `refines` | swreq → arch | `refined_by` | yes | no |
| `implements` | impl → swreq | `implements_back` | yes | no |
| `verifies` | test → swreq | `verifies_back` | yes | no |
| `results_for` | test_result → test | `results` | yes | no |
| `mitigates` | risk → req | `mitigated_by` | yes | no |
| `affects` | decision → arch | `affected_by` | yes | no |
| `motivates` | (declared, unused) | `motivated_by` | yes | no |
| `gap_for` | gap → any need | `gaps` | yes | no |
| **`allocates`** | CV `arch` → BMS `req` (external, `BMS_REQ_*`) | `allocated_from` | **new** | **yes** |

```
user_story ◄─traces_to── req ◄─satisfies── arch ◄─refines── swreq ◄─implements── impl
                          ▲                 │ ▲                 ▲
                          │ mitigates       │ │ affects         └──verifies── test ◄─results_for── test_result
                         risk               │ decision
                                            └──allocates──► BMS_REQ_* (external, BEV only)
```

- `allocates` means "this BMS requirement realises the subsystem share described
  by the CV arch element". It may target **only BMS interface needs** (§5.2.3).
- Only `allocates` gets `parse_variants = true` (M§3: enable it only where
  needed). Variation of the other links is done with `if` (later `choose`) /
  file variants around the **source** need.

### 4.3 Fields

| Field | Applies to | Constraint | Taken from BMS | Variant-aware |
|---|---|---|---|---|
| `status` | authored spec needs | enum `draft` / `review` / `approved` / **`imported`** (set on every pinned BMS need, exempted from the workflow, E-R F1/F-9); required on spec needs | yes | no |
| `value` | vehicle `req` | free text; the product-specific value of a requirement | **new** | **yes** (`parse_variants`) |
| `outcome` | test_result | enum `passed` / `failed` / `error` / `skipped` | yes | no |
| `runtime_s` | test_result | free text | yes | no |
| `test_run_label` | test_result | timestamp pattern | yes | no |
| `chain_reqs` | test_result | vehicle reqs this result is evidence for (test → swreq → arch → req) | yes | no |
| `gap_category`, `gap_link`, `gap_shortfall`, `gap_need_id`, `gap_need_type` | gap | as in BMS (`gap_link` enum extended by `allocates`) | yes | no |
| **`product`** | test_result, gap | enum of the product names (`configs/*_defconfig`), generated with the variant list (K§6 `--vscode`) | **new** | no — it records **which** product the evidence belongs to |

**Imported needs need the BMS vocabulary (E-R F-1).** Both tools **drop** an
imported need whose type the CV project does not declare and **strip** every
undeclared field. Therefore the CV metamodel declares **all** BMS types and
links (§4.1, §4.2) and these BMS fields, even where the CV never sets them
itself: `chemistry`, `outcome`, `runtime_s`, `test_run_label`, `chain_reqs`,
the `gap_*` fields, `code_url`; `local-url` comes from codelinks
`set_local_url = true`.

**Not taken over from BMS:**

| BMS element | Why not |
|---|---|
| named variant `lfp` | BMS variant model (`var.pack.*`); CV uses its own named variants (§2.3) |
| codelinks projects `code` / `tests` (Python) | CV code is C; one codelinks project per subsystem and tree (§6.2) |

### 4.4 Schema rules (`metamodel/schemas.json`)

Same structure and severity split as the BMS:

| Severity | Rule group | Source |
|---|---|---|
| `violation` | id prefix per type | declared in `[[needs.types]]` |
| `violation` | upward trace per stage (`traces_to`, `satisfies`, `refines`, `implements`, `verifies`, `results_for`, `mitigates`, `affects`, `gap_for`) | declared in `[[workflow.stages.trace]]` (§7.2) |
| `violation` | `status` present on spec needs | declared field |
| `violation` | test_result / gap evidence fields present, incl. **`product`** | importers |
| `warning` | reverse coverage (every user_story decomposed, every arch refined, every swreq implemented and verified, every req satisfied) | stage `direction = "both"` |
| `warning` | single-parent conventions | observed, as in BMS |

**New CV rules:**

| Severity | Rule | Why |
|---|---|---|
| `violation` | `allocates` targets match `^BMS_REQ_` | only BMS requirements can be allocated |
| `violation` | `allocates` targets are BMS interface needs (tag `interface`) | §5.2.3 — `validate.network` on `allocates`; sphinx-needs requires the array form with `items`: `{"type":"array","items":{"type":"string"},"contains":{"type":"string","const":"interface"}}` (E-R C5) |
| `violation` | every BMS `arch` element (`docs/subsystems/bms/`) has ≥1 `allocates` | the black box must say what it expects from the BMS |
| — | all CV rules `select` only local needs (`is_external == False`) | imported BMS needs are validated by the BMS, not re-validated here |

**Variant-aware evaluation:** schemas run **per product** (§8 locally, CI matrix in A§); a
need gated out of a product is not in that product's graph and is therefore not
counted as missing coverage there (§7.5).

**Empty-repo behaviour:** with no content, coverage rules have nothing to check
and pass; trace rules apply as soon as the first need is authored.

### 4.5 Code markers

Same grammar as the BMS, with C comments (configuration in §6.2, usage rules in
C§5):

| Tree | Codelinks project | Marker | Default type | Link field |
|---|---|---|---|---|
| `src/<x>/` | `<x>` | `// @<title>, IMPL_<…>, [SWREQ_<…>]` | `impl` | `implements` |
| `tests/<x>/` | `<x>_tests` | `// @<title>, TEST_<…>, [SWREQ_<…>]` | `test` | `verifies` |

## 5. BMS integration infrastructure (`needs_external_needs`)

### 5.1 Why external needs (and not mounts)

| | `needs_external_needs` (chosen) | sphinx-mounts (M§7) |
|---|---|---|
| BMS config (ontology, codelinks, workflow) | not needed in CV | must be re-declared in CV |
| BMS variant resolution | already done in the BMS build | CV must produce `var.pack.*` for BMS docs |
| Relationship modelled | supplier / independent product | same docs build |
| BMS pages in CV output | links to BMS published docs | rendered inside CV |

Mounting stays a later option (C§10).

### 5.2 BMS side: what the BMS must provide

| Step | Action |
|---|---|
| 5.2.1 | Export one `needs.json` **per chemistry** — already exists as scripts `needs` (NMC default) and `needs:lfp`. |
| 5.2.2 | Publish both as **versioned release artifacts** (CI job on tag), e.g. `bms-<version>-nmc.needs.json`, `bms-<version>-lfp.needs.json`, plus the HTML of each variant. |
| 5.2.3 | Declare the **interface needs** (IDs the CV platform may link to) with the tag `interface`. Changing them is an interface change (K§10.4). |
| 5.2.4 | No change to the BMS variant model; the CV platform never touches `var.pack.*`. |

Interface needs to tag (existing BMS IDs; their use is content, C§3):

`REQ_POWER_DERATING`, `REQ_ISOLATION_FAULT`, `REQ_CELL_VOLTAGE_LIMITS`,
`REQ_SOC_ACCURACY`, `REQ_SOC_INVALID_FLAG`, `REQ_PACK_OVERCURRENT`,
`REQ_FAULT_REACTION_TIME`, `REQ_HEATING_REQUEST`, `REQ_COOLING_REQUEST`.

### 5.3 CV side: selecting the BMS variant

`needs_external_needs` is static configuration, not a `var.*` condition. The
variant selection therefore happens **at configure time**, using the same
pattern as the active variant copy (K§7 6.6):

| Step | Action |
|---|---|
| 5.3.1 | Pin the BMS version: `third_party/bms/<version>/{nmc,lfp}.needs.json` (committed, or fetched by CMake `FetchContent` from the release), processed by `tools/pin_bms.py` (from `eval_pin_bms.py`): derive `docname` from ubc's `__source__` path (the ubc export has no `docname`, so links would point to `__error__.html`), **drop `__source__`** (absolute local paths), tag the interface needs (until the BMS does it), set `status = "imported"` (E-R B2, F1, F-2). |
| 5.3.2 | `cmake/bms.cmake` reads `BMS__ENABLED` / `BMS__CHEMISTRY` from `autoconf.cmake` and copies the matching file to `build/active/bms.needs.json`. |
| 5.3.3 | Diesel products (`BMS__ENABLED=n`): copy an **empty but valid** `needs.json` stub, so no BMS needs appear and the config stays identical for all products. |
| 5.3.4 | On failure, delete the copy and the `build/active/VARIANT` marker (same rule as K§7 6.6; the experiment forgot the marker, E-R D3). |
| 5.3.5 | The `docs` target and CI pass the same file explicitly (K§9 8.1). |

Configuration in `ubproject.toml`:

```toml
[[needs.external_needs]]
json_path = "build/active/bms.needs.json"
base_url  = "<published BMS docs URL>/<version>/<chemistry>"   # links open the BMS docs
id_prefix = "BMS_"                                              # REQ_POWER_DERATING -> BMS_REQ_POWER_DERATING
css_class = "external_bms"
```

- `id_prefix` avoids ID clashes with CV `REQ_*` and makes the origin visible.
- Both tools read `[[needs.external_needs]]` with `json_path` (E-R C1); an
  **empty stub** builds cleanly (C3).
- `base_url` per chemistry: ubc accepts a `-c` override, but Sphinx ignores a
  `needs_external_needs` set in `conf.py` because `needs_from_toml` wins
  (E-R C2). **Decision for now:** one `base_url` per BMS version; per-chemistry
  URLs deferred (§11).
- ubc does **not** fill backlinks (`allocated_from`) on external needs; Sphinx
  does. The BMS-usage report therefore uses the Sphinx needtable (E-R B2).
- Chemistry-specific **values** written with the BMS `:variant:` role stay
  unresolved in the exported `content`; only fields are resolved. The BMS
  should expose them as fields (e.g. `cell_v_min`, `cell_v_max`) — BMS-side
  change, requested with §5.2 (E-R F-3).

## 6. Build, IDE and code analysis (per K§5–K§9)

### 6.1 Overview

| Topic | CV specifics |
|---|---|
| Generator | as K§6; `autoconf.cmake` additionally drives the BMS file selection (§5.3); `autoconf.h` carries `CONFIG_*` for C code, including the individual choice options (e.g. `CONFIG_VEHICLE__TYPE__BUS`) |
| CMake | `project(cv_platform C)`; `CMAKE_EXPORT_COMPILE_COMMANDS ON`; components `src/vcu`, `src/chg`, `src/eng` selected from Kconfig (K§7 6.4); `autoconf.h` on the include path |
| CMake Tools | variant picker lists the four products (§2.2), generated (K§8.1); `cmake.copyCompileCommands` → `build/compile_commands.json` |
| IDE | selecting a product switches CV docs, the BMS needs of its chemistry and the analysed code at once |
| CLI / CI | per product: CMake configure (generator, BMS file, compile DB) → `ubc` + `sphinx-build -W` → `needs.json` export |

### 6.2 Codelinks preprocessor

sphinx-codelinks can parse C/C++ **preprocessor-aware** (via libclang): markers
inside inactive `#if` / `#ifdef` / `#else` branches are dropped
(`[codelinks.projects.<x>.analyse.preprocessor]`). Together with Kconfig this
makes implementation and test needs follow the selected variant.

**Two gating layers for code:**

| Layer | Granularity | Mechanism |
|---|---|---|
| Subsystem | whole component (e.g. CHG absent in diesel) | component not built (K§7 6.4) **and** its `code_trace.rst` excluded by `variant_sources` — markers only materialise where a `src-trace` page names their codelinks project |
| Feature | code inside a built component (e.g. MCS, pantograph) | `#if CONFIG_<…>` in C; the codelinks preprocessor drops markers in inactive branches |
| Alternative implementation | same need, different code per product | the **same need ID** in `#if` / `#else`; the active product's `compile_commands.json` decides which marker becomes the need (E-R E6, C§5.1) |

**Configuration (one codelinks project per subsystem and tree):**

```toml
[codelinks]
set_local_url = true
set_remote_url = true

[codelinks.projects.chg]
remote_url_pattern = "https://github.com/PhilipPartsch/variant_demo/blob/{commit}/{path}#L{line}"

[codelinks.projects.chg.source_discover]
src_dir = "src/chg"
include = ["**/*.c", "**/*.h"]
comment_type = "cpp"

[codelinks.projects.chg.analyse.oneline_comment_style]
start_sequence = "@need:"     # "@" collides with Doxygen commands in C (ubc warning)

[codelinks.projects.chg.analyse.preprocessor]
compile_commands = "build/compile_commands.json"   # active variant (CMake Tools copy)
includes = ["build/active", "src/chg/include"]      # fallback: active autoconf.h
defines  = []                                       # fallback: only non-Kconfig macros
```

(and the same for `tests/chg` as project `chg_tests` with default type `test`.)

**How the variant reaches the preprocessor:**

| Path | Source of macros | Variant-correct? |
|---|---|---|
| `.c` file with entry in `compile_commands.json` | compiler flags of the active build + `#include "autoconf.h"` | yes — the compile DB is the active copy (`cmake.copyCompileCommands`), refreshed on every variant switch |
| File without DB entry (headers, files of components not built) | `includes` + `defines` fallback | yes for `CONFIG_*`, **if** the file includes `autoconf.h` and `build/active/autoconf.h` is the active copy |

`defines` holds only **variant-independent** macros needed to parse (e.g. a
platform macro the code expects). Variant macros come only from Kconfig as
`CONFIG_*` (coding rules: C§5).

**Setup steps:**

| Step | Action |
|---|---|
| 6.2.1 | Install `sphinx-codelinks[libclang]` in the docs toolchain. |
| 6.2.2 | CMake: `CMAKE_EXPORT_COMPILE_COMMANDS ON`; CMake Tools: `cmake.copyCompileCommands = "${workspaceFolder}/build/compile_commands.json"`. |
| 6.2.3 | Extend the active copy step (K§7 6.6) to also copy `autoconf.h` to `build/active/`; delete both on configure failure. |
| 6.2.4 | One codelinks project per subsystem and per `src`/`tests` tree; `src-trace` directives in `docs/subsystems/<x>/code_trace.rst`. |
| 6.2.6 | **Every traced `.c` file must be built by CMake**, tests included (CTest): with the preprocessor and an explicit `compile_commands.json`, codelinks skips a `.c` file without a DB entry in both tools; headers are fine (E-R F-5). |
| 6.2.5 | CLI / CI: configure the product **before** the docs build, so the compile DB exists; the `docs` target depends on configure. In CI, point `compile_commands` at the product's build dir (not the active copy). |

### 6.3 First open in VS Code (CMake Tools)

**Observed on 2026-10-08** (experiment branch, E-R D1): selecting the variant
`truck_bev_nmc` / `Debug` in the status bar did **not** configure the project —
no build directory `build/cmake/truck_bev_nmc/Debug/` was created, because no
**kit** had been selected yet. The active copies in `build/active/` still held
`truck_diesel` from an earlier command-line run, so **ubCode showed a different
product than the status bar**.

**Steps on a fresh clone:**

| # | Step | Result |
|---|---|---|
| 1 | Open the repository folder (`code .`), trust the workspace | CMake Tools, C/C++ and ubCode activate |
| 2 | `Cmd/Ctrl+Shift+P` → **CMake: Select a Kit** → pick the project kit `cv-platform` (see below) — one-time per workspace | kit stored in the workspace state |
| 3 | Select the product in the status bar — the **only** choice; the build type is always `Debug` and not offered | — |
| 4 | **CMake: Configure** (afterwards automatic on every variant switch, confirmed by E-R D1) | `build/cmake/<product>/`, `build/compile_commands.json`, `build/active/{variants.json,autoconf.h,bms.needs.json,VARIANT}` |
| 5 | Check the landing page / `build/active/VARIANT` shows the selected product | ubCode, IntelliSense and code analysis follow the status bar |
| 6 | If the ubCode **Needs Index** still shows code needs of the previous product, run **CMake: Configure** once (E-R E3: the preview follows at once, the index can lag) | code needs match the product |

**Build type.** Always `Debug`: `.vscode/cmake-variants.json` has **no
`buildType` axis**, so CMake Tools never asks for it; `cmake.configureSettings`
and the default in `CMakeLists.txt` (`if(NOT CMAKE_BUILD_TYPE) set(… Debug …)`)
fix it for the IDE, the command line and CI alike.

**Kit.** Kits are build-only (K§0 P3): any C compiler gives the same variant
data. To avoid machine-specific choices, `.vscode/cmake-kits.json` defines one
project kit without a fixed compiler path:

```json
[
  { "name": "cv-platform", "description": "Project kit: CMake picks the system C compiler", "keep": true }
]
```

On the evaluation machine the scanned kits were Apple Clang 21.0.0
(`/usr/bin/clang`, chosen), a stale Clang 17.0.0 entry for the same path, and
Homebrew GCC 16.1.0 — all would work. Prefer the project kit; if a developer
picks a scanned kit, nothing changes for the documentation.

**Settings** (`.vscode/settings.json`, committed):

| Setting | Value | Why |
|---|---|---|
| `cmake.configureOnOpen` | `true` | configure as soon as a kit is known |
| `cmake.buildDirectory` | `${workspaceFolder}/build/cmake/${variant:variant}` | one build dir per product, the same one the command line uses |
| `cmake.configureSettings` | `{ "CMAKE_BUILD_TYPE": "Debug" }` | build type fixed; `CMakeLists.txt` also defaults to `Debug` for CLI / CI |
| `cmake.copyCompileCommands` | `${workspaceFolder}/build/compile_commands.json` | codelinks preprocessor and IntelliSense follow the product |
| `cmake.generator` | `Ninja` | same generator as CLI / CI |
| `C_Cpp.default.configurationProvider` | `ms-vscode.cmake-tools` | IntelliSense from CMake |

**Keep the IDE and command-line runs apart.** `build/active/` belongs to the
product selected in the IDE. `tools/build_product.sh` / `build_all.sh` configure
other products for their own builds and would overwrite it; therefore they
**save `build/active/` at start and restore it at the end** (or run with
`-DCV_UPDATE_ACTIVE=OFF` and per-product paths, decided in implementation).
The landing page shows `<{ var.meta.product }>`, so a mismatch is visible at a
glance.

## 7. AI workflow setup

### 7.1 What is reused from the BMS

| BMS element | CV platform |
|---|---|
| `[workflow]` stages, `orphan_exempt_types` | same structure, routes adapted to §3 (§7.2) |
| `[quality]` + criteria files | reused + `variant_consistency`; allocation criteria folded into `arch.toml` (§7.3) |
| skills / agents (`draft-*`, `review-*`, `record-decision`, `change-request`, `drive-workflow`, `recover-*`, …) | installed with `ubc agent install --detect` into `.claude/skills/`, `.agents/skills/`, `.github/agents/`; plus the project skill `draft-allocation` in the same three locations (§7.4) |
| `.pharaoh/verdicts/<ID>.json` | same, at the repository root |
| `.mcp.json` → `ubc serve mcp` | same, `--default-config ubproject.toml` |

### 7.2 Workflow stages

Streams are the subsystems: `vcu`, `chg`, `eng`, `bms`. Vehicle-level stages
are global.

| Stage | Produces | Depends on | Author skill | Review skill | Trace (min 1, `both` unless noted) | Route |
|---|---|---|---|---|---|---|
| `user_stories` | user_story | — | — | `review-feat` | — | single, `docs/vehicle/user_stories.rst` |
| `reqs` | req | user_stories | `draft-requirement` | `review-requirement` | `traces_to` → user_story | single, `docs/vehicle/requirements.rst` |
| `archs` | arch | reqs | `draft-arch` | `review-arch` | `satisfies` → req | per-root, `docs/subsystems/{stream}/architecture.rst` (`vcu`, `chg`, `eng`) |
| **`bms_allocation`** | arch | reqs | **`draft-allocation`** (project skill) | `review-arch` | `satisfies` → req; `allocates` → req (external `BMS_REQ_*`, outgoing) | single, `docs/subsystems/bms/architecture.rst` |
| `swreqs` | swreq | archs | `draft-requirement` | `review-requirement` | `refines` → arch | per-root, `docs/subsystems/{stream}/software_requirements.rst` |
| `code` | impl | swreqs | `draft-impl` | — | `implements` → swreq | global, `src` |
| `tests` | test | code | `draft-test` | — | `verifies` → swreq | global, `tests` |
| `test_results` (optional) | test_result | — | — (importer) | — | `results_for` → test (outgoing) | single, `docs/_global/test_results.rst` |
| `risks` (optional) | risk | — | — | — | `mitigates` → req (outgoing) | single, `docs/_global/risks.rst` |
| `decisions` (optional) | decision | — | `record-decision` | `review-decision` | `affects` → arch (outgoing) | single, `docs/_global/decisions.rst` |

`orphan_exempt_types = ["user_story", "req", "arch", "swreq", "gap"]`, as in
the BMS, and **`exempt_status = ["imported"]`** so that imported BMS needs are
not counted as CV work (without it: 40 review gaps and a trace gap on `BMS_*`
needs, E-R F1).

Stage `authoring` texts are taken from the BMS and extended with the authoring
rules of C§6.2 (e.g. archs: "… place variant-specific elements in the subsystem
folder of their variant, gate any other variant-specific content with the
named variants of §2.3").

Two stages producing the same type with different routes, and a trace entry
targeting external needs, pass `ubc agent config-validate` (E-R F1).
**Author skills resolve per stage**, **review skills per need type** (E-R F4):
with two stages producing `arch`, one review skill reviews all `arch` needs.
Therefore `bms_allocation` gets its own author skill `draft-allocation` and is
reviewed by `review-arch`, whose criteria file `arch.toml` contains the
allocation criteria. A separate review skill would require a dedicated need
type (`bms_ifc`).

### 7.3 Quality criteria (`metamodel/quality/`)

| File | Types | Criteria |
|---|---|---|
| `requirement.toml` | req, swreq | BMS criteria (parent_fit, atomicity, verifiability, unambiguity, comprehensibility, feasibility) **+ variant_consistency** |
| `arch.toml` | arch | BMS criteria (parent_fit, design_clarity, completeness, consistency, implementability) **+ variant_consistency** |
| `feat.toml` | user_story | BMS criteria (parent_fit, single_user_capability, user_observable, no_mechanism_leak, naming_clarity) **+ variant_consistency** |
| `decision.toml` | decision | BMS criteria (context_present required, …) |
| ~~`allocation.toml`~~ → folded into `arch.toml` (quality criteria are per type; `bms_allocation` reuses `review-arch`, E-R F4) | arch in `bms_allocation` | parent_fit, **interface_only** (targets are BMS interface needs), **allocation_complete** (every BMS-relevant aspect of the CV req is covered by an allocated BMS req), **no_value_copy** (BMS values referenced, not restated), variant_consistency |

**`variant_consistency`** (new, all types): the need is gated by the **same or
a stronger** condition than its parent; variant-specific content uses the
named variants / folders of §2.3; no build-type or kit conditions (K§0 P3).

`[quality.required]`: `parent_fit = 1` (as in BMS) and `variant_consistency = 1`.

### 7.4 Agents, skills and tools

| Item | Action |
|---|---|
| Install | `ubc agent install --detect` → `.agents/skills/`, `.github/agents/`, `.pharaoh/agent/` |
| MCP | `.mcp.json`: `ubc serve mcp --default-config ubproject.toml` |
| Project skill `draft-allocation` | authors the BMS black-box arch elements (§7.2). Like every skill it exists in **three host locations with identical content**: `.claude/skills/draft-allocation/SKILL.md` (Claude Code — the copy `ubc agent doctor` checks), `.agents/skills/draft-allocation/SKILL.md` (agents-standard hosts), `.github/agents/draft-allocation.agent.md` (GitHub Copilot). Not in the install manifest, so `ubc agent update` does not touch it |
| Skill mirror check | `tools/check_skill_mirrors.py`: every skill identical in all three locations; doctor only checks mirrors of manifest-owned skills (E-R F-12). Runs in `build_all.sh` and CI |
| Review briefings | `ubc agent review-brief` also lists imported `BMS_*` needs (ignores `exempt_status`); the gate `verdict-check` excludes them. Reviewers skip `BMS_*` (E-R F-13) |
| MCP context | `ubc serve mcp` exposes the imported `BMS_*` needs of the active product (`query_cypher`, E-R F3) |
| Existing `recover-*` skills | available for recovering swreqs / archs from existing C code |
| `change-request` | when a BMS pin update changes interface needs, cascade from the affected `BMS_*` needs down the CV V-model |
| `drive-workflow` / `ubc agent next` | as in BMS, plus the per-product gate of §7.5 |

### 7.5 Variant-aware gates

The BMS workflow and schemas are variant-agnostic. In a product line,
"every swreq is implemented" is a **per-product** statement — a CHG swreq is
legitimately absent in the diesel truck. The setup provides:

1. **Active variant for the agent:** `ubc agent next` and `ubc check` evaluate
   the variant selected in CMake Tools (`build/active/variants.json`).
2. **Per-product completion:** the gates run once per product **after
   configuring that product** (`tools/build_product.sh <product>`, CI matrix).
   A `-c "needs.variant_data_file = …"` override alone is not enough: it
   switches docs and BMS import, but code analysis keeps the active
   `compile_commands.json`, and overriding nested codelinks settings with `-c`
   replaces the whole project table (E-R F2).
5. **Imported needs exempt:** `exempt_status = ["imported"]` (§7.2).
3. **Product-tagged evidence:** the importers write `product` on gaps and test
   results and run per product in CI.
4. **No blanket exemptions:** lint ignores stay narrow (by need id) and, if
   needed, per product — never a suppression of a whole rule.

The matching **authoring** rules for agents and humans are in C§6.2.

## 8. Local build entry points

One command per product, used by developers **and** later by CI (A§), so local
and CI results cannot drift apart:

| Entry point | Does |
|---|---|
| `tools/build_product.sh <product>` | CMake configure into `build/<product>/` (generator, BMS selection, compile DB) → `ubc check` → `ubc build needs` → **ubCode HTML** (`ubc build html`) into `build/site/<product>/ubcode/` → **sphinx-needs HTML** (`docs` target, `sphinx-build -W`) into `build/site/<product>/sphinx/` → both `needs.json` into `build/site/<product>/` |
| `tools/build_all.sh` | `build_product.sh` for every `configs/*_defconfig`, then the once-per-repo checks below; saves and restores `build/active/` so the IDE keeps its product (§6.3) |
| CMake targets `docs`, `docs_ubc` | the two HTML builds of the active product (for CMake Tools) |
| `ubc script build-all` | alias in `ubproject.toml` `[scripts]` |

Once-per-repo checks (in `build_all.sh`):

- drift check `kconfig2variants --all --vscode --check` (K§6);
- consistency checks of M§8 / M§9, including the **alternatives check** (every
  need ID defined in complementary `if` blocks exists in every product, M§8);
- BMS pin check: `third_party/bms/<version>` matches the version in
  `ubproject.toml` / `cmake/bms.cmake`;
- skill mirror check `tools/check_skill_mirrors.py` (§7.4).

The output layout `build/site/<product>/{sphinx,ubcode}/` is exactly the
folder layout of the `gh-pages` branch, one folder per variant (A§3.1).

## 9. Ownership and governance

| Artifact | Owner | Review rule |
|---|---|---|
| CV Kconfig, defconfigs | CV platform team | per K§12 |
| BMS interface needs, BMS releases | BMS team | interface changes announced; CV updates the pin explicitly |
| BMS version pin in CV | CV platform team | a pin update is a reviewed change with variant diff (C§7) |
| Metamodel (`[[needs.types]]`, links, fields, `metamodel/schemas.json`) | CV metamodel owner | changes aligned with the BMS metamodel; deviations listed in §4.3 |
| `[workflow]`, `metamodel/quality/`, skills | CV metamodel owner | new / changed criteria reviewed like code; verdicts in `.pharaoh/` are committed |

## 10. Rollout

1. **Evaluation done:** exit criteria of [01-evaluation.md](01-evaluation.md)
   met; its decisions are applied to this plan.
2. **BMS release artifacts:** per-chemistry `needs.json` + HTML published,
   interface needs tagged (§5.2).
3. **GitHub settings** R7, R8, R11, R13 (§3.4); R14 goes into the first setup
   commit (R3 licence: done).
4. **Repository skeleton:** tag `pre-cv-platform` on `main`, migrate the
   existing content (§3.2), folder structure and skeleton files (§3), Kconfig
   and the four defconfigs (§2), generator, CMake + CMake Tools (K§ phases 1–7).
5. **Metamodel** (§4) and variant hooks (§2.3).
6. **BMS import** (§5.3) — D4.
7. **Code analysis** (§6.2) — D5.
8. **AI workflow** install, stages, quality, new skills (§7) — D6.
9. **Local build entry points** (§8) — D7.
10. **Commit and push** to this repository — D8:
   1. Remote: the existing `origin`
      (`https://github.com/PhilipPartsch/variant_demo`); no new repository.
      Before the first restructuring commit, tag the current `main` as
      `pre-cv-platform` and push the tag.
   2. Pre-push check:
      - `build/` and other generated outputs are ignored (`git status` shows
        none of them);
      - the committed generated files are up to date
        (`kconfig2variants --all --vscode --check`);
      - pinned BMS artifacts (`third_party/bms/<version>/`), `.pharaoh/`,
        `metamodel/` and `.vscode/` are included;
      - `.agents/plans/` stays untracked (gitignored);
      - no credentials or local paths in `ubproject.toml`, `.mcp.json` or
        `.vscode/settings.json`;
      - no AI attribution trailers in commit messages
        (`git log --format='%(trailers)' origin/main..`);
      - no `eval/*` branch is pushed (the repository stays clean, §3.4).
   3. Work on a branch (`setup/cv-platform`), commit in logical steps (skeleton,
      metamodel, BMS import, code analysis, AI workflow, entry points), push with
      `git push -u origin setup/cv-platform`.
   4. Open a pull request to `main` of `PhilipPartsch/variant_demo`; merge when
      `tools/build_all.sh` passes for all four products (CI follows with A§).
   5. Merged work branches are not deleted automatically (R11 off); delete them manually when no longer needed.
   6. Optionally tag the merge commit (`setup-done`) as the starting point of
      the content plan.
11. Handover: start [03-mechanism-evaluation.md](03-mechanism-evaluation.md) (side branch) and [04-content.md](04-content.md).

## 11. Open points and risks

Answered by plan 1 (details in [01-evaluation-result.md](01-evaluation-result.md)).
Still open:

- **IDE behaviour** (E-R U3): CMake Tools reconfigures on a variant switch
  (D1), ubCode re-indexes changed active copies (D2) and re-analyses code (E3),
  what a missing active file looks like (D3), and the editor diagnostics for
  alternatives, `if` and external-need hovers (A2, A3, C1).
- **ubc without licence in CI** (G3) — needs an OSI licence file in the
  repository (E-R U1) and the CI dry run (U2).
- **libclang on Linux / Windows** (E5) — Linux in the CI dry run.
- **Per-chemistry `base_url`** for external needs (C2) — deferred.
- **ubc backlinks on external needs** (B2) — feedback to useblocks.
- **sphinx-codelinks CSS path** on source pages (`_static/_static/…`, E-R F-7) —
  cosmetic, report upstream.
- **Silent empty variants:** the active copies (`variants.json`,
  `bms.needs.json`, `autoconf.h`) must exist before ubCode indexes —
  `cmake.configureOnOpen` and the delete-on-failure rule (K§7 6.6) cover this.
