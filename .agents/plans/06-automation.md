# Plan 6: Automation — CI and GitHub Pages

Step 6 of the [roadmap](00-roadmap.md). Automates every build and test that is
not yet automated, and publishes the documentation of **all products** built
with **sphinx-needs and ubCode side by side** on GitHub Pages of
`PhilipPartsch/variant_demo`.

Referenced: [02-basic-setup.md](02-basic-setup.md) (`B§`, local entry points
B§8), [03-mechanism-evaluation.md](03-mechanism-evaluation.md) (`V§`),
[05-test.md](05-test.md) (`T§`), [01-evaluation.md](01-evaluation.md) (`E§`,
group G answers the open automation questions).

## 0. Goals and definition of done

1. Every push and pull request builds all four products with both toolchains
   and runs the tests of T§ — with the **same scripts** developers run locally
   (`tools/build_product.sh`, `tools/build_all.sh`, `tools/test_all.sh`).
2. Every push to `main` publishes to the **`gh-pages` branch**, with **one
   folder per product variant**, served by GitHub Pages; for each product
   the **sphinx-needs** and the **ubCode** output can be opened and compared
   **side by side**.
3. A failing build or test never replaces the last good site.

"If not already done": a minimal CI (build matrix only) may already exist from
plan 2; this plan completes it.

| # | Done when |
|---|---|
| A1 | PRs to `main` run checks, the product build matrix and the tests; results visible in the PR and the job summary. |
| A2 | Push to `main` updates the `gh-pages` branch: one folder per variant (`<product>/`), landing page lists all products; GitHub Pages serves the branch. |
| A3 | Each product has sphinx-needs HTML, ubCode HTML, a side-by-side compare page, a needs diff (ubc vs Sphinx) and test reports. |
| A4 | The first CI run on `main` has verified the questions plan 1 could not test locally (§1.1). |
| A5 | Nightly platform run (T§ L9) reports separately. |

## 1. Prerequisites

| Item | Action |
|---|---|
| ubc in CI | `useblocks/ubc-action` (pinned SHA, **Linux only**) with `UBC_VERSION = "0.35.0"` pinned (the version the evaluation used). Free for public projects **with an OSI licence file** — add `LICENSE` first (E-R G3, U1). **No license secrets**: this repository is open source and needs no ubCode license (confirmed early by E§ G3; the private BMS repo is different). Fallback only if G3 fails: secrets as in the BMS demo |
| GitHub Pages | **Branch-based**: the branch `gh-pages` exists (empty orphan commit `ce0f2fc`, pushed 2026-10-08). Settings → Pages → Build and deployment → Source: **Deploy from a branch** → `gh-pages`, folder `/ (root)` — **enabled 2026-10-08** (status `built`, HTTPS enforced). The branch is written **only by CI**, never by hand. All repository settings: B§3.4 |
| Tool versions | Python via `.python-version`, dependencies via `uv` lock; sphinx-needs, sphinx-mounts, sphinx-codelinks[libclang] pinned (E§ A7) |
| System packages | CMake, Ninja, a C compiler, graphviz, libclang (E§ E5) |
| Actions | all third-party actions pinned to a commit SHA |

### 1.1 First-run verification (from plan 1)

Plan 1 could not test these without pushing an evaluation branch (the
repository stays clean), so the **first CI run on `main`** verifies them. Each
has a fallback ready:

| ID | Verified by the first run | Pass | Fallback |
|---|---|---|---|
| E§ G3 | `useblocks/ubc-action` **without licence inputs** → `ubc --version`, `ubc check`, `ubc build html` (needs `LICENSE` = MIT on `main`, B§3.4 R3) | all three succeed | ask useblocks; until then add licence secrets as in the BMS demo |
| E§ E5 | `sphinx-codelinks[libclang]` on `ubuntu-latest`; the preprocessor yields the same `IMPL_*` per product as on macOS | identical code needs to the local run | pin a libclang wheel / use a container image |
| E§ G4 | `pages` job pushes the variant folders and `.nojekyll` to `gh-pages`; Pages (branch source, already enabled) rebuilds | `…/variant_demo/<product>/sphinx/` and `…/<product>/ubcode/` reachable, `_static/` served | Pages source "GitHub Actions" (artifact deploy) |
| E§ G5 | open `…/<product>/compare.html` in a browser | both panes load | two links per product instead of iframes |
| 99 UB-14, CL-03 | no machine path in the published site: `grep -r 'file:///' gh-pages/` (ubCode HTML shows `local-url` as text, ubc `needs.json` carries it) | no match | `tools/make_site.py` strips / rewrites `local-url` in the ubCode HTML and the published `needs.json`, or `set_local_url = false` (see §6) |

