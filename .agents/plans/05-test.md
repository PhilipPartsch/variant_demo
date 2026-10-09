# Plan 5: Test everything

Step 5 of the [roadmap](00-roadmap.md). Tests the tooling, the build, the
variant mechanisms, the content and the IDE behaviour of the CV platform for
**all four products** and **both toolchains** (ubc and Sphinx). Plan 6
([06-automation.md](06-automation.md), `A§`) runs these tests in CI.

Referenced: [02-basic-setup.md](02-basic-setup.md) (`B§`),
[03-mechanism-evaluation.md](03-mechanism-evaluation.md) (`V§`),
[04-content.md](04-content.md) (`C§`),
[variant-mechanisms.md](variant-mechanisms.md) (`M§`),
[kconfig-variant-configuration.md](kconfig-variant-configuration.md) (`K§`).
Supersedes the generic test plan in `archive/`.

Products: **D** = `truck_diesel_eu`, **N** = `truck_bev_nmc_eu`,
**B** = `bus_bev_lfp_eu`, **A** = `truck_bev_lfp_na`.

## 1. Scope and levels

| Level | What | Where | How | Runs |
|---|---|---|---|---|
| L1 Tooling unit | generator, check scripts, importers | `tools/tests/` | pytest | every PR |
| L2 Build integration | CMake configure, active copies, BMS selection, component selection, entry points | `tools/tests/` | pytest driving `cmake` / `tools/build_product.sh` | every PR |
| L3 Docs per product | expected needs, values, links per product; ubc ↔ Sphinx parity | `tools/tests/golden/` | golden `needs.json` + oracle tables | every PR |
| L4 Content | coverage matrix C§1.1, traceability completeness per product | `tools/tests/` | scripts over `needs.json` | every PR |
| L5 Negative / mutation | every check fails when it should | `tools/tests/mutations/` | apply defect to a temp copy, expect failure | every PR |
| L6 C code | unit tests of the CV code per product | `tests/<x>/` | CTest; JUnit → `test_result` needs with `product` | every PR |
| L7 Mechanism regression | V§3 expectations on `eval/mechanisms` rebased on `main` | eval branch (local only) | `tools/build_all.sh` + V§3 tables as oracle | locally, after changes to the basic setup on `main` (the branch is never pushed) |
| L8 IDE | CMake Tools + ubCode behaviour | — | manual checklist | per release / tool upgrade |
| L9 Platform | paths, line endings, libclang | — | L1–L3 on Linux (CI), macOS (local), Windows (optional) | nightly / per release |

Local entry: `tools/test_all.sh` (L1–L6) — the same command CI calls (A§).

## 2. Oracles

| Oracle | Source |
|---|---|
| Presence per product of every need | "Present in" columns of C§2.1–§2.5 |
| Field values per product | C§2.2 (`value` fields), C§3 (BMS chemistry values) |
| Link targets per product | C§2.3, C§3 |
| Alternative branch per product | C§4.1, C§8.1 |
| Code needs per product | C§5, C§8.1 |
| Generic mechanism expectations | V§3 tables (for L7) |
| Golden files | `tools/tests/golden/<product>.needs.json`, `.../<product>.variants.json` — reviewed when created, updated only by a reviewed PR |

## 3. L1 — Tooling unit tests

| ID | Test | Expected | Ref |
|---|---|---|---|
| GEN-01 | `A__B__C` symbol | nested `var.a.b.c`, lower-case | K§4.1 |
| GEN-02 | symbol without namespace | generator error | K§4.1 |
| GEN-03 | bool / int / hex / string | `true`/`false`, integers, strings unchanged (`"2.50"`) | K§4.2 |
| GEN-04 | `tristate` in model | error | K§4.2 |
| GEN-05 | named choice | one string; option bools absent from JSON, present in `autoconf.h` | K§4.3 |
| GEN-06 | disabled symbol (`BMS__CHEMISTRY` in D) | emitted as `false` / `""` | K§4.6 |
| GEN-07 | undefined symbol / dependency violation / out of range in defconfig | error, non-zero exit | K§6 |
| GEN-08 | run twice | byte-identical, sorted, not rewritten when unchanged | K§6 |
| GEN-09 | `var.meta.product` | equals defconfig name | K§8.3 |
| GEN-10 | no kit / build-type input | CLI has none | K§0 P3 |
| GEN-11 | `--vscode` | `cmake-variants.json` and task inputs list the four products | K§6 |
| GEN-12 | `--check` with a hand-edited committed file | fails, names the file | K§6 |
| CHK-01 | alternatives check | detects a missing alternative ID per product | M§8 |
| CHK-02 | condition registry | detects an unknown `var.*` key | M§8 |
| CHK-03 | BMS pin check | detects version mismatch | B§8 |
| CHK-04 | skill mirror check | detects a skill missing or different in one of `.claude/skills/`, `.agents/skills/`, `.github/agents/` | B§7.4 |
| IMP-01 | test-result importer | `test_result` needs with `product`, `outcome`, `chain_reqs` | B§4.3 |
| IMP-02 | gap importer | `gap` needs with `product` and attribution fields | B§4.3 |

