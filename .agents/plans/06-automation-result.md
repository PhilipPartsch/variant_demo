# Result of plan 6: Automation

Outcome of [06-automation.md](06-automation.md) (`A§`), executed 2026-10-10 on
`ci/pages`, merged into `main` with PR #1
(https://github.com/PhilipPartsch/variant_demo/pull/1, merge commit `9546209`).

**Status: CI green on pull requests and on `main`; the site is live at
https://philippartsch.github.io/variant_demo/ — four products, sphinx-needs and
ubCode side by side. Open: `nightly.yml` (A5), the local `--checks` /
`--product` options (A§4), the manual browser checks and rulesets (plan 8
M-07 … M-09).**

## 1. Definition of done

| # | Criterion | Result |
|---|---|---|
| A1 | PRs run checks, product matrix and tests; results in PR and job summary | ✓ run 38046042046 (PR): products, 4 × build, checks (121 passed, 1 skipped), site with job summary |
| A2 | push to `main` updates `gh-pages`, one folder per product, landing page | ✓ run 38046217069: `pages` committed `site: 9546209…` (`66e9ae3`, by github-actions[bot]); Pages build `built` |
| A3 | per product: sphinx-needs, ubCode, side by side, needs diff, tests | ✓ `<product>/{sphinx,ubcode}/`, `compare.html`, `needs-diff.html` (0 differences in all four), `tests/` (all passed); HTTP 200 checked |
| A4 | first-run verification (§1.1) | ✓ see §2 |
| A5 | nightly platform run | **open** (rollout step 8) |

## 2. First-run verification (A§1.1)

| ID | Result |
|---|---|
| E§ G3 — ubc without licence in CI | ✓ ubc 0.35.0 runs `check`, `build needs`, `build html`, `agent check`/`doctor` in this public, MIT-licensed repository without licence inputs |
| E§ E5 — libclang on Linux | ✓ same code needs as on macOS (golden files, DOC-09, DOC-09b green on `ubuntu-latest`) |
| E§ G4 — deploy to `gh-pages` | ✓ variant folders + `.nojekyll`; `_static/` served (HTTP 200) |
| E§ G5 — compare page | technically ✓ (HTTP 200); **visual check open** (plan 8 M-07) |
| 99 UB-14, CL-03 — no machine paths | ✓ no `/home/runner` or `file:///` in the published tree (`make_site.py` fails the deploy otherwise) |
| T§ L9 — Linux | ✓ 121 passed, 1 skipped — identical to macOS |

## 3. What was built

| File | Content |
|---|---|
| `.github/workflows/ci.yml` | `products` (matrix from `configs/*_defconfig`) → `build` (per product `tools/build_product.sh`, artifact) → `checks` (`tools/check_all.sh`, `SKIP_BUILD=1 tools/test_all.sh`, `ubc agent doctor`) → `site` (`tools/make_site.py`, job summary, `site` artifact as preview) → `pages` (push to `main`: `rsync --delete` into the `gh-pages` checkout, one commit per deploy) |
| `.github/actions/setup/action.yml` | ninja, graphviz, uv + `.venv` from `requirements.txt`, ubc 0.35.0 downloaded with a pinned SHA-256 |
| `tools/make_site.py` | landing page, `compare.html`, `needs-diff.html`, `tests/`, `products.json`, `.nojekyll`; local paths → repository-relative; same tree locally in `build/site/` |
| `tools/check_all.sh` | once-per-repo checks, shared by `build_all.sh` and CI |

Settings: `contents: read` by default, `contents: write` only for `pages`;
`concurrency` per ref (PRs cancel older runs) and group `gh-pages` for the
deploy; all third-party actions pinned to commit SHAs (R7).

## 4. Findings

| # | Finding | Handling |
|---|---|---|
| 1 | `useblocks/ubc-action` uses `actions/cache@v4` by tag → blocked by the SHA-pinning policy; also downloads into the workspace, no checksum | plan 99 **UA-02**; ubc downloaded directly (`setup` action) |
| 2 | `tools/env.sh` aborted silently (`set -euo pipefail` + failing `ls`) when the ubCode extension is missing | fixed (`706bcc9`) |
| 3 | `ubc build needs` writes absolute `__source__` paths also without `--source-maps` | plan 99 **UB-01** sharpened; `make_site.py` makes them relative |
| 4 | `gh run watch` returned before the run finished | polled with `gh run view` instead (local tooling only) |

## 5. Deviations from the plan

| Plan | Deviation |
|---|---|
| A§2.1 `report` job | merged into `site` (job summary + site artifact) |
| A§2.1 `checks` content | runs after the matrix and uses its exports (L3, L4, L6 need them), not in parallel |
| A§1 ubc via `useblocks/ubc-action` | direct download with checksum (UA-02) |
| A§1 `uv` lock | `requirements.txt` with pinned versions instead of a lock file |
| A§4 `test_all.sh --checks` / `--product` | not implemented; `tools/check_all.sh` and `tools/build_product.sh` cover the same |

## 6. Next

- You (plan 8): **M-07** compare pages and **M-08** published site in the
  browser; **M-09** rulesets R9 (required checks: `checks`, `build (<product>)`,
  `site`) and R10 — the checks exist now.
- `nightly.yml` (A5, T§ L9 macOS): macOS needs another ubc install route than
  the Linux download (UA-01).