Results are added to [01-evaluation-result.md](01-evaluation-result.md). The browser checks (G4, G5, UB-14) are
manual: [07-manual-steps.md](07-manual-steps.md) §3 (M-07, M-08).

## 2. Workflows

### 2.1 `ci.yml` — on pull request and push

```
checks ──────────────┐
build (matrix: D, N, B, A) ──► report ──► (main only) pages ──► gh-pages branch
```

| Job | Runs on | Steps |
|---|---|---|
| `checks` | ubuntu | install tools → T§ L1 (pytest `tools/tests/`) → drift check → Kconfig hygiene → condition registry → skill mirror check (three host locations) → `ubc agent doctor` → T§ L5 mutation tests |
| `build` (matrix `product` = the four defconfigs, generated list) | ubuntu | install tools + ubc → `tools/build_product.sh $product` (configure, `ubc check`, ubCode HTML, sphinx-needs HTML, both `needs.json`) → CTest + JUnit import (T§ L6) → golden + parity + content checks (T§ L3, L4) → upload artifact `site-<product>` (`build/site/<product>/`) and `test-<product>` |
| `report` | ubuntu | needs `checks`, `build` → job summary: table product × (build, ubc, Sphinx, parity, tests, coverage) |
| `pages` | ubuntu, push to `main`, all previous jobs green | check out `gh-pages` into `pages/` (`actions/checkout` with `ref: gh-pages`) → download the `site-<product>` / `test-<product>` artifacts → `tools/make_site.py` writes the variant folders and root files following the folder rules of §3.1 → `git add -A`, commit `site: <main sha>` → `git push origin gh-pages` with `GITHUB_TOKEN` (`contents: write` for this job only) |

Settings:

- `concurrency`: one run per ref; the `pages` job uses the group `gh-pages`
  with `cancel-in-progress: false`, so two deploys never race on the branch.
- Permissions: `contents: read` by default; only the jobs that push to
  `gh-pages` get `contents: write`.
- A push made with `GITHUB_TOKEN` does not trigger other workflows, so
  deploying to `gh-pages` cannot loop.
- The product matrix is generated from `configs/*_defconfig` (small setup job
  that emits JSON), so a new product needs no workflow change.
- Release-gated tests (T§ DOC-06) are skipped automatically while the pinned
  sphinx-needs has no `choose`.

### 2.2 `nightly.yml` — scheduled

| Job | Content |
|---|---|
| `platforms` | T§ L1–L3 on `ubuntu`, `macos`, (optional) `windows` (T§ L9); `useblocks/ubc-action` is Linux-only (E-R F-10), so macOS / Windows run the Sphinx path only, or install ubc by another route |
| `bms-pin` | rebuild against the pinned BMS artifacts and report if a newer BMS release exists |

## 3. GitHub Pages site on the `gh-pages` branch

### 3.1 Branch layout — one folder per variant

```
gh-pages  (branch root = site root)
├── .nojekyll                        required: Sphinx output has `_static/`, `_sources/` (Jekyll would hide `_*`)
├── index.html                       landing page (§3.2)
├── products.json                    manifest: products, configuration, commit, build time, tool versions
├── assets/                          CSS / JS for landing and compare pages
├── truck_diesel_eu/                 one folder per variant = defconfig name
│   ├── sphinx/                      sphinx-needs HTML
│   ├── ubcode/                      ubCode HTML (ubc build html)
│   ├── compare.html                 side-by-side view (§3.3)
│   ├── needs-diff.html              ubc vs Sphinx needs.json differences
│   ├── needs.sphinx.json, needs.ubc.json
│   └── tests/                       JUnit HTML report, coverage (if any)
├── truck_bev_nmc_eu/                same structure
├── bus_bev_lfp_eu/                  same structure
└── truck_bev_lfp_na/                same structure
```

URLs: `https://philippartsch.github.io/variant_demo/<product>/sphinx/`,
`…/<product>/ubcode/`, `…/<product>/compare.html`.

**Folder rules** (applied by `tools/make_site.py`):

| Rule | Why |
|---|---|
| A variant folder is named exactly like its defconfig (`configs/<product>_defconfig` → `<product>/`). | One name for a product everywhere: CMake Tools picker, build dirs, URLs. |
| Each deploy from `main` **replaces every variant folder completely** (delete, then copy the new build). | No stale pages from an earlier build of the same product. |
| A variant folder whose defconfig no longer exists is **removed**; `products.json` lists the folders the last deploy owned. | Retired products disappear from the site. |
| `.nojekyll` is always present. | Otherwise GitHub Pages hides Sphinx' `_static` and `_sources`. |
| One commit per deploy (`site: <main sha>`); if the branch grows too large, squash it to a fresh orphan commit (CI job, manual trigger). | History stays useful but bounded. |
| Optional later: `pr/<number>/<product>/` previews for pull requests from this repository, removed when the pull request closes. | Review of documentation changes per variant. |

