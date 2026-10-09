# Plan 3: Evaluation of the variant mechanisms on the basic setup

Step 3 of the [roadmap](00-roadmap.md). Proves **every variant mechanism** with
**bare-minimum generic elements** on top of the committed basic setup
([02-basic-setup.md](02-basic-setup.md), `B§`). The elements live on a side
branch; **bugs found in the basic setup are fixed on `main`**.

Referenced: [01-evaluation.md](01-evaluation.md) (`E§`),
[04-content.md](04-content.md) (`C§`), [05-test.md](05-test.md) (`T§`),
[06-automation.md](06-automation.md) (`A§`),
[variant-mechanisms.md](variant-mechanisms.md) (`M§`),
[kconfig-variant-configuration.md](kconfig-variant-configuration.md) (`K§`).

Difference to plan 1: plan 1 asked "can the tools do it, and how?" in a
scratch area. This plan asks **"does our committed setup do it, end to end,
for every product and both toolchains?"**

## 0. Goals

1. Each mechanism of M§2, plus Kconfig, CMake Tools, BMS import, code analysis
   and the per-product AI-workflow gate, demonstrated with one or two generic
   elements.
2. Expected result per product written down **before** building, then checked
   in **ubc and Sphinx**.
3. Every defect found is classified and fixed where it belongs — basic setup
   defects on `main`.
4. The patterns that work become the templates for the content (C§) and the
   expectations for the tests (T§).

Non-goals: real product content, test automation (T§, A§).

## 1. Branch and workflow

| Item | Rule |
|---|---|
| Branch | `eval/mechanisms`, created from `main` after plan 2 is merged |
| Commits | one commit per mechanism (`eval: V05 alternatives`), so each can be inspected and reverted alone |
| Merge | never merged to `main` |
| Sync | after every fix on `main`: `git rebase main` (local; nothing to push) |
| Sharing | **local only** — never pushed (the repository stays clean); results are shared through the findings log (§5) and the fixes merged on `main` |

### 1.1 Finding → fix flow

```
run V-item ──► result ≠ expectation ──► classify
                                          │
   ┌──────────────────────┬───────────────┼────────────────────┬─────────────────────┐
   ▼                      ▼               ▼                    ▼                     ▼
 basic-setup bug       tool bug        plan error          eval element error   expectation wrong
 fix/* branch from     report upstream  update M / K / B     fix on               fix the expectation
 main → PR → merge     (useblocks);     and, if needed,      eval/mechanisms      (record why)
 → rebase eval branch  workaround on    the setup on main
                       main via fix/*
```

Every finding is logged in §5 with its class, fix location and commit / PR.

**Tool findings → plan 99:** every bug or gap found in a useblocks tool (ubc / ubCode, Pharaoh, Sphinx-Needs, Sphinx-Codelinks, sphinx-mounts, ubc-action, ubTrace, ubConnect, Sphinx-Test-Reports) is added to [99-tool-bugs.md](99-tool-bugs.md) in the same session: summary, marker `branch@commit` + file:line on a pushed branch, input, wrong output, workaround, two solutions.

## 2. Generic elements

Product-neutral content ("generic element demonstrating …"), using the Kconfig
symbols of `main` (B§2). IDs follow the metamodel prefixes with `EVAL` in the
name, so they pass the schemas. Location on the branch:

```
docs/eval/                     index.rst (in the root toctree, branch only)
  mechanisms.rst               V01–V07
  bev_only/page.rst            V08 (file variant)
eval/bundle/                   V09 (tiny external bundle for a mount)
src/vcu/eval_markers.c         V12
src/vcu/include/vcu/eval.h     V12 (header path)
src/chg/eval_chg.c             V13
```

Branch-only configuration additions (in `ubproject.toml` on the branch):
one `variant_sources` rule for `docs/eval/bev_only/**`, one `[[source.mounts]]`
entry for `eval/bundle`, a user story `US_EVAL` as trace root.

## 3. Evaluation items

Products (B§2.2): **D** = `truck_diesel_eu`, **N** = `truck_bev_nmc_eu`
(MCS), **B** = `bus_bev_lfp_eu` (pantograph), **A** = `truck_bev_lfp_na`.

### 3.1 Documentation mechanisms

