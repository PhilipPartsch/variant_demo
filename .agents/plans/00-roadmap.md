# Roadmap: CV platform with variant management

Six steps, one plan each, plus plan 7 with all manual steps. The CV platform (commercial vehicle: truck / bus,
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
| 7 | [07-manual-steps.md](07-manual-steps.md) | `MS§` | all manual steps of plans 3–6 and 99 (decisions, reviews, IDE session, browser checks, settings) — the other plans point here | — |

Triggered plan (not in the execution order): [20-choose-migration.md](20-choose-migration.md)
— migrate the alternatives from complementary `if` blocks to `choose` / `when`
/ `otherwise` as soon as Sphinx-Needs (≥ 8.6.0) **and** ubc / ubCode support it
(gate checked 2026-10-10: neither does yet).

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
      │                     7 reviews: M-01 content, M-03 golden files, M-04 xfail
      │                                                                 │
      └────────────────────────────────── main ◄── merge test/cv-platform (content + tests)
                                           │
                                           └──► 6 ci/* (from main, PR) ──► main ──► GitHub Pages
```

Execution order (decision 2026-10-10, "way A"):

| # | Step | Branch | Done when |
|---|---|---|---|
| 1 | plan 1 evaluation | `eval/open-questions` (local) | ✓ |
| 2 | plan 2 basic setup | `setup/cv-platform` → `main` | ✓ |
| 3 | plan 3 mechanism evaluation | `eval/mechanisms` (local) | ✓ |
| 4 | plan 4 content | `content/cv-platform` | ✓ (not merged) |
| 5 | plan 5 tests | `test/cv-platform` on top of the content | ✓ (not merged) |
| 6 | **plan 7 reviews** M-01, M-03, M-04 | — | your OK |
| 7 | merge `test/cv-platform` (content + tests) into `main`, push | `main` | `tools/test_all.sh` green on `main` |
| 8 | plan 6 automation | `ci/*` from `main`, pull request | first CI run on `main` green (A§1.1) |
| 9 | plan 7 after the deploy: M-07, M-08, M-09 | — | |

The remaining manual steps of plan 7 (M-05 IDE session, M-02, M-06, M-10 …
M-13) do not block this order.

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
| `main` | basic setup, content, tests, automation | — |
| `eval/open-questions` | step 1 scratch experiments — **local only**, never pushed (the repository stays clean) | never |
| `eval/mechanisms` | step 3 generic elements — **local only**, never pushed; rebased on `main` | never |
| `setup/*`, `content/*`, `test/*`, `ci/*`, `fix/*` | work branches | via pull request, CI green |
| `gh-pages` | published site: one folder per product variant (`<product>/sphinx`, `<product>/ubcode`, …); written **only by CI** (A§3.1) | never (orphan branch) |

On `origin` there are only `main`, `gh-pages` and short-lived work branches
during their pull request (deleted on merge). GitHub settings: B§3.4.

Tag `pre-cv-platform` on `main` before the first restructuring commit (B§3.2).

Plans live in `.agents/plans/` — local only, gitignored, kept for now.

## Global rules

1. Only released, ubCode-supported directives — no invented directives,
   markers or comment conventions. Unreleased features (e.g. sphinx-needs
   `choose`) get a fallback from released features.
2. Build kit / build type are never part of the variant model (K§0 P3); the
   build type is always `Debug` and not offered as a choice.
3. Every product is built with **both** ubc and Sphinx; their results must
   agree.
4. Every bug or gap found in a **useblocks tool** is recorded in
   [99-tool-bugs.md](99-tool-bugs.md) (summary, `branch@commit` marker on a
   pushed branch, input, wrong output, two solutions) — in every plan, in the
   same session the finding is made.
