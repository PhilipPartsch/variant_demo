# Roadmap: CV platform with variant management

Seven steps, one plan each, plus plan 8 with all manual steps. The CV platform (commercial vehicle: truck / bus,
diesel / battery-electric, using the BMS from `rollout-demo-bms`) is built in
**this repository** (`origin` = `https://github.com/PhilipPartsch/variant_demo`).

| Step | Plan | Abbrev. | Result | Branch |
|---|---|---|---|---|
| 1 | [01-evaluation.md](01-evaluation.md) | `E§` | answers to all open **Verify** questions | `eval/open-questions` (local only, never pushed) |
| 2 | [02-basic-setup.md](02-basic-setup.md) | `B§` | structured, empty repository that builds every product | `setup/*` → `main` |
| 3 | [03-mechanism-evaluation.md](03-mechanism-evaluation.md) | `V§` | every variant mechanism proven with bare-minimum generic elements | `eval/mechanisms` (local only, on top of `main`, never pushed); fixes → `main` |
| 4 | [04-content.md](04-content.md) | `C§` | small, short CV content covering everything | `content/*` → `main` |
| 5 | [05-test.md](05-test.md) | `T§` | tests for tooling, mechanisms, content and IDE behaviour | `test/*` → `main` |
| 6 | [06-automation.md](06-automation.md) | `A§` | CI for builds and tests; GitHub Pages with sphinx-needs and ubCode output side by side for all products | `ci/*` → `main` |
| 7 | [07-system-model.md](07-system-model.md) | `S§` | system, subsystems, missing BMS capabilities as requirements, interfaces and external systems as needs (three phases, one PR each) | `model/*` → `main` |
| 8 | [08-manual-steps.md](08-manual-steps.md) | `MS§` | all manual steps of plans 3–7 and 99 (decisions, reviews, IDE session, browser checks, settings) — the other plans point here | — |

