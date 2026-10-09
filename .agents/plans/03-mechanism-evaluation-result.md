# Result of plan 3: Mechanism evaluation

Outcome of [03-mechanism-evaluation.md](03-mechanism-evaluation.md) (`V§`),
executed 2026-10-09 on the local branch `eval/mechanisms` (never pushed),
rebased on `main` `e744d72`.

**Status: all automated items pass for all four products in ubc and Sphinx,
including V20 after the `bms_block` decision. Deferred (decision 2026-10-09, low risk): the IDE items V16 / V17 (IDE half)
to the first VS Code session in plan 4, V22 to the Pages comparison in plan 6;
V06 skipped (`choose` not released). Plan 3 closed.**

## 1. Results per item

D = `truck_diesel_eu`, N = `truck_bev_nmc_eu`, B = `bus_bev_lfp_eu`, A = `truck_bev_lfp_na`.
"ubc + Sphinx" = checked by `tools/eval_expect.py` in both `needs.json` exports.

| ID | Mechanism | Result D / N / B / A | Status |
|---|---|---|---|
| V14 | Kconfig generator | nesting, choices as strings, disabled `false` / `""`, `meta.product`; drift check clean | ✓ |
| V18 | entry points | `tools/build_all.sh` green, both HTML outputs per product | ✓ |
| V01 | field, named variant | truck / truck / bus / truck | ✓ ubc + Sphinx |
| V02 | field, inline condition | 400 / 800 / 400 / 800 (after fix #2) | ✓ ubc + Sphinx |
| V03 | `<{ }>` data reference | product names; chemistry "" / nmc / lfp / lfp | ✓ ubc + Sphinx |
| V04 | `if` | – / ✓ / – / – (spelled-out condition, finding #1) | ✓ ubc + Sphinx |
| V05 | alternatives, one id | otherwise / mcs / pantograph / otherwise | ✓ ubc + Sphinx |
| V06 | `choose` | — | skipped (not released) |
| V07 | link variant | `allocates` [] / PD / PD / PD | ✓ ubc + Sphinx (ubc omits the empty list, #6) |
| V08 | file variant | – / ✓ / ✓ / ✓; toctree entry INFO, `-W` passes | ✓ ubc + Sphinx |
| V09 | mount with `if` | – / – / ✓ / – | ✓ ubc + Sphinx |
| V10 | BMS import | none / NMC / LFP / LFP, `status imported`, tag `interface` | ✓ ubc + Sphinx |
| V11 | dependency rule | gated child valid everywhere; probe (ungated link to `REQ_EVAL_IF`): dangling link in D in both tools, resolves in N | ✓ |
| V12 | preprocessor | DIESEL / BEV+MCS+HDR / BEV / BEV, header via fallback includes | ✓ ubc + Sphinx |
| V12b | one id, two implementations | `IMPL_EVAL_ENERGY` from `#else` (fuel) in D, `#if` (SoC) in N/B/A; probe without `#if`/`#else`: ubc `needs.duplicate`, Sphinx `duplicate_id` | ✓ |
| V13 | component selection | – / ✓ / ✓ / ✓ | ✓ ubc + Sphinx |
| V15 | Kconfig constraint | probe MCS on the 400 V bus: generator fails with the dependency message, `build/active/` emptied | ✓ |
| V16 | CMake Tools switching | — | **deferred** → first VS Code session in plan 4 (§3); covered in plan 1 (E-R D1/D2) and on the CLI |
| V17 | build settings outside the model | all build dirs `Debug`; GCC 16 vs Apple Clang: identical `variants.json`, identical ubc and Sphinx `needs.json` (225 needs) | ✓ CLI; IDE half **deferred** → plan 4 (§3) |
| V19 | per-product gate | `ubc agent gaps` per product: `SWREQ_EVAL_MCS` only in N, gated needs only where present, no `BMS_*` gaps | ✓ |
| V20 | allocation stage | first run: an `arch` with `allocates` owes `refines` (permanent gap) → new type `bms_block`; `BB_EVAL` – / ✓ / ✓ / ✓, only the review gap, stage `bms_allocation` counts 1 element (archs 17) | ✓ ubc + Sphinx |
| V21 | parity | per product identical need IDs and identical variant-relevant values; differences only in export format (#6, #9) | ✓ |
| V22 | visual spot check | — | **deferred** → plan 6 Pages comparison (A§1.1 G5); `needs.json` parity shown in V21 |
| — | alternatives check (NEG-10) | probe without the `otherwise` branch: `check_variants.py` reports `REQ_EVAL_ALT` missing in D | ✓ |

## 2. Findings and fixes

Full log in V§5. Summary:

| # | Finding | Class | Where fixed |
|---|---|---|---|
| 1 | `if` does not resolve named variants | plan error | M§5, C§4, V04 updated |
| 2 | `var.hv.class` unusable in Sphinx (Python keyword) | basic-setup bug | `main` `07806d7`: `HV__VOLTAGE`, generator rejects keywords |
| 3 | Sphinx `-W` fails on backward-coverage warnings | basic-setup bug | `main` `07806d7`: `suppress_warnings` as in the BMS |
| 4 | `ubc check` fails on backward-coverage warnings | expectation | stays warning-free (decision); content rule C§6.2 #8; eval keeps its narrow ignore |
| 5 | `check_variants.py` false positive on inline literals | basic-setup bug | `main` `37257e1` |
| 6 | ubc omits empty links in `needs.json` | expectation | normalise in T§ DOC-10 |
| 7 | `agent status` counts imported needs (F-14) | tool (minor) | gaps are correct; feedback to useblocks |
| 8 | BMS black-box arch owes `refines` (F-18) | plan error | `main` `e744d72`: type `bms_block` |
| 9 | ubc `local-url` absolute `file://`, `remote-url` differs from Sphinx | tool difference | A§ |
| 10 | sphinx-codelinks fails in a git worktree | tool bug | build in the main checkout |

Fix branches `fix/hv-voltage-and-schema-warnings`, `fix/check-variants-inline-code`
and `fix/bms-block-type` are merged (fast-forward) into `main` and kept;
`main` pushed 2026-10-09 (`origin/main` = `e744d72`, no trailers).

## 3. Deferred checks (IDE, visual)

Risk accepted 2026-10-09: IDE / display only, no effect on build, content,
CI or Pages. With `eval/mechanisms` checked out:

1. **V16:** switch D → N → B → A in the CMake Tools status bar. Per switch:
   `build/active/VARIANT` follows, the landing page and `docs/eval/index.rst`
   preview show the product, the Needs Index shows `IMPL_EVAL_ENERGY` from the
   right branch (`src/vcu/eval_markers.c`), `REQ_EVAL_IF` only in N.
2. **V17 (IDE half):** the status bar offers only the product, no build type.
3. **V22:** compare `build/site/<product>/ubcode/eval/mechanisms.html` with
   `build/site/<product>/sphinx/eval/mechanisms.html` for V01–V10 (run
   `tools/build_all.sh` first).

## 4. Decisions taken (2026-10-09)

| # | Question | Decision | Done |
|---|---|---|---|
| 1 | dedicated type for BMS black boxes | **yes** | type `bms_block` (`BB_`), stage `bms_allocation` produces it, schema rules `id-prefix-bms_block`, `trace-bms_block-satisfies`, `bms_block-allocates`, `alloc-*` for arch + bms_block, criteria `metamodel/quality/allocation.toml`; B§ and C§ updated (`ARCH_BMS_*` → `BB_*`) |
| 2 | `ubc check --deny error` during authoring | **no — stays warning-free** | C§6.2 rule 8: author complete V slices, no lint ignores on `main` |
| 3 | push `main` | **yes** | pushed `e744d72` |

## 5. Handover

- **C§ (plan 4):** templates = the eval elements (`docs/eval/*.rst`,
  `src/vcu/eval_markers.c`); spelled-out `if` conditions; `<<name: a, b>>` for
  named variants; `HV__VOLTAGE` / `var.hv.voltage`; black boxes as `bms_block`
  with a CV `arch` per vehicle req as well; warning-free `ubc check`.
- **T§ (plan 5):** oracle = `tools/eval_expect.py` (V§3 tables as code);
  normalise empty links (#6) for DOC-10; the probes of §1 are NEG-01, NEG-09,
  NEG-10, NEG-16 and GEN-07.
- **A§ (plan 6):** codelinks URLs in published `needs.json` (#9).
