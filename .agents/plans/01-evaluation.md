# Plan 1: Evaluation of the open questions

Step 1 of the [roadmap](00-roadmap.md). Answers every open **Verify** question
of the plans **before** the basic setup is built, with throw-away experiments
that contain only the handful of elements each question needs. The answers
decide configuration details of the basic setup (`B§`, plan 2) and of all
later steps.

Referenced: [02-basic-setup.md](02-basic-setup.md) (`B§`),
[04-content.md](04-content.md) (`C§`), [06-automation.md](06-automation.md)
(`A§`), [variant-mechanisms.md](variant-mechanisms.md) (`M§`),
[kconfig-variant-configuration.md](kconfig-variant-configuration.md) (`K§`).

Only released, ubCode-supported directives are used; nothing is invented for
the experiments.

Difference to step 3 ([03-mechanism-evaluation.md](03-mechanism-evaluation.md)):
this step asks **"can the tools do it, and how?"** in a scratch area; step 3
proves **"does our committed basic setup do it?"** for every mechanism.

## 0. Goals

1. Turn every **Verify** point into a recorded answer: **works**, **works with
   workaround**, or **blocked**.
2. Find blockers **early** — especially where ubc / ubCode and Sphinx could
   disagree.
3. Feed every answer back into the plan that raised it (§5).

Non-goals: content, polish, CI. The experiment branch is throw-away.

## 1. Experiment setup

### 1.1 Where

A throw-away branch `eval/open-questions` **in this repository**
(`PhilipPartsch/variant_demo`), branched from the current `main`. Its files
follow the folder layout planned in B§3 so that working configuration can be
copied into the basic setup unchanged. It stays **local**: it is never pushed
and never merged (the repository stays clean).

Questions that can only be answered by GitHub Actions (G3, G4, E5 on Linux)
are therefore **not** tested from this branch; they are verified by the first
CI run on `main` (A§1.1).

Experiments are added in stages, cheapest first, so blockers show up early:

| Stage | Adds | Answers |
|---|---|---|
| 1 — docs only | hand-written `variants/<product>.json`, `ubproject.toml`, a few `.rst` pages, BMS `needs.json` exports | groups A, B, C |
| 2 — configuration | minimal Kconfig, generator, CMake, `.vscode` | group D |
| 3 — code | two C files, one header, codelinks preprocessor | group E |
| 4 — AI workflow | `[workflow]` with three stages | group F |
| 5 — automation | local only: ubCode HTML per product, local compare page (G1, G2, G5); G3 / G4 / E5-Linux move to the first CI run on `main` (A§1.1) | group G |

### 1.2 Elements

Only what the experiments in §3 need:

| Area | Minimal element | Used by |
|---|---|---|
| Kconfig | `VEHICLE__TYPE` (truck/bus), `POWERTRAIN__TYPE` (diesel/bev), `BMS__CHEMISTRY` (nmc/lfp, depends on bev), `CHARGING__MCS` (bool, depends on bev) | A, D, E |
| Products | `truck_diesel`, `truck_bev_nmc` (MCS), `bus_bev_lfp` | all |
| Generator | minimal `kconfig2variants.py` (nesting, choices → strings, disabled → `false`, `var.meta.product`) | A, D |
| CMake | configure → generator → active copies (`variants.json`, `autoconf.h`, `bms.needs.json`); components `vcu` (always), `chg` (BEV) | D, E |
| `.vscode` | hand-written `cmake-variants.json` with the three products, `settings.json` (B§6) | D |
| Metamodel | types `user_story`, `req`, `arch`, `swreq`, `impl`, `test`; links `traces_to`, `satisfies`, `refines`, `implements`, `verifies`, `allocates`; fields `status`, `value` | all |
| Schemas | 2 rules: `allocates` target prefix, `allocates` target tag `interface` | C |
| Workflow | stages `reqs`, `archs`, `bms_allocation` | F |
| BMS data | `needs.json` for NMC and LFP exported locally from `rollout-demo-bms` (scripts `needs`, `needs:lfp`), plus an empty stub | B, C |

### 1.3 Documentation elements