| ID | Mechanism | Generic element | Expected D / N / B / A | Ref |
|---|---|---|---|---|
| V01 | Field `<<>>` with named variant | `REQ_EVAL_FIELD.value: <<bus: bus-value, truck-value>>` | truck / truck / bus / truck | M§3 |
| V02 | Field `<<>>` with inline condition | `REQ_EVAL_INLINE.value: <<[var.hv.voltage == "v800"]: 800, 400>>`; diesel has `hv.voltage` disabled | 400 / 800 / 400 / 800 | M§3, K§4.6 |
| V03 | Data reference `<{ }>` | `REQ_EVAL_DATA` text: `<{ var.meta.product }>`, `<{ var.bms.chemistry }>` | product name each; chemistry "" / nmc / lfp / lfp | M§3 |
| V04 | `if` | `REQ_EVAL_IF` inside `.. if:: var.charging.mcs == True` (named variants are not resolved by `if`, §5 #1) | – / ✓ / – / – | M§5 |
| V05 | Alternatives (complementary `if`, same ID) | `REQ_EVAL_ALT` in three blocks: MCS / pantograph / otherwise | otherwise / MCS / pantograph / otherwise | M§5.1 |
| V06 | `choose` (**release-gated**) | `REQ_EVAL_CHOOSE`, same three branches as V05 | same as V05 — skipped until the pinned sphinx-needs has `choose` | M§5, M§5.2 |
| V07 | Link variant | `ARCH_EVAL_LINK` `allocates: <<bev: BMS_REQ_POWER_DERATING>>` | no link / link / link / link | M§4 |
| V08 | File variant (`variant_sources`) | `docs/eval/bev_only/page.rst` with `REQ_EVAL_BEV_FILE` | – / ✓ / ✓ / ✓; toctree entry INFO, `-W` passes | M§6 |
| V09 | Mount with `if` | `eval/bundle/` mounted at `_mounted/eval`, `if = "var.vehicle.type == 'bus'"` | – / – / ✓ / – | M§7 |
| V10 | External needs (BMS import) | needtable of `BMS_REQ_CELL_VOLTAGE_LIMITS` | none / NMC values / LFP values / LFP values | B§5 |
| V11 | Dependency rule | `REQ_EVAL_CHILD` gated `if mcs`, `traces_to` `US_EVAL` (ungated) — valid; temporary negative probe: ungated link **to** `REQ_EVAL_IF` | valid build in all; probe fails D, B, A with dangling link | M§8.1 |

### 3.2 Configuration, build and IDE

| ID | Mechanism | Check | Expected | Ref |
|---|---|---|---|---|
| V14 | Kconfig generator | generated `variants/*.json`: nesting, choices as strings, disabled symbols `false` / `""`, `var.meta.product` | matches K§4 for all four products; drift check clean | K§4, K§6 |
| V15 | Kconfig constraints | temporary probe: `CHARGING__MCS=y` in the bus defconfig with `HV__VOLTAGE__V400` | generator fails with the dependency message | K§6 |
| V16 | CMake Tools switching | switch D → N → B → A in the status bar | `build/active/*` and the ubCode view follow each switch | K§8, E§ D1/D2 |
| V17 | Build settings outside the variant model | CMake Tools offers only the product (no build type); every build dir has `CMAKE_BUILD_TYPE=Debug`; same product built with another kit (e.g. Clang vs GCC) | identical `variants.json` and `needs.json` | K§0 P3 |
| V18 | Local entry points | `tools/build_all.sh` | all products, both HTML outputs in `build/site/<product>/` | B§8 |

### 3.3 Code

| ID | Mechanism | Generic element | Expected D / N / B / A | Ref |
|---|---|---|---|---|
| V12 | Codelinks preprocessor | `eval_markers.c`: `IMPL_EVAL_BEV` in `#if CONFIG_POWERTRAIN__TYPE__BEV`, `IMPL_EVAL_DIESEL` in `#else`, `IMPL_EVAL_MCS` in `#if CONFIG_CHARGING__MCS`; header marker `IMPL_EVAL_HDR` in `#if CONFIG_CHARGING__MCS` | DIESEL / BEV+MCS+HDR / BEV / BEV | B§6.2 |
| V12b | Same need ID, two implementations | `eval_markers.c`: `IMPL_EVAL_ENERGY` in **both** `#if CONFIG_POWERTRAIN__TYPE__BEV` and `#else`, implementing one ungated `SWREQ_EVAL_ENERGY`; switched by `compile_commands.json`. Temporary negative probe: remove `#if` / `#else` | exactly one `IMPL_EVAL_ENERGY` per product — D from `#else` (fuel), N / B / A from `#if` (SoC), different source line; probe: duplicate ID in ubc and Sphinx | B§6.2, C§5.1, E-R E6 |
| V13 | Component selection | `eval_chg.c` with `IMPL_EVAL_CHG` (CHG built for BEV only, `code_trace.rst` excluded for diesel) | – / ✓ / ✓ / ✓ | B§6.2 |

Each `IMPL_EVAL_*` implements a `SWREQ_EVAL_*` gated like the marker (rule C§5.3).

### 3.4 AI workflow

| ID | Mechanism | Check | Expected | Ref |
|---|---|---|---|---|
| V19 | Per-product gate | `ubc check` / `ubc agent next` per product with the variant override | `SWREQ_EVAL_MCS` counted only in N; no false coverage gap in D, B, A | B§7.5 |
| V20 | Allocation stage | `ARCH_EVAL_LINK` handled by stage `bms_allocation` rules (or the fallback type of B§7.2) | stage gate passes in BEV products, not applicable in D | B§7.2 |

### 3.5 Toolchain parity

| ID | Check | Expected |
|---|---|---|
| V21 | per product: `needs.json` from ubc vs Sphinx (normalised) | identical sets of IDs and resolved field / link values |
| V22 | per product: ubCode HTML vs sphinx-needs HTML, visual spot check of V01–V10 | same visible content |

## 4. Procedure per item

1. Write the expectation (§3) — already done for the listed items.
2. Add the generic element(s) in one commit.
3. Run `tools/build_all.sh`; for V16 / V19 also the IDE.
4. Compare with the expectation for all four products, both toolchains.
5. Pass → next item. Fail → finding (§1.1, §5).
6. Negative probes (V11, V15) are applied **temporarily** and not committed;
   their outcome is logged.

Order: V14 → V18 → V01–V05 → V07 → V08 → V10 → V11 → V09 → V12 → V12b → V13 → V16 →
V17 → V19 → V20 → V21 → V22; V06 when `choose` is released.

## 5. Findings log

| # | V-item | Observation | Class | Fixed in (branch / PR / commit) | Plans updated |
|---|---|---|---|---|---|
| 1 | V04 | `.. if:: mcs` → "Unknown variant key: var.mcs"; `if` does not resolve named variants (ubc `if.invalid_expression`) | plan error | eval elements use spelled-out conditions | M§5, C§4, V04 |
| 2 | V02 | `var.hv.class` cannot be evaluated by sphinx-needs (`class` is a Python keyword); ubc accepts it | basic-setup bug | `fix/hv-voltage-and-schema-warnings` `07806d7` → `main`: `HV__CLASS` → `HV__VOLTAGE`, generator rejects keywords | B§2.1, V02, C§, K§ |
| 3 | all | Sphinx turns warning-severity schema results (backward coverage) into warnings → `-W` fails while a V is incomplete | basic-setup bug | same commit: `docs/conf.py` suppresses `sn_schema_warning.network_contains_too_few` (as the BMS) | — |
| 4 | all | `ubc check` exits 1 on the same backward-coverage warnings | expectation | decision 2026-10-09: stays warning-free (no `--deny error`, no lint ignore on `main`); eval branch keeps its `_EVAL_` ignore | C§6.2 rule 8 |
| 5 | V03 | `check_variants.py` read ``` ``<<[condition]: a, b>>`` ``` in prose as a condition | basic-setup bug | `fix/check-variants-inline-code` `37257e1` → `main` | — |
| 6 | V07 / V21 | ubc omits empty link lists in `needs.json`; Sphinx writes `[]` | expectation | checker normalises; T§ DOC-10 must normalise | T§ |
| 7 | V19 | `agent status` stage counts include imported needs (F-14); `agent gaps` excludes them correctly | tool bug (minor) | none needed for gates | — |
| 8 | V20 | every `arch` owes `refines` (swreqs stage, per type) → BMS black-box elements get a permanent gap (F-18); no per-stage filter in the schema | plan error | `fix/bms-block-type` `e744d72` → `main`: type `bms_block` (`BB_`), `allocation.toml`; V20 element `BB_EVAL` | B§4, B§7, C§2.3, C§3 |
| 9 | V21 | ubc writes `local-url` as absolute `file://` path and applies `remote_url_pattern`; Sphinx writes relative paths for both | tool difference | A§: strip / accept before publishing | A§ |
| 10 | — | sphinx-codelinks fails in a git worktree ("git root is not found": needs a `.git` directory) | tool bug | build in the main checkout | — |

## 6. Exit criteria

- All items pass for all four products in ubc and Sphinx — or have a logged
  tool bug with a workaround merged on `main`.
- All basic-setup fixes are merged on `main`; `eval/mechanisms` is rebased and
  green on top of it.
- M, K and B are updated with every plan error found.
- Handover:
  - to C§: the element patterns that worked (they become the templates for the
    real content);
  - to T§: the expectation tables of §3 (they become test oracles);
  - to A§: nothing to publish — the branch stays local; the mechanism
    regression (T§ L7) runs locally (`tools/build_all.sh` on the rebased branch).
