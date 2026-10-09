# Result of plan 2: Basic setup

Outcome of [02-basic-setup.md](02-basic-setup.md) (`B§`), executed 2026-10-08
on the local branch `setup/cv-platform` (from `main` `6ef4c49`). Reused the
working parts of `eval/open-questions` (plan 1).

**Status: done — D1–D8 met.** Merged to `main` by fast-forward and pushed
2026-10-09 (`origin/main` = `241dd1f`, tag `pre-cv-platform`); see §8.

## 1. Definition of done

| # | Criterion | Result |
|---|---|---|
| D1 | four products configure (CMake Tools + CLI) | ✓ CLI for all four (`tools/build_all.sh`); IDE files in place (`cmake-variants.json` generated, project kit, Debug fixed) — IDE re-check after the switch to the new product names is a manual step for you (§6) |
| D2 | `sphinx-build -W` per product, product shown | ✓ all four; landing page shows `product <name>` in both HTML outputs |
| D3 | `ubc check` / `ubc build` per product | ✓ all four, `ubc build html` at the default `--deny warning` |
| D4 | BMS needs of the right chemistry, none in diesel | ✓ 205 `BMS_*` needs in N/B/A (`chemistry` NMC resp. LFP, `status imported`, 9 tagged `interface`), 0 in D; integration page lists the interface needs |
| D5 | codelinks analyses the code of every built component | ✓ stubs analysed (no markers yet). Temporary probe (reverted): ENG marker only in D, `#if CONFIG_CHARGING__MCS` marker only in N, same-ID VCU marker from `#else` in D and `#if` in N/B |
| D6 | `ubc agent next` names `user_stories` | ✓ **for the diesel product**; on BEV products it reports `done` because the imported BMS needs are counted as stage output — finding F-14 |
| D7 | local entry point runs D1–D5 + checks | ✓ `tools/build_all.sh` green, also on a fresh clone of the branch |
| D8 | pushed and merged | ✓ fast-forward merge, pushed 2026-10-09 (no PR: merged locally on request) |

ubc/Sphinx parity per product: identical sets of need IDs (205/205 for BEV, 0/0 for diesel).

## 2. Commits on `setup/cv-platform` (local, not pushed)

| Commit | Content |
|---|---|
| `4aefe4d` | Replace the feature-tour demo with the CV platform skeleton |
| `43d41a6` | Add the CV metamodel: schema rules and review criteria |
| `e001130` | Import the BMS needs per chemistry |
| `f351514` | Set up the AI workflow for the CV platform |
| `731956c` | Add the local build entry points and repository checks |

No commit carries a trailer (`git log --format='%(trailers)' main..` is empty).
Local tag `pre-cv-platform` → `6ef4c49` (not pushed).

## 3. What was built (by rollout step)

| Step | Done |
|---|---|
| 2 BMS artifacts | No BMS-side release (the BMS repo is not changed). `tools/pin_bms.py --bms ../rollout-demo-bms` exports both chemistries with the BMS's own ubc config (`-c variant_data_file`) into `third_party/bms/0.1.0/` and does the BMS-side steps on the CV side: interface tags (all 9 IDs of B§5.2), `status = "imported"`, `docname` from `__source__`, drops `__source__`, clears codelinks `local-url` (absolute paths, F-17). `--check` verifies the pin. |
| 3 GitHub settings | read only; nothing changed (see §5) |
| 4 Skeleton | tag; old demo removed (`index.rst`, `requirements.rst`, `specifications.rst`, `tests.md`, `variants.json`, root `conf.py`); `quality/` → `metamodel/quality/`; folder tree of B§3; `Kconfig` (+ `src/<x>/Kconfig` menus via `rsource`), 4 defconfigs, generator with `--all --vscode --check`, `CMakeLists.txt` + `cmake/{kconfig,bms,active,docs}.cmake`, `.vscode/` (settings, kit, generated variants, tasks with generated product list, extensions), C stubs + CTest per component, docs skeleton, README, `requirements.txt` (pinned toolchain), `.gitignore` (`build/` explicit) |
| 5 Metamodel | `ubproject.toml`: 10 types with BMS colours/styles, 11 links (`allocates` with `parse_variants`), BMS fields + `value` + `product` (enum = products, drift-checked), `status` enum incl. `imported`, named variants, 4 `variant_sources` rules. `metamodel/schemas.json`: the 32 BMS rules, every `select` local-only, `product` required on test_result/gap, plus `alloc-target-prefix`, `alloc-target-interface`, `bms-arch-allocates` (select by `docname` `^subsystems/bms/`) — all three verified with temporary probes in ubc **and** Sphinx |
| 6 BMS import | `cmake/bms.cmake` selects `nmc` / `lfp` / `empty.needs.json` from `CONFIG_BMS__*`; `[[needs.external_needs]]` with `id_prefix = "BMS_"` |
| 7 Code analysis | 6 codelinks projects (`vcu`, `chg`, `eng` + `_tests`), libclang preprocessor on `build/compile_commands.json`, fallback `build/active` |
| 8 AI workflow | `[workflow]` with the 10 stages of B§7.2 (authoring texts from BMS + C§6.2 rules), `exempt_status = ["imported"]`, `[quality]` with `variant_consistency` required; `draft-allocation` in all three locations; `.mcp.json`; `config-validate` ok, `doctor` ok, mirror check 13/13 |
| 9 Entry points | `tools/build_product.sh`, `tools/build_all.sh` (saves/restores `build/active/` + `build/compile_commands.json`), `tools/env.sh` (ubc of the ubCode extension, venv), `tools/check_variants.py` (condition registry, bare booleans, branch coverage, `CONFIG_*` symbols, alternatives complete — negative probe fails as expected), CMake targets `docs` / `docs_ubc`, `ubc script build-all` |