| File | Elements |
|---|---|
| `docs/index.rst` | `<{ var.meta.product }>`, `<{ var.bms.chemistry }>` |
| `docs/vehicle/requirements.rst` | `REQ_POWER` with field `value: <<[bus]: 250 kW, 450 kW>>`; `REQ_MCS` inside `if mcs`; `REQ_ENERGY_SOURCE` as two complementary `if` blocks with the same ID |
| `docs/subsystems/vcu/architecture.rst` | `ARCH_VCU_POWER` with `allocates: <<[bev]: BMS_REQ_POWER_DERATING>>` (link variant to an external need) |
| `docs/subsystems/chg/architecture.rst` | `ARCH_CHG_INLET` (file BEV-only via `variant_sources`) |
| `docs/subsystems/bms/architecture.rst` | `ARCH_BMS_LIMITS` allocating two BMS needs, one tagged `interface`, one not (negative case) |
| `docs/subsystems/{vcu,chg}/code_trace.rst` | `src-trace` for the codelinks projects |
| `docs/subsystems/bms/integration.rst` | needtable of `BMS_*` needs |

### 1.4 Code elements

| File | Content |
|---|---|
| `src/vcu/energy.c` | `#if CONFIG_POWERTRAIN__TYPE__BEV` / `#else` with one marker each |
| `src/vcu/energy.h` | one marker inside `#if CONFIG_CHARGING__MCS` (header fallback path) |
| `src/chg/mcs.c` | marker inside `#if CONFIG_CHARGING__MCS` (component built only for BEV) |
| `tests/vcu/test_energy.c` | one test marker |

## 2. How each experiment is run

For every experiment:

1. Build the minimal setup for **each** product, with **both** toolchains:
   `ubc build needs` and `sphinx-build -W` (with sphinx-mounts and
   sphinx-codelinks); compare the per-product `needs.json`.
2. Where the IDE matters, check in VS Code with CMake Tools + ubCode.
3. Record: tool versions, observation, answer (works / workaround / blocked),
   decision, plan sections to update.

Timebox: half a day per experiment group in §3; a blocked experiment stops only its group.

## 3. Experiments

Priority: **P1** = blocks the basic setup, **P2** = blocks content, demo or
automation, **P3** = can be decided later.

### Group A — variant data and conditions (ubc vs. Sphinx)

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| A1 | Which variant-data location do sphinx-needs, ubc and sphinx-mounts all read: `[variants] data_file` or `[needs] variant_data_file`? | M§1.4 | Kconfig, generator, `variant_sources` | one location works for all three, no `mounts.variant_data_location` warning | keep `[needs]` and accept sphinx-mounts' legacy path | P1 |
| A2 | Does **ubc / ubCode** honour `if`: content of a false block is not indexed? | M§5, B§2.3 | `REQ_MCS` | `REQ_MCS` absent in ubc for `truck_diesel` and `bus_bev_lfp`, present for `truck_bev_nmc`; same in Sphinx | file variants instead of `if` for need-bearing content | **P1** |
| A3 | **Complementary `if` blocks with the same ID**: does ubc / ubCode report a duplicate ID (if it indexes both branches)? | M§5.1 | `REQ_ENERGY_SOURCE` | exactly one `REQ_ENERGY_SOURCE` per product in ubc and Sphinx, no duplicate warning in the IDE | different IDs per alternative + a common parent; or file variants | **P1** |
| A4 | `<<[...]>>` with named variants and `<{ var.* }>`: identical values in ubc and Sphinx? | M§3 | `REQ_POWER.value`, index page | same values per product | inline conditions instead of named variants | P1 |
| A5 | `variant_sources` parity: same document set in ubc and Sphinx (+ sphinx-mounts); toctree reference to an excluded file downgraded to INFO with `-W`? | M§6 | `subsystems/chg/**` | identical docnames; `-W` passes for `truck_diesel` | `if` around toctree entries | P1 |
| A6 | Disabled symbols as `false` / `""` / `0`: same evaluation in needs and mounts; `var.x == True` accepted, bare `var.x` rejected by sphinx-mounts? | K§4.6, K§4.2 | `BMS__CHEMISTRY` in `truck_diesel` | no `variant_rule_unevaluable`; same results in both tools | omit disabled symbols and guard every condition | P2 |
| A7 | Minimum versions of sphinx-needs / ubc / sphinx-mounts / sphinx-codelinks for everything above; `choose` release status | M§11, C§8.2 | all | versions pinned; `choose` release tracked | — | P1 |