Assembled by `tools/make_site.py` from the downloaded `site-<product>` and
`test-<product>` artifacts into the `gh-pages` working copy; the same script
writes the identical tree locally into `build/site/` for previews.

### 3.2 Landing page

One row per product, generated from `variants/<product>.json`:

| Product | Configuration | sphinx-needs | ubCode | Side by side | Needs diff | Tests |
|---|---|---|---|---|---|---|
| `truck_bev_nmc_eu` | truck · BEV · NMC · 800 V · MCS · EU | link | link | link | ✓ identical / n differences | ✓ 12/12 |

Header: commit SHA, build time, tool versions (ubc, sphinx-needs,
sphinx-mounts, sphinx-codelinks), BMS version pin.

### 3.3 Side-by-side compare page

- Two panes (CSS grid, 50 / 50, full height): left **sphinx-needs**, right
  **ubCode**, each an iframe of the product's output.
- A product selector switches both panes at once.
- A page selector opens the **same document** in both panes (document list from
  the Sphinx build; mapping to ubCode paths per E§ G2).
- Fallback if framing does not work (E§ G5): two buttons opening both outputs in
  separate tabs.

### 3.4 Needs diff page

Per product: needs only in Sphinx, only in ubc, and needs with different
field / link values — from the two `needs.json` files. Empty diff = parity
(T§ DOC-10).

## 4. Local reproduction

| CI job | Local command |
|---|---|
| `checks` | `tools/test_all.sh --checks` |
| `build` for one product | `tools/build_product.sh <product>` + `tools/test_all.sh --product <product>` |
| `pages` assembly | `tools/make_site.py build/site` → `python -m http.server -d build/site` → open `http://localhost:8000/` (same tree as the `gh-pages` branch) |

## 5. Rollout

1. Prerequisites (§1): `LICENSE` (MIT) pushed on `main`, `gh-pages` branch and Pages source (both done), repository settings B§3.4 R7, R8, R11, pinned versions (no licence secrets).
2. `checks` + `build` matrix (minimal CI, may already exist from plan 2); the first run on `main` verifies §1.1.
2a. Branch rulesets B§3.4 R9, R10 once the required checks exist ([07-manual-steps.md](07-manual-steps.md) M-09).
3. Tests of T§ wired into `checks` and `build` as they become available.
4. `report` job summary.
5. Site assembly (`tools/make_site.py`), landing page, compare page, needs diff.
6. `pages` job: deploy from `main` into the variant folders of `gh-pages` (§3.1).
7. (no eval job: `eval/*` branches stay local, T§ L7 runs locally.)
8. `nightly.yml`.

**Tool findings → plan 99:** every bug or gap found in a useblocks tool (ubc / ubCode, Pharaoh, Sphinx-Needs, Sphinx-Codelinks, sphinx-mounts, ubc-action, ubTrace, ubConnect, Sphinx-Test-Reports) is added to [99-tool-bugs.md](99-tool-bugs.md) in the same session: summary, marker `branch@commit` + file:line on a pushed branch, input, wrong output, workaround, two solutions. CI-specific findings (e.g. ubc-action, Linux libclang, Pages) use a marker to the workflow file and the run URL.

## 6. Open points and risks

- **ubCode HTML under a sub-path and in an iframe** (E§ G2, G5). Fallback:
  separate links.
- **ubc per-product HTML build** with the variant override (E§ G1). Fallback:
  configure each product in its own job (already the case in the matrix).
- **ubc without license in CI** is expected for this open-source repository; verified first in E§ G3. Since no secrets are needed, pull requests from forks also run the full ubc path.
- **Push races on `gh-pages`:** prevented by the shared concurrency group (§2.1).
- **Branch growth:** every deploy adds HTML for four variants × two
  toolchains; squash job if needed (§3.1).
- **Jekyll:** without `.nojekyll`, Sphinx assets under `_static/` are not served.
- **Local paths in the published site** (plan 99 UB-14, CL-03): ubCode HTML
  renders the codelinks `local-url` as plain text with the absolute path of
  the build machine (in CI: the runner's path), and ubc's `needs.json` exports
  it. Options: (1) `set_local_url = false` in `ubproject.toml` for everyone —
  simple, but Sphinx then loses the links to its generated source pages;
  (2) a CI-only override `-c 'codelinks.set_local_url = false'` — check first
  that it does not replace the whole `[codelinks]` table (UB-05); (3)
  `tools/make_site.py` removes / rewrites `local-url` in the published ubCode
  HTML and `needs.json` and fails the deploy if any `file://` remains. Decide
  with the first CI run (§1.1); the `file://` check stays in any case.
- **Build time:** four products × two toolchains × libclang analysis; use the
  matrix, caching (`uv`, compiler cache) and `fail-fast: false`.