Triggered plan (not in the execution order): [20-choose-migration.md](20-choose-migration.md)
— migrate the alternatives from complementary `if` blocks to `choose` / `when`
/ `otherwise`. **Done 2026-10-14** (PR #4): Sphinx-Needs 9.0.0, sphinx-mounts
0.3.0, Sphinx-Codelinks 2.0.0, ubc / ubCode 0.37.0.

Triggered plan: [110-test-reports.md](110-test-reports.md) — replace the own test
result importer by Sphinx-Test-Reports once ubCode supports it. **Triggered
2026-10-14** (T1, T4): ubCode 0.37.0 reads the STR directives; re-run open.

Demo (not a step): [30-demo.md](30-demo.md) — demo script: preparation, eight acts
(10-minute and 30-minute version), likely questions, fallbacks.

Bug list (not a step): [99-tool-bugs.md](99-tool-bugs.md) — bugs and gaps in
the **useblocks tools** (ubc / ubCode, Pharaoh, Sphinx-Needs, Sphinx-Codelinks,
sphinx-mounts, ubc-action), each with a `branch@commit` marker, input, wrong
output and two solution options. Every plan adds its new findings there.

Concept references (not steps):

| Document | Abbrev. | Content |
|---|---|---|
| [variant-mechanisms.md](variant-mechanisms.md) | `M§` | how documents consume `var.*`: fields, links, `if`, alternatives, `variant_sources`, mounts |
| [kconfig-variant-configuration.md](kconfig-variant-configuration.md) | `K§` | Kconfig feature model, generator, CMake, VS Code / CMake Tools |

`archive/` holds superseded plans (kept for now).

## Flow

```
 1 evaluation ──decisions──► M, K, 02–06
      │
 2 basic setup ──────────────► main ◄──────────── fixes ─────────┐
      │                          │                                │
      │                          ├──► 3 eval/mechanisms (side branch, rebased on main)
      │                          │         └── findings ──────────┘
      │                          │
      │                          └──► 4 content/cv-platform ──► 5 test/cv-platform (on top of 4)
      │                                                                 │
      │                     8 reviews: M-01 content, M-03 golden files, M-04 xfail
      │                                                                 │
      └────────────────────────────────── main ◄── merge test/cv-platform (content + tests)
                                           │
                                           └──► 6 ci/* (from main, PR) ──► main ──► GitHub Pages
                                                                          │
                     7 model/system ──► model/bms-requirements ──► model/interfaces (one PR each)
                                                                          │
                                           8 open manual steps (M-07 … M-13, golden reviews)
```

Execution order (decision 2026-10-10, "way A"):

| # | Step | Branch | Done when |
|---|---|---|---|
| 1 | plan 1 evaluation | `eval/open-questions` (local) | ✓ |
| 2 | plan 2 basic setup | `setup/cv-platform` → `main` | ✓ |
| 3 | plan 3 mechanism evaluation | `eval/mechanisms` (local) | ✓ |
| 4 | plan 4 content | `content/cv-platform` | ✓ (not merged) |
| 5 | plan 5 tests | `test/cv-platform` on top of the content | ✓ (not merged) |
| 6 | **plan 8 reviews** M-01, M-03, M-04 | — | ✓ 2026-10-10 |
| 7 | merge `test/cv-platform` (content + tests) into `main`, push | `main` | ✓ 2026-10-10 |
| 8 | plan 6 automation | `ci/*` from `main`, pull request | ✓ 2026-10-10: PR #1 merged, site live (nightly open) |
| 9 | plan 7 phase 1: system and subsystems | `model/system` → PR | ✓ 2026-10-13: PR #3 merged; M-14, IDE-08 done |
| 10 | plan 7 phase 2: missing BMS capabilities as requirements | `model/bms-requirements` → PR | CI green, merged |
| 11 | plan 7 phase 3: interfaces and external systems | `model/interfaces` → PR | CI green, merged |
| 12 | plan 8 after the deploy: M-07, M-08, M-09 | — | |

Plan 7 comes before the open manual steps of plan 8 (decision 2026-10-12);
its own manual items (golden reviews, IDE check) are added to plan 8. The
remaining manual steps of plan 8 (M-05 IDE session, M-02, M-06, M-11 …
M-13) do not block this order.

Outside this order: plan 20 (`choose` migration) ✓ 2026-10-14, PR #4 merged
(M-10 done).

- Step 1 decides **how** things are configured; nothing of it lands on `main`
  directly — working snippets are copied into step 2.
- Step 3 runs on top of `main`. A bug in the basic setup is **fixed on
  `main`** (branch `fix/*`, PR), then `eval/mechanisms` is rebased.
- Step 6 starts only after content and tests are merged into `main` (row 7
  of the execution order), so the first CI run checks exactly the reviewed
  state and can call `tools/test_all.sh` from the start.

## Branch and commit rules

| Branch | Purpose | Merged to `main`? |
|---|---|---|
| `main` | basic setup, content, tests, automation, system model | — |
| `eval/open-questions` | step 1 scratch experiments — **local only**, never pushed (the repository stays clean) | never |
| `eval/mechanisms` | step 3 generic elements — **local only**, never pushed; rebased on `main` | never |
| `setup/*`, `content/*`, `test/*`, `ci/*`, `model/*`, `fix/*` | work branches | via pull request, CI green |
| `gh-pages` | published site: one folder per product variant (`<product>/sphinx`, `<product>/ubcode`, …); written **only by CI** (A§3.1) | never (orphan branch) |

On `origin` there are `main`, `gh-pages` and the feature / work branches of the
pull requests. **Feature branches are kept after the merge** (decision
2026-10-14; R11 "delete head branches on merge" stays off) — never delete them.
`eval/*` branches stay local. GitHub settings: B§3.4.

Tag `pre-cv-platform` on `main` before the first restructuring commit (B§3.2).

Plans live in `.agents/plans/` — local only, gitignored, kept for now.

## Global rules

1. Only released, ubCode-supported directives — no invented directives,
   markers or comment conventions. Unreleased features get a fallback from
   released features (as `choose` had until Sphinx-Needs 9.0.0 / ubCode
   0.37.0: complementary `if` blocks, M§5.1).
2. Build kit / build type are never part of the variant model (K§0 P3); the
   build type is always `Debug` and not offered as a choice.
3. Every product is built with **both** ubc and Sphinx; their results must
   agree.
4. Every bug or gap found in a **useblocks tool** is recorded in
   [99-tool-bugs.md](99-tool-bugs.md) (summary, `branch@commit` marker on a
   pushed branch, input, wrong output, two solutions) — in every plan, in the
   same session the finding is made.