`ubc agent install --detect` was **not** re-run: the installed `vmodel` v9
skills already cover every skill the new stages name and `doctor` reports them
current; `--detect` would have derived a workflow from the (empty) graph.
`.agents/plans/` untouched.

## 4. Findings

| # | Finding | Handling |
|---|---|---|
| F-14 | `ubc agent status` / `next` count imported needs (`status imported`) as stage output; `exempt_status` does not exclude them. BEV products show every stage `done` with an empty CV graph | D6 checked on diesel; `-c 'needs.external_needs = []'` gives the right answer on BEV. Feedback to useblocks; re-check in V19/V20 |
| F-15 | ubc rejects the whole BMS import when a declared field is `nullable = false` and the export carries `null` (`code_url`) | `code_url` declared nullable (as in the eval) |
| F-16 | Sphinx `needs.json` drops external needs (`needs_builder_filter` default `is_external==False`); ubc keeps them and ignores `builder_filter` | `[needs] builder_filter = ""` → parity |
| F-17 | BMS export carries absolute `file://` paths in codelinks `local-url` | `pin_bms.py` clears them; refuses to pin if a home path remains |
| F-18 | BMS rule `coverage-arch-refines-back` would warn on every BMS black-box arch (they are allocated, not refined) | rule selects `docname ^subsystems/(vcu|chg|eng)/` (no `not` in sphinx `select`, no look-ahead in ubc regex). The workflow gate of stage `swreqs` may report the same — check in V20 |
| F-19 | `file(COPY_FILE)` fails when `build/active/` does not exist yet (fresh clone) | `file(MAKE_DIRECTORY)` first |
| — | Missing `VARIANT` removal on configure failure (E-R D3) | fixed: all four active files removed; probe with a broken defconfig and an unknown product |
| — | ubc `build html` alpha: needtable over all needs truncates at 100 and fails `--deny warning` | report page filters `is_external == False` |

## 5. Deviations from the plan

| Plan | Deviation | Why |
|---|---|---|
| B§3 `tools/import_test_results.py`, `import_gaps.py` | not ported yet | the BMS versions parse Python markers / pytest JUnit; a C/CTest port cannot be validated without markers and a report → with C§5 code / T§ IMP-01/02 |
| B§5.2 BMS release artifacts | pinned from the local BMS checkout (commit `38c9f30`, version 0.1.0), not from a BMS release | BMS repo unchanged; same files, provenance in `pin_bms.py` |
| B§5.3 `base_url` | placeholder `https://bms-docs.invalid/0.1.0` | BMS docs are not published |
| B§3 output `build/docs/<product>/` | `build/site/<product>/{sphinx,ubcode}/` | as B§8 and the gh-pages layout |
| B§3.2 agent reinstall | not re-run | see §3 |

## 6. Decisions needed before D8 (nothing outward has been done)

1. **BMS content becomes public.** `third_party/bms/0.1.0/*.needs.json` hold the
   full needs (titles, content) of the **private** BMS repo. Pushing the branch
   publishes them in the public `variant_demo`. OK — or fetch them at configure
   time instead of committing them?
2. **GitHub settings** (B§3.4): R7 allow GitHub-owned + `useblocks/ubc-action`
   + `astral-sh/setup-uv`, require SHA pinning (now: all allowed, no pinning);
   R8 token stays `read` (already); R11 delete head branches on merge (now
   off); R13 description + topics (now empty; homepage already set).
3. **Push**: tag `pre-cv-platform`, branch `setup/cv-platform`, open the PR,
   merge (no CI yet — `build_all.sh` is green locally).
4. **IDE re-check** (you): select kit `cv-platform` and switch the four new
   product names in the CMake Tools status bar; ubCode should follow
   (`build/active/VARIANT`).
5. **Cleanup** after the merge: delete the local `eval/open-questions` branch.

## 7. Handover

- Plan 3 (`eval/mechanisms` from `main` after the merge): re-check F-14 in
  V19/V20 and F-18 for the `swreqs` gate; `check_variants.py` covers CHK-01/02.
- Plan 4: importers (§5), real BMS `base_url` once published.
- Plan 6: CI calls `tools/build_product.sh <product>` per matrix job and the
  once-per-repo checks of `build_all.sh`; set `UBC` to the action's ubc.

## 8. Decisions taken (2026-10-09)

| Item | Decision |
|---|---|
| BMS content public | yes — `third_party/bms/0.1.0/*.needs.json` committed and pushed |
| Plans | un-ignored and committed by the user (`241dd1f`); now tracked on `main` |
| Merge | `main` fast-forwarded to `setup/cv-platform`; branch kept (local and on `origin`) |
| Push | `main` + tag `pre-cv-platform` pushed, no AI trailers |
| R7 | **set**: GitHub-owned actions + `useblocks/ubc-action@*` + `astral-sh/setup-uv@*`, SHA pinning required, verified creators not allowed |
| R8 | unchanged (`read`) |
| R11 | **not set** — merged branches are kept |
| R13 | **set**: description and topics `kconfig`, `sphinx-needs`, `ubcode`, `variant-management`; homepage already the Pages URL |
| R9, R10 | with plan 6 (CI checks must exist first) |