### Group B — links

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| B1 | Link variant syntax with `parse_variants` on a link type, single and multiple target IDs | M§4, C§11 | `ARCH_VCU_POWER.allocates` | link present only in BEV products; works with 2 IDs | wrap the whole need in `if bev` | P2 |
| B2 | Links to **external, prefixed** needs (`BMS_REQ_*`) resolve in ubc and Sphinx, incl. incoming `allocated_from` on the external need | B§5.3 | `ARCH_BMS_LIMITS` | no dangling link; backlink visible in Sphinx | link only in one direction / report via needtable | P1 |

### Group C — external needs (BMS import)

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| C1 | Does ubc / ubCode read `[[needs.external_needs]]` with `json_path`? | B§5.3 | BMS `needs.json` | `BMS_*` IDs resolve and hover in the IDE | generate a CV-side `needs.json` import via `needimport` (**Verify** ubc support) | **P1** |
| C2 | Can `base_url` differ per product (chemistry / version)? | B§5.3 | two chemistries | links open the right BMS docs per product | generate the `[[needs.external_needs]]` block at configure time | P3 |
| C3 | Is an **empty stub** `needs.json` accepted without warnings? | B§5.3 | `truck_diesel` | clean build in both tools | minimal stub with one hidden placeholder need | P1 |
| C4 | Do CV schemas skip external needs with `select` on `is_external == False`? | B§4.4 | schemas | no schema findings on `BMS_*` needs | filter by id prefix | P2 |
| C5 | Can a schema check a **property of the link target** (tag `interface`)? | B§4.4 | negative allocation | the non-interface allocation is reported | CI script over `needs.json` | P3 |

### Group D — CMake Tools and IDE

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| D1 | Does CMake Tools reconfigure automatically on a variant switch (variants mode)? | K§8.3 | `.vscode`, CMake | switching updates `build/active/*` without manual configure | task "Select product" that configures | P1 |
| D2 | Does ubCode re-index when `build/active/variants.json` / `bms.needs.json` change outside the editor? | K§8.3 | active copies | values in the IDE follow the switch within seconds | post-configure task triggering a reload | P1 |
| D3 | What does ubCode show with a **missing** active file (fresh clone, failed configure)? | B§11, K§7 6.6 | delete `build/active/*` | visible problem (warning or empty marker), not silent | `cmake.configureOnOpen` + sanity check | P2 |

### Group E — code analysis (codelinks preprocessor)

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| E1 | Does ubc / ubCode support `analyse.preprocessor` (libclang) like sphinx-codelinks? | B§6.2 | `energy.c` | only the active branch's marker per product, in IDE and Sphinx | gate markers by file (subsystem layer only) | **P1** |
| E2 | Header fallback: `includes = ["build/active", …]` evaluates `#if CONFIG_*` in `energy.h` | B§6.2 | `energy.h` | marker follows `CHARGING__MCS` | no markers in headers (rule C§5.5) | P2 |
| E3 | Does ubCode re-analyse after `build/compile_commands.json` changes on a switch? | B§11 | switch products | markers follow the switch | manual reload task | P2 |
| E4 | Unbuilt component (`chg` in `truck_diesel`): markers excluded because `code_trace.rst` is excluded by `variant_sources` | B§6.2 | `src/chg/mcs.c` | no `IMPL_*` from `chg` in `truck_diesel` | per-subsystem `src_dir` switched at configure time | P1 |
| E5 | libclang available on macOS, Linux, Windows and in the CI image | B§11 | install | `sphinx-codelinks[libclang]` works on all | pin a libclang wheel / container image | P2 |

