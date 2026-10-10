# Plan 20: Migrate the alternatives to `choose` / `when` / `otherwise`

Triggered plan (not part of the numbered execution order): starts as soon as
**every useblocks tool in the toolchain supports `choose`** (gate, §1). Until
then the alternatives stay as complementary `if` blocks with one shared id
(M§5.1) — the released fallback required by global rule 1 of the roadmap.

Referenced: [variant-mechanisms.md](variant-mechanisms.md) (`M§5`, §5.1, §5.2),
[04-content.md](04-content.md) (`C§4.1`, §8.2), [05-test.md](05-test.md)
(`T§` DOC-06, NEG-09), [03-mechanism-evaluation.md](03-mechanism-evaluation.md)
(`V§` V06), [07-manual-steps.md](07-manual-steps.md) (M-10),
[99-tool-bugs.md](99-tool-bugs.md).

## 0. Goal

Each set of complementary `if` blocks that defines one need id becomes one
`choose` with `when` branches (first true branch wins) and, where it fits, an
`otherwise`. **The per-product result must not change**: every product's
`needs.json` (ubc and Sphinx) and the golden files stay identical; only the
source gets simpler (no repeated negations).

Syntax (Sphinx-Needs `latest`, "Added in version 8.6.0"):

```rst
.. choose::

   .. when:: var.charging.mcs == True

      .. arch:: High-power charging interface
         :id: ARCH_CHG_INLET
         …

   .. when:: var.charging.pantograph == True

      .. arch:: High-power charging interface
         :id: ARCH_CHG_INLET
         …

   .. otherwise::

      .. arch:: High-power charging interface
         :id: ARCH_CHG_INLET
         …
```

Rules (Sphinx-Needs documentation): conditions in order, first true `when`
wins; `otherwise` optional and last; a `choose` contains only `when`,
`otherwise` and comments, all in the same file; branches not taken are never
parsed; conditions use the `var` namespace only (same grammar as `if` — named
variants are not resolved, plan 99 UB-12); mistakes are reported as
`needs.choose`.

## 1. Gate — all useblocks tools support `choose`

| Tool | Needed | Status 2026-10-10 | How to check |
|---|---|---|---|
| Sphinx-Needs | release with `choose` | **no** — latest release 8.5.0 (2026-09-03); `choose` documented for 8.6.0 | PyPI `sphinx-needs` ≥ 8.6.0; the probe (§3 step 1) builds with `-W` |
| ubc (CLI) | parses `choose`, same result as Sphinx | **no** — 0.35.0: `Unknown directive: 'choose'`, the alternative need is dropped (probe on `test/cv-platform@23d74b4`, reverted) | probe: `ubc check` without `Unknown directive`, `ubc build needs` per product = Sphinx |
| ubCode (VS Code) | editor support: branches not taken shown inactive, Needs Index follows the product | **no** (same engine as ubc 0.35.0) | IDE check (§3 step 9, plan 7) |
| Pharaoh (`ubc agent`) | stages, gaps and reviews see the chosen branch | open | `ubc agent gaps` per product unchanged by the migration |
| sphinx-mounts, Sphinx-Codelinks | not involved (`choose` is inside a document; code alternatives stay `#if` / `#else`) | — | — |

Check the gate whenever a new Sphinx-Needs or ubCode release appears. Record
the result in this table; a failing check of a released version goes into
plan 99.

## 2. Scope

| Alternative (one id) | File | Today (`if` blocks) | With `choose` |
|---|---|---|---|
| `REQ_ENERGY_SOURCE` (showcase A) | `docs/vehicle/requirements.rst` | `bev` / `not bev` | `when var.powertrain.type == 'bev'` + `otherwise` |
| `ARCH_CHG_INLET` (showcase B) | `docs/subsystems/chg/architecture.rst` | `mcs` / `pantograph and not mcs` / `not mcs and not pantograph` | `when mcs`, `when pantograph`, `otherwise` — the negations disappear; the order is the decision `DEC_CHARGING_INLET_PRIORITY` |
| `ARCH_CHG_SESSION_CONTROL` (market) | `docs/subsystems/chg/architecture.rst` | `eu` / `na` | `when eu`, `when na`, **no** `otherwise` (a new market must get its own branch; without one the id is missing and the alternatives check fails, instead of a silent CCS1 default) |
| `REQ_EVAL_ALT` / new `REQ_EVAL_CHOOSE` (V05 / V06) | `eval/mechanisms`: `docs/eval/mechanisms.rst` | V05 `if` blocks | V06 `choose` element (V§3.1), V05 kept as the `if` reference |