## 4. L2 — Build integration

| ID | Test | Expected | Ref |
|---|---|---|---|
| CMK-01 | configure without / with unknown `VARIANT` | clear configure error | K§7 |
| CMK-02 | configure each product | `build/active/{variants.json,autoconf.h,bms.needs.json}` match the product | B§5.3, B§6.2 |
| CMK-03 | broken defconfig | configure fails; active copies deleted | K§7 6.6 |
| CMK-04 | BMS selection | D → empty stub, N → NMC, B / A → LFP | B§5.3 |
| CMK-05 | component selection | CHG built for N, B, A; ENG built for D | B§6.1 |
| CMK-06 | build type fixed, kit independent | every build dir has `CMAKE_BUILD_TYPE=Debug`; the same product built with another kit gives identical `variants.json` and `needs.json` | K§0 P3 |
| CMK-07 | edit Kconfig / defconfig | reconfigure on next build | K§7 |
| ENT-01 | `tools/build_product.sh <p>` | `build/site/<p>/{sphinx,ubcode}/` and both `needs.json` | B§8 |
| ENT-02 | `tools/build_all.sh` | all products + once-per-repo checks pass | B§8 |

## 5. L3 — Documentation per product

Each test runs for D, N, B, A, with ubc **and** Sphinx.

| ID | Test | Expected | Ref |
|---|---|---|---|
| DOC-01 | needs present / absent | per C§2 "Present in" | C§2 |
| DOC-02 | `value` fields | `REQ_TRACTION_POWER_LIMIT`, `REQ_MAX_CHARGE_POWER` per C§2.2 | M§3 |
| DOC-03 | `<{ }>` text | product name, powertrain, chemistry rendered | M§3 |
| DOC-04 | link variant | `ARCH_VCU_POWER_MGMT` → `BMS_REQ_POWER_DERATING` only in N, B, A | M§4 |
| DOC-05 | alternatives | `REQ_ENERGY_SOURCE` and `ARCH_CHG_INLET` branch per C§8.1; exactly one per product | M§5.1 |
| DOC-06 | `choose` (**release-gated**) | same as DOC-05 after migration; skipped until the pin has `choose` | M§5.2 |
| DOC-07 | file variants | `subsystems/chg|bms` absent in D, `eng` only in D, region annex per market; `-W` passes | M§6 |
| DOC-08 | BMS import | `BMS_*` needs only in N, B, A, with the chemistry's values | B§5 |
| DOC-09 | code needs | `impl` / `test` per C§5 and C§8.1 (preprocessor + component) | B§6.2 |
| DOC-09b | same need ID, two implementations | exactly one `IMPL_VCU_ENERGY_DISPLAY` per product; its source line / title from the `#else` branch in D and the `#if` branch in N, B, A; trace to `SWREQ_VCU_ENERGY_DISPLAY` identical in all | C§5.1 |
| DOC-10 | parity | ubc and Sphinx `needs.json` identical after normalisation | — |
| DOC-11 | golden | `needs.json` equals `tools/tests/golden/<product>.needs.json` | — |

## 6. L4 — Content

| ID | Test | Expected | Ref |
|---|---|---|---|
| CNT-01 | coverage matrix | every row of C§1.1 has ≥1 item (types, links, fields, mechanisms) | C§1.1 |
| CNT-02 | traceability per product | no schema violations; no coverage warnings except those owed by later stages | B§4.4 |
| CNT-03 | gating consistency | every child gated ⊇ parent (no dangling links in any product) | B§7.3 |
| CNT-04 | allocations | every `allocates` targets a BMS interface need | B§4.4 |
| CNT-05 | review verdicts | every authored need has a verdict in `.pharaoh/verdicts/` with `parent_fit` and `variant_consistency` passed | B§7.3 |
| CNT-06 | brevity | needs ≤ 2 sentences (lint script, warning only) | C§0 |