### Group F — AI workflow

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| F1 | Two stages producing `arch` with different routes (`archs`, `bms_allocation`); a trace entry targeting an **external** need | B§7.2 | workflow | `ubc agent next` orders the stages correctly; gate counts `allocates` to `BMS_REQ_*` | type `bms_ifc` (B§7.2) | **P1** |
| F2 | Do `ubc agent next` / `ubc check` accept a per-product variant override (`-c "needs.variant_data_file = …"`)? | B§7.5 | 3 products | per-product gate results differ as expected | run gates only in CI per product | P1 |
| F3 | Does the MCP server (`ubc serve mcp`) expose imported `BMS_*` needs to agents? | B§11 | BMS import | agent can read `BMS_REQ_POWER_DERATING` via MCP | pass the BMS `needs.json` to the skill as a file | P2 |
| F4 | Can project-specific skills (`draft-allocation`, `review-allocation`) be registered next to the installed ones and referenced from a stage? | B§7.4 | workflow | stage `bms_allocation` resolves its skills | reuse `draft-arch` / `review-arch` with an allocation-specific `authoring` text | P2 |

### Group G — automation and publishing (input for plan 6)

| ID | Question | Source | Elements | Pass criterion | Fallback | Prio |
|---|---|---|---|---|---|---|
| G1 | Does `ubc build html` accept the per-product variant override (`-c "needs.variant_data_file = …"`) and the active BMS import, so it renders each product? | A§ | 3 products | one ubCode HTML per product with the right values | configure each product in its own CI job so `build/active/*` is correct | P2 |
| G2 | Is the ubCode HTML output a static site that can be served from GitHub Pages under a sub-path (`/<product>/ubcode/`)? | A§ | one product | pages render, relative links work under a sub-path | post-process paths / one Pages site per output | P2 |
| G3 | ubc in GitHub Actions **without license secrets**: this repository is open source and needs no ubCode license (unlike the private BMS repo, whose CI uses `UBCODE_LICENSE_KEY` / `UBCODE_LICENSE_USER`) | A§ | minimal workflow on `eval/open-questions`: `useblocks/ubc-action` without license inputs → `ubc --version`, `ubc check`, `ubc build html` | all three succeed in CI, also on a pull request | add license secrets as in the BMS demo | **P1** |
| G4 | GitHub Pages for `PhilipPartsch/variant_demo` served from the **`gh-pages` branch** (decided), one folder per variant; does a CI push with `GITHUB_TOKEN` work, and are Sphinx `_static/` assets served with `.nojekyll`? | A§ | workflow dry run writing `<product>/` folders to `gh-pages` | pages of two variants reachable under `/<product>/sphinx/` and `/<product>/ubcode/` | Pages source "GitHub Actions" (artifact deploy) | P2 |
| G5 | Can sphinx-needs and ubCode HTML be shown **side by side** (iframes on one compare page) without cross-origin or framing problems? | A§ | compare page | both panes load and scroll independently | two links per product instead of iframes | P3 |

## 4. Execution order

1. **P1 blockers first**, in stage order (§1.1): A7 (versions) → G3 (ubc in CI without license) → A1 → A2 →
   A3 → C1 → B2 → C3 → A4 → A5 → D1 → D2 → E1 → E4 → F1 → F2.
2. Then P2, then P3.
3. Stop and decide after A2 / A3 / C1 / E1 / F1: if one of them is
   **blocked**, the affected design (alternatives, BMS import, code variants,
   allocation stage) switches to its fallback **before** continuing.

## 5. Results and plan updates

Results are recorded in a table appended to this plan:

| ID | Tool versions | Answer | Decision | Plans updated |
|---|---|---|---|---|
| A2 | … | works / workaround / blocked | … | M§5, B§2.3, … |

Each answer is written back:

| Outcome | Action |
|---|---|
| works | remove the **Verify** marker in the source plan; note the minimum version |
| works with workaround | replace the open point with the workaround in the source plan |
| blocked | switch the source plan to the fallback; add a risk if the demo is affected |

The working configuration of the experiment branch (Kconfig, generator,
`ubproject.toml` snippets, CMake, `.vscode`, workflow snippets) is copied into
the basic setup (plan 2) and the automation (plan 6).

## 6. Exit criteria

- All P1 experiments answered; no P1 left **blocked** without an accepted fallback.
- All P2 experiments answered, or explicitly deferred with an owner.
- Versions pinned (A7).
- The **Verify** markers in M, K and plans 2–6 are either removed or point to a
  recorded P3 deferral.
- Go / no-go for plan 2 (basic setup).