Not in scope: single `if` blocks (presence, no alternative), file variants,
link and field variants, code alternatives (`#if` / `#else`, C§5.1).

## 3. Steps

Work on a branch `feat/choose` from `main`; one commit per step.

| # | Step | Done when |
|---|---|---|
| 1 | **Probe** in a copy (pattern of T§ L5): showcase A as `choose`, all four products, ubc + Sphinx | same `needs.json` per product as the `if` form; no `Unknown directive`, no `needs.choose` warning |
| 2 | **Pin** the versions: `requirements.txt` (`sphinx-needs==8.6.x`), ubc / ubCode version in `tools/env.sh` hint, A§1 `UBC_VERSION`, README | `tools/test_all.sh` green with the new versions *before* any content change |
| 3 | **Mechanism evaluation** on `eval/mechanisms` (local): add V06 (`REQ_EVAL_CHOOSE`, three branches) to `docs/eval/mechanisms.rst` and to `tools/eval_expect.py` | V06 otherwise / mcs / pantograph / otherwise in both tools (V§3.1) |
| 4 | **Tooling:** `tools/check_variants.py` reads `.. when::` conditions (registry, bare booleans) and checks branch coverage per `choose` (every branch, including `otherwise`, is taken in ≥ 1 product; first-match semantics); alternatives check unchanged (an id defined in several branches exists in every product that has the file) | unit tests for the new parsing (L1) green |
| 5 | **Migrate showcase A** (`REQ_ENERGY_SOURCE`) | golden files unchanged, `tools/test_all.sh` green |
| 6 | **Migrate showcase B** (`ARCH_CHG_INLET`) and update `DEC_CHARGING_INLET_PRIORITY` (the order of the `when` branches is the decision) | golden files unchanged except the decision text |
| 7 | **Migrate the market alternative** (`ARCH_CHG_SESSION_CONTROL`) | golden files unchanged |
| 8 | **Tests:** DOC-06 active (skip only if the installed Sphinx-Needs < 8.6.0); NEG-09 becomes "overlapping `when` conditions → first branch wins, no duplicate" (expectation changes); new NEG-17 `when` without condition → `needs.choose`; new NEG-18 `choose` without matching branch and without `otherwise` → alternatives check fails | `tools/test_all.sh` green |
| 9 | **IDE check** (plan 7, as an addition to M-05): ubCode shows the branches not taken as inactive and the Needs Index follows the product for the three alternatives | your OK |
| 10 | **Rules and texts:** M§5.1 / §5.2 (interim pattern → history), C§6.2 rule 4, the authoring texts of `[workflow]` (stage `reqs`: "alternatives as `choose`"), criterion `variant_consistency` (mentions `choose` / `when`), the RST comments "With the sphinx-needs `choose` directive this becomes …" removed | review of the diff |
| 11 | **Reviews:** the changed needs get new fingerprints → one review round (independent context) for the migrated ids | verdicts submitted; PH-01 (one verdict per id) still applies — `choose` does not change it |
| 12 | Pull request to `main`; plan 7 M-10 closed; C§8.2 demo readiness done | merged |

## 4. Exit criteria

- All alternatives of §2 use `choose`; no complementary `if` blocks with one id remain on `main`.
- Per product and toolchain: `needs.json` unchanged against the golden files
  (except texts changed on purpose in step 6), warning-free `ubc check`,
  `sphinx-build -W`, `tools/test_all.sh` green including DOC-06.
- V06 green on `eval/mechanisms` (L7).
- IDE check of step 9 passed.
- Every problem found in a useblocks tool is in [99-tool-bugs.md](99-tool-bugs.md).

## 5. Rollback

The `if` form stays in the git history (commit before step 5). If a later tool
version breaks `choose`, revert steps 5–7 (one commit each) and keep the
pinned versions of step 2 until the tool is fixed.

## 6. Open points

- **ubc / ubCode version** with `choose`: unknown; check the release notes of
  every ubCode release (gate §1).
- **Named variants in `when`:** same grammar as `if` → not resolved (UB-12);
  spelled-out conditions as today.
- **Verdicts:** `choose` keeps one id per alternative, so PH-01 (verdict per id)
  is not solved by the migration.
- **`otherwise` vs. explicit `when`:** decided per alternative in §2 (market:
  no `otherwise`, so that a new market is not silently mapped).