## 7. L5 — Negative / mutation

| ID | Injected defect | Expected failing check |
|---|---|---|
| NEG-01 | ungated link to a BEV-only need | `-W` build fails for D |
| NEG-02 | `variant_sources` rule with unknown `var.foo` | `mounts.variant_rule_unevaluable` → fail |
| NEG-03 | condition with key not in the generated data | condition registry fails |
| NEG-04 | Kconfig symbol used nowhere | dead-symbol check fails |
| NEG-05 | condition true in all products | branch-coverage check fails |
| NEG-06 | `BUILD__DEBUG` symbol / `var.build.*` | build-configuration check fails |
| NEG-07 | symbol without `help` / `tristate` / no prefix | Kconfig hygiene fails |
| NEG-08 | hand-edited generated file | drift check fails |
| NEG-09 | overlapping alternative conditions | duplicate-ID build error |
| NEG-10 | gap in alternative conditions | alternatives check fails |
| NEG-11 | allocation to a non-interface BMS need | schema (or CI script) fails |
| NEG-12 | BMS pin points to a version without an allocated ID | dangling external link fails |
| NEG-13 | missing `variant_data_file` | sanity check fails (no silent empty values) |
| NEG-14 | bare boolean `var.x` in a `variant_sources` rule | rejected → fail |
| NEG-15 | marker inside `#if CONFIG_CHARGING__MCS` implementing an ungated swreq | gating-consistency check fails |
| NEG-16 | the two `IMPL_VCU_ENERGY_DISPLAY` markers without `#if` / `#else` (both active) | duplicate ID: ubc `needs.duplicate`, Sphinx `duplicate_id` |

## 8. L6 — C code

| ID | Test | Expected |
|---|---|---|
| CODE-01 | CTest per product | all tests of built components pass |
| CODE-02 | feature code | MCS tests run only in N; pantograph tests only in B |
| CODE-03 | JUnit import | `test_result` needs per product with `results_for` → `TEST_*` |
| CODE-04 | every `swreq` present in a product has ≥1 passing test in that product | per-product verification coverage |

## 9. L8 — IDE checklist (manual)

Manual; moved to [07-manual-steps.md](07-manual-steps.md) §2 (M-05,
IDE-01 … IDE-07). Other manual steps of this plan: M-03 (approve the golden
files), M-04 (CNT-05 as `xfail`), M-06 (Windows in L9).

## 10. Entry and exit criteria

**Entry:** plan 4 content merged for the items under test (M-01); golden files
reviewed (M-03, [07-manual-steps.md](07-manual-steps.md)).

**Exit:**

- L1–L6 green for all four products, both toolchains, on Linux.
- Every NEG test fails as expected (a check that never fails is not a check).
- L7 green on `eval/mechanisms` rebased on the current `main`.
- L8 checklist passed on at least one OS ([07-manual-steps.md](07-manual-steps.md) M-05).
- Release-gated tests (DOC-06) skipped only while the pinned sphinx-needs has
  no `choose`; mandatory after the pin is raised.
- Every test that fails because of a useblocks tool (not our content or
  tooling) has an entry in [99-tool-bugs.md](99-tool-bugs.md), and the test
  references its id (e.g. `xfail` reason "PH-01").

**Tool findings → plan 99:** every bug or gap found in a useblocks tool (ubc / ubCode, Pharaoh, Sphinx-Needs, Sphinx-Codelinks, sphinx-mounts, ubc-action, ubTrace, ubConnect, Sphinx-Test-Reports) is added to [99-tool-bugs.md](99-tool-bugs.md) in the same session: summary, marker `branch@commit` + file:line on a pushed branch, input, wrong output, workaround, two solutions.

## 11. Rollout

1. L1 with the generator (test-first, can start during plan 2).
2. L2 and the entry points.
3. Golden files and L3 once content step C§9 is complete.
4. L4 and L5.
5. L6 with the C code (C§5).
6. L7 on the eval branch.
7. L8 checklist; L9 nightly.
8. Wire everything into CI (A§).
