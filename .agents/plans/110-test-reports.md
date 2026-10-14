# Plan 110: Re-evaluate Sphinx-Test-Reports for test result management

Triggered plan (not part of the numbered execution order). It decides whether the
CV platform can replace its own importer `tools/import_test_results.py` with the
useblocks tool [Sphinx-Test-Reports](https://sphinx-test-reports.readthedocs.io/en/latest/index.html)
("STR"). Plan 99 §1 lists STR as "candidate to replace `tools/import_test_results.py`".

**Trigger 2026-10-14 (T1, T4): re-run open.** ubCode / ubc 0.37.0 reads the STR
directives (`test-file`, `test-suite`, `test-case`, `:auto_suites:` /
`:auto_cases:`) with a `[test_reports]` table and reports mistakes as
`needs.test_report_*` (ubCode changelog 0.37); the pin is now Sphinx-Needs
9.0.0 (plan 20). The baseline below is the state before.

**Status (baseline 2026-10-12): not possible.** ubCode / ubc 0.35.0 does not know
the STR directives, and the STR command-line converter has bugs that block the
only other route that works in both toolchains (§3). This plan is therefore a
**re-run plan**. On every trigger (§1), repeat the analysis in a shadow folder
(§4), compare it with the baseline (§3), and take the follow-up given in the
outcome table (§5).

Referenced: [02-basic-setup.md](02-basic-setup.md) (`B§4.3`), [05-test.md](05-test.md)
(`T§` IMP-01, CODE-01…04, CNT-01, CNT-05), [06-automation.md](06-automation.md),
[99-tool-bugs.md](99-tool-bugs.md) (UB-07, UB-13, PH-06),
[20-choose-migration.md](20-choose-migration.md) (same gate pattern).

Global rules that apply here (roadmap):

- **Rule 1: released, ubCode-supported directives only.** STR directives are allowed
  only once a **released** ubc / ubCode supports them.
- **Rule 3: ubc and Sphinx give the same result.** Every route must keep the parity
  check of `tools/build_product.sh` green.
- **Rule 4: tool bugs go into plan 99.** The findings in §7 are written ready to
  paste into plan 99 but are **not in plan 99 yet**. Transfer them on the first
  re-run, after reproducing each one on a pushed commit.
- **The analysis does not touch the repository.** Other agents may be working in it
  at the same time. Work only in a shadow folder in the session scratchpad and
  delete it completely at the end (§4.6).

## 0. Goal

Test evidence (`test_result` needs) is produced by a **released useblocks tool**
rather than repository code, and it stays:

- per product (the results of product X are visible only in product X),
- linked by `results_for` to the `TEST_*` need, with one result per test case,
- identical in ubc and Sphinx, warning-free, and covered by the schema rules,
- reproducible from the CTest run of `tools/build_product.sh`, locally and in CI.

## 1. Triggers

Re-run §4 when any of these happens:

| # | Trigger | How to notice |
|---|---|---|
| T1 | New ubCode extension / ubc release | `ls ~/.vscode/extensions/ \| grep useblocks.ubcode`, `ubc --version`, ubCode changelog; plan 99 version table |
| T2 | New STR / `ub-test-reports` release (e.g. 3.0.0) | `curl -s https://pypi.org/pypi/sphinx-test-reports/json`, same for `ub-test-reports`; STR changelog |
| T3 | One of the findings in §7 is reported as fixed | plan 99 entries / useblocks release notes |
| T4 | The sphinx-needs pin changes (`requirements.txt`) | the STR minimum is 8.5.0 in 3.0 |

Before starting, search the ubCode docs (the ubcode MCP server's documentation
search, or the website) for "test-file", "test_reports", "Sphinx-Test-Reports" and
"JUnit". This is a cheap first check for T1.

## 2. Current state (unchanged until a migration)

### 2.1 Data flow

```
tests/<x>/test_<x>.c        one executable per component; each case prints "PASS|FAIL TEST_<id>"
   │  add_test(test_<x>)    tests/CMakeLists.txt: ONE CTest test per executable
   ▼
ctest --output-junit        build/site/<p>/junit.xml   (tools/build_product.sh:32)
   ▼
tools/import_test_results.py   manual step after tools/build_all.sh; parses the system-out
   │                           lines, looks up TEST_* in build/site/<p>/ubc.needs.json,
   │                           computes chain_reqs (test → verifies → refines → satisfies)
   ▼
docs/_global/test_results.rst  COMMITTED snapshot, one `.. if:: var.meta.product == '<p>'`
                               block per product, TRES_<id>__<PRODUCT> needs
```

### 2.2 Everything that depends on it (the migration checklist)

| Where | What |
|---|---|
| `ubproject.toml` (types, links, fields 222–254, stage `test_results`) | type `test_result` / `TRES_`, link `results_for`, fields `outcome`, `runtime_s`, `test_run_label`, `chain_reqs`, `product` |
| `metamodel/schemas.json` | `id-prefix-test_result`, `trace-test_result-results_for` (min 1 / max 1), `field-test_result-run-evidence`; all select `is_external == false` |
| `docs/_global/test_results.rst`, `docs/index.rst:73`, `docs/method/{testing,metamodel}.rst` | page and its description |
| `tests/*/test_*.c` | the `PASS/FAIL <TEST id>` output convention |
| `tools/make_site.py:115` | `tests_page()` parses the same lines from `junit.xml` |
| `tools/import_gaps.py:19` | `results_for` in its link list |
| `tools/tests/test_l1_tooling.py:195` (IMP-01), `test_l6_code.py` (CODE-01…03), `test_l4_content.py:28,32,109`, `test_l3_docs.py:19`, `normalize.py:12`, `update_golden.py` | tests and oracles |

### 2.3 Weaknesses STR should fix

- Our own code and our own stdout convention, parsed in three places.
- **CTest granularity:** one CTest test per executable. A single failing case fails
  the whole executable, and every case gets the executable's runtime.
- `outcome` can only become `passed` or `failed`; `error` and `skipped` never occur.
- A manual, committed snapshot (295 lines) that goes stale. CODE-03 only detects
  that it is stale.

## 3. Baseline results (2026-10-12)

Versions: ubc / ubCode 0.35.0, `sphinx-test-reports==2.0.0` (released
2026-09-11; `ub-test-reports` 1.0.0 is on PyPI but was not tested),
`sphinx==8.2.3`, `sphinx-needs==8.5.0`, CMake / CTest 4.4.2. Base commit
`main@9546209`.

| # | Experiment (§4.4) | Baseline result | Verdict |
|---|---|---|---|
| E1 | Converter on today's `junit.xml` | 2 needs (`test_result__test_vcu__test_vcu_woszt`, …), **one per executable**, no link to `TEST_*` | needs per-case CTest |
| E2 | CTest, one `add_test` per case with `LABELS` | one `<testcase name="TEST_A">` per case with its own `status`/`time`/`<failure>`; the **only** property CTest writes is `cmake_labels` | ✓ |
| E3 | `--link-property cmake_labels=results_for`, label = test id | `results_for: ['TEST_A']` | ✓ |
| E4 | CTest `DISABLED` case (`status="disabled"`) | `result: passed` | ✗ STR-01 |
| E5 | `[test_reports.case] prefix = "TRES_"`, `deterministic_case_ids = true` | ignored by the converter; IDs `<need_type>__<class>__<name>_<hash5 lowercase>`, outside `id_regex` | ✗ STR-02 |
| E6 | `[[needs.external_needs]]` + `id_prefix = "TRES_"` | imported in ubc **and** Sphinx; links resolve; Sphinx fills `results_for_back`; `id_regex` not applied to external needs in either tool; undeclared STR fields → one warning per source | ✓ with warnings |
| E7 | `.. test-file::` directive | **ubc: `warning[block.directive_unknown] Unknown directive: 'test-file'`**, no needs. Sphinx: `NeedsApiConfigException: test_result already exists as need type` when the type is in `[[needs.types]]` and in `[test_reports.case]` | ✗ UB-17, STR-03 |
| E8 | `.. needimport::` of the converter output | ubc imports all needs, Sphinx refuses them (`id_regex`) → silent parity break | ✗ UB-16 |
| E9 | E6 with the STR fields declared in `[needs.fields]` | **ubc drops the whole source** (`needs_schema…default … null; the source contributed no needs`); Sphinx is fine. Stripping `needs_schema` fixes ubc | ✗ UB-15 |
| E10 | Field values (E6 + workaround) | `result`, `time`, `results_for`; no product, no run timestamp, no `chain_reqs` | metamodel change needed |
| E11 | `test-file` inside `.. if:: var.meta.product == …` | not reachable (E7) | open |
| E12 | Directive links via `property_link_types` | not reachable (E7) | open |
| E13 | ubc ↔ Sphinx ID parity for directive-created cases | not reachable (E7) | open |
| E14 | ubCode HTML / IDE rendering of STR needs | not reachable (E7) | open |

**Baseline conclusion:** no route meets rules 1 and 3 without workarounds.

- Directives (route B): blocked by **UB-17** in ubc.
- `needimport` (route C): blocked by **UB-16**.
- Converter + external needs (route D): works only with two workarounds (UB-15,
  STR-02) plus a latent wrong result (STR-01).

Keep the importer.

## 4. Re-run procedure

### 4.1 Shadow folder

```bash
S="<session scratchpad>/shadow110"     # never inside the repository
mkdir -p "$S/in"
cp build/site/*/junit.xml "$S/in/"     # read-only copies; build/ may be missing → run E2 first
UBC="$(ls -d ~/.vscode/extensions/useblocks.ubcode-*/server/cli/ubc | sort -V | tail -1)"
```

Do not use `git worktree`, because it writes to `.git`. Do not run the repository's
`tools/*.sh`, because they write to `build/active/` and `build/site/`.

### 4.2 Environment

```bash
python3.12 -m venv "$S/venv"
"$S/venv/bin/pip" install "sphinx==8.2.3" "sphinx-needs==<pin from requirements.txt>" \
    "sphinx-mounts==0.2.0" "sphinx-test-reports[sphinx]==<newest>"   # + "ub-test-reports==<newest>" if released
"$UBC" --version
```

Record every version in the result table (§4.5).

### 4.3 Minimal projects

- **CMake project** `$S/cm`: one C executable that takes the test id as `argv[1]`
  and fails for `TEST_B`. Register `TEST_A`, `TEST_B` (one `add_test` each, `LABELS`
  = test id) and `TEST_C` (`DISABLED TRUE`). Then run
  `ctest --output-junit $S/in/cm.xml`.
- **Docs project** `$S/mini/<route>`: copy the relevant parts of the repository
  `ubproject.toml`, namely `[needs] id_required`, **the same `id_regex`**,
  `builder_filter = ""`, types `test` + `test_result`, link `results_for`, and a
  `[needs.variants]`/`variant_data_file` pair for E11. Add `docs/conf.py` with
  `needs_from_toml = "../ubproject.toml"`, `needs_build_json = True`, and an
  `index.rst` with `.. test::` needs `TEST_A`, `TEST_B`. Use one project per route:
  `ext` (E6/E9), `imp` (E8) and `dir` (E7, E11–E14).
- In each project run `"$UBC" check`, `"$UBC" build needs -o ubc.json`,
  `"$UBC" build html -o ubc_html`, and
  `"$S/venv/bin/sphinx-build -E -b html docs out"`. Then compare the IDs, `type`,
  `results_for` and result field of `ubc.json` against `out/needs.json`.

### 4.4 Experiments

Run E1–E14 from §3. If a new ubc supports the directives, E11–E14 are the
important ones:

| # | What to check for the directive route |
|---|---|
| E7 | `ubc check` knows `test-file` / `test-suite` / `test-case` / `test-results`; ubc reads `[test_reports]` from `ubproject.toml`; same need set in ubc and Sphinx |
| E7b | `test_result` declared once: in `[[needs.types]]` **or** `[test_reports.case]`. Which one does ubc need? Does STR-03 still abort Sphinx? |
| E11 | `test-file` inside `.. if:: var.meta.product == '<p>'` and with a path that varies per product. Options: one block per product pointing to `build/site/<p>/junit.xml`, or one file `build/active/junit.xml`, which needs a copy step in `build_product.sh`. Check `tr_rootdir` / `rootdir` relative to the repo root in ubc and Sphinx |
| E12 | `property_link_types = { cmake_labels = "results_for" }` makes `results_for` → `TEST_A` in **both** tools |
| E13 | Identical IDs in ubc and Sphinx (deterministic or hashed); IDs match `id_regex` / `TRES_`; IDs are stable over two CTest runs with different timings |
| E14 | ubCode HTML and the IDE (hover, needs explorer) show the results; the `test-report` / `test-results` tables render in ubc HTML; no absolute local paths in the output (compare UB-14) |
| E15 | Schema rules: are directive-created needs `is_external == false`? Do the rules `trace-test_result-results_for` and `field-test_result-run-evidence` fire correctly, or do they need STR field names? |
| E16 | Workflow: `ubc agent gaps` / stage `test_results` counts the new needs (PH-06) |

### 4.5 Result record

Add a dated column next to "Baseline result" in §3: versions, ✓ / ✗ per
experiment, and new finding IDs. Do not delete the baseline column; the history
shows which release fixed what.

### 4.6 Cleanup (mandatory)

```bash
rm -rf "$S"; test ! -e "$S" && echo removed
git status --short      # must show no changes made by this analysis (other agents' files excepted)
```

## 5. Outcome → follow-up

| Outcome of the re-run | Route | Follow-up |
|---|---|---|
| E7 + E11–E15 ✓ (ubc supports the STR directives, parity, product gating, links) | **B: directives** | Write the migration plan (§6.2 B) and start a decision with the user |
| E7 ✗, but STR-01, STR-02 and UB-15 fixed (E4, E5, E9 ✓ without workarounds) | **D: converter + `[[needs.external_needs]]`** | Write the migration plan (§6.2 D) |
| E7 ✗ and the D blockers still open | — | Keep the importer; update §3 and plan 99; wait for the next trigger |
| Only UB-16 fixed | C (`needimport`) is still worse than D (it needs a committed file or a docs-time path) | No action |

Whichever route is chosen, §6.1 is a prerequisite.

## 6. Migration outline (only after a positive re-run)

### 6.1 Prerequisite: one CTest test per test case

Needed by every STR route (E1 vs E2). It can also be done earlier on its own merits:
per-case results and runtimes, and `ctest -R TEST_…`. That is a decision for the
user, not part of this plan's trigger.

1. Each test executable takes the test id as `argv[1]` and exits ≠ 0 on FAIL **and
   on an unknown id** (drift guard). Without an argument it runs all cases.
2. In `tests/CMakeLists.txt`, call `add_test(NAME TEST_<id> COMMAND test_<x> TEST_<id>)`
   and set `LABELS TEST_<id>` (exactly one label). Gate the case list with the same
   `CONFIG_*` as the `#if` in the C file; Kconfig symbols are CMake variables via
   `autoconf.cmake`.
3. The importer, `make_site.py` and `test_l6_code.py` map by `<testcase name>` +
   `status` instead of parsing `system-out`.

### 6.2 Route-specific steps

**B: directives** (if E7, E11–E15 ✓)
- `[test_reports]` in `ubproject.toml` (case type `test_result`, `property_link_types`,
  `rootdir`); add the extension to `conf.py`; pin it in `requirements.txt`.
- `docs/_global/test_results.rst`: per product, an `.. if::` with `test-file`
  (or one `build/active/junit.xml`, per E11), plus `test-results` / `needtable`.
- `build_product.sh`: CTest must run **before** `ubc` and Sphinx; this is already
  the order.

**D: converter + external needs** (if E4, E5, E9 ✓)
- After CTest, `build_product.sh` runs `test-reports build needs -o build/active/test_results.needs.json`.
- CMake configure writes an empty but valid stub (like the empty BMS file), and
  `[[needs.external_needs]]` points at it. The file is per product, so no `if`
  blocks and no `product` field are needed.
- Rules for **external** test results in `schemas.json`; today's rules select
  `is_external == false`.

**Both routes**
- Metamodel: STR vocabulary (`result`, `time`, …) instead of `outcome` /
  `runtime_s`; declare every STR field (UB-13). Replace `chain_reqs` with a view
  (`needtable` / `needflow` over `results_for` → `verifies` → …).
- Delete `tools/import_test_results.py` and the committed snapshot.
- Update tests IMP-01 and CODE-03 (no staleness any more), the CNT `product`
  assertion (only for `gap`), `normalize.py` (`time`), `make_site.py`, and the
  docs in `docs/method/`.

### 6.3 Decisions to take with the user then

| # | Question | Proposal |
|---|---|---|
| D1 | Route B or D (if both are possible) | B: no extra build step, and STR's report tables are available |
| D2 | Field vocabulary: STR or ours (via post-processing) | STR; post-processing would be our own code again |
| D3 | Results at build time or a committed snapshot | build time; the evidence is the published site and the CI artefact |
| D4 | `chain_reqs`: drop and add a view, or keep | drop, add a view |
| D5 | Package: `sphinx-test-reports` or `ub-test-reports` (3.0 split) | the one the chosen route needs; pin exactly |

## 7. Tool findings for plan 99 (baseline, to transfer)

Reproduced in a scratch copy based on `main@9546209`. Before transferring them to
plan 99, reproduce each one on a pushed commit (rule 4). On every re-run, mark the
entries that are fixed (§4.5).

### STR-01 CTest `status="disabled"` reported as passed
- **Tool:** sphinx-test-reports 2.0.0 (`junitparser.py:204-212`)
- **Input:** CTest `--output-junit` with `set_tests_properties(T PROPERTIES DISABLED TRUE)` → `<testcase … status="disabled">` without a result child.
- **Wrong output:** `result: passed`. Expected `disabled` / `skipped`.
- **Workaround:** none needed yet (no disabled tests).
- **Solution A:** treat every `status` other than `run` (`disabled`, `notrun`) as not passed.
- **Solution B:** a CTest dialect (as for googletest), detected by `cmake_labels` / `<testsuite name="(empty)">`.

### STR-02 Converter ignores the configured prefix; IDs fail a strict `id_regex`
- **Tool:** sphinx-test-reports 2.0.0 (`needs_export.py:214`, `identity.py`)
- **Input:** `[test_reports.case] prefix = "TRES_"`, `deterministic_case_ids = true`, `test-reports build needs …`.
- **Wrong output:** `test_result__TEST_A__TEST_A_isagy`. The prefix is unused, and the lowercase hash conflicts with `id_regex = "^[A-Z]+_[A-Z][A-Z0-9_]*$"`. External needs are not regex-checked, so this only shows with `needimport`.
- **Workaround:** `[[needs.external_needs]] id_prefix`.
- **Solution A:** the converter uses `[test_reports.case].prefix`, with an option for upper-case IDs.
- **Solution B:** an ID template option (e.g. `{prefix}{name}`) for cases whose name is already unique.

### STR-03 Type declared in `[[needs.types]]` and `[test_reports.case]` aborts Sphinx
- **Tool:** sphinx-test-reports 2.0.0 with sphinx-needs 8.5.0 `needs_from_toml`
- **Input:** one `ubproject.toml` with `[[needs.types]] directive = "test_result"` and `[test_reports.case] type = "test_result"`.
- **Wrong output:** `NeedsApiConfigException: test_result already exists as need type`, and the build aborts. Expected: reuse the declared type, or a typed `test_reports.*` warning.
- **Workaround:** declare the type once. ubc needs it in `[[needs.types]]`.
- **Solution A:** skip `add_need_type` when the type already exists with compatible settings.
- **Solution B:** `[test_reports.case]` references an existing `[[needs.types]]` entry.

### UB-15 External `needs.json` with `needs_schema` `default: null` dropped entirely
- **Tool:** ubc 0.35.0
- **Input:** `[[needs.external_needs]]` on a `test-reports build needs` output, with the STR fields declared in `[needs.fields]`.
- **Wrong output:** `needs_schema…default could not be read: Value cannot be converted to string: null; the source contributed no needs`; 0 of 3 needs imported. Sphinx imports all 3.
- **Workaround:** strip `needs_schema` from the file before import.
- **Solution A:** accept `null` as "no default" (it is valid JSON Schema).
- **Solution B:** on a schema mismatch, ignore the `needs_schema` block, keep the needs, and warn.

### UB-16 `needimport`: ubc skips `id_regex` and the unknown-key warning
- **Tool:** ubc 0.35.0
- **Input:** `.. needimport:: tr.needs.json` with `:id_prefix: TRES_`, IDs `TRES_test_result__…`, `id_regex = "^[A-Z]+_[A-Z][A-Z0-9_]*$"`.
- **Wrong output:** ubc imports all 3 needs and reports "No errors found". Sphinx refuses all 3 (`does not match configured regex`) and warns about unknown keys. The result is a silent ubc ↔ Sphinx difference.
- **Workaround:** do not use `needimport` for test results.
- **Solution A:** apply `id_regex` to imported needs, as Sphinx does.
- **Solution B:** at least warn, as ubc already does for external sources (`needs.external`).

### UB-17 (gap) Sphinx-Test-Reports directives unknown to ubc
- **Tool:** ubc 0.35.0 / ubCode
- **Input:** `.. test-file::` in an rst file.
- **Wrong output:** `warning[block.directive_unknown] Unknown directive: 'test-file'`; no test needs in ubc, the IDE or the ubCode HTML.
- **Workaround:** keep `tools/import_test_results.py`.
- **Solution A:** ubc supports the STR directives and reads `[test_reports]` from `ubproject.toml`.
- **Solution B:** ubc runs the STR conversion itself for a `[[needs.external_needs]]` entry that points at a JUnit file.

## 8. Risks for a later migration

- **The CTest case list duplicates the `#if CONFIG_*` gates** (§6.1). This is caught
  by the "unknown id" exit and by the check that every `TEST_*` has exactly one
  result.
- **`LABELS` as the link carrier** (E3/E12): any extra label becomes a second
  `results_for` target. Rule: exactly one label per test; the max-1 schema rule
  stays.
- **External needs** (route D) are outside the `is_external == false` rules and the
  Pharaoh stage counts (PH-06). UB-07: ubc does not fill back-links on external
  needs.
- **STR 3.0** renames modules (`sphinxcontrib.test_reports` → `sphinx_test_reports`
  / `ub_test_reports`) and moves the converter. Pin exactly and re-run §4 on every
  upgrade.
