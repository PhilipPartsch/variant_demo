# Plan 998: Re-check the tool bugs of plan 999 on new tool versions

Triggered re-run plan (not part of the numbered execution order). useblocks
releases new versions of its tools regularly. On each release, this plan
re-tests the entries of [999-tool-bugs.md](999-tool-bugs.md) on the new
version, records per entry whether it is still open, fixed or changed, and
lists the workarounds in this repository that a fix makes removable.

Plan 999 says (§1): "The findings were made with the older versions; entries
not marked fixed are not re-tested on the new ones yet." This plan closes that
gap. Its **first run** re-tests every open entry on the versions pinned today
(ubc / ubCode 0.37.0, Sphinx-Needs 9.0.0, Sphinx-Codelinks 2.0.0,
sphinx-mounts 0.3.0, Sphinx-Test-Reports 3.0.0 / `ub-test-reports` 1.1.0).

Referenced: [999-tool-bugs.md](999-tool-bugs.md) (the record),
[110-test-reports.md](110-test-reports.md) (same re-run pattern; STR entries),
[20-choose-migration.md](20-choose-migration.md) (how a version raise is done),
[08-manual-steps.md](08-manual-steps.md) (M-04 PH-01, M-12 hand-over),
[05-test.md](05-test.md) (`T§` test ids named in the entries).

Global rules that apply here (roadmap):

- **Rule 3: ubc and Sphinx give the same result.** Many entries are parity
  breaks; "fixed" means both toolchains agree again.
- **Rule 4: tool bugs go into plan 999.** Plan 999 stays the only record of
  the entries. This plan records only its run log (§7); new findings of a run
  become new plan 999 entries in the same session.
- **The re-check does not touch the repository.** Other agents may be working
  in it. Work only in a shadow clone in the session scratchpad and delete it
  at the end (§4.6). Removing a workaround or raising a pin is a follow-up
  (§5), never part of the run.
- Plan changes (998, 999) stay uncommitted until the user asks.

## 0. Goal

After each run:

- every entry in plan 999 has a **Status** line naming the version it was last
  checked on and the result (§3);
- every fixed entry names the version that fixed it, and the workaround in the
  repository that can now go is listed as a follow-up (§5);
- every new problem found on the way is a new plan 999 entry.

## 1. Triggers

Run §4 when any of these happens:

| # | Trigger | How to notice | Entries to re-check (§6) |
|---|---|---|---|
| T1 | New ubCode extension / ubc release | `ls ~/.vscode/extensions/ \| grep useblocks.ubcode`; `"$UBC" --version`; ubCode changelog | UB-*, PH-*, and every entry whose tool column names ubc (SN-07, CL-02, CL-03, SM-01, STR-04) |
| T2 | New Sphinx-Needs release | `curl -s https://pypi.org/pypi/sphinx-needs/json \| jq -r .info.version`; changelog | SN-*, UB-12, UB-13, UB-17, UB-19, STR-03 |
| T3 | New Sphinx-Codelinks release | same for `sphinx-codelinks` | CL-* |
| T4 | New sphinx-mounts release | same for `sphinx-mounts` | SM-01 |
| T5 | New `sphinx-test-reports` / `ub-test-reports` release | same for both packages | STR-*, UB-16, PH-12, PH-13; also trigger T2 of plan 110 |
| T6 | New commit / tag of `useblocks/ubc-action` | `gh api repos/useblocks/ubc-action/commits/main --jq .sha` against the SHA in UA-02 | UA-* |
| T7 | useblocks reports a fix (release notes, reply to the M-12 hand-over) | release notes, issue replies | the named entries |

One-shot version check (compare with the "Version here" column of plan 999 §1):

```bash
UBC="$(ls -d ~/.vscode/extensions/useblocks.ubcode-*/server/cli/ubc | sort -V | tail -1)"
"$UBC" --version
for p in sphinx-needs sphinx-codelinks sphinx-mounts sphinx-test-reports ub-test-reports; do
  printf '%-22s %s\n' "$p" "$(curl -s "https://pypi.org/pypi/$p/json" | jq -r .info.version)"
done
```

Always call `"$UBC"`, never a bare `ubc`: the `ubc` on `PATH` can be an older
release (plan 110 §4.1). Before a T1 run, also search the ubCode docs (ubcode
MCP `search_docs`) for the keywords of the entries in scope: a documented fix
or a documented design decision changes the expected result.

## 2. Scope

- **Re-checked:** every entry of the triggered tool(s) that is not marked
  fixed or resolved (§1 column "Entries to re-check").
- **Regression check (cheap):** entries marked fixed or resolved (UB-17,
  UB-18, CL-06) are re-run only when their repository test exists (NEG-16 for
  CL-06) or when the fix's area changed in the release notes.
- **Full build:** on every run, the whole repository builds once on the new
  version (§4.4). This finds new problems and is the go / no-go input for a
  version raise.
- **Out of scope:** Sphinx, kconfiglib, CMake, libclang (as in plan 999);
  changing the repository.

## 3. Status vocabulary

Each re-checked entry in plan 999 gets (or updates) one line, the same form
CL-06 already uses:

```
- **Status:** <result> on <tool> <version> (<date>, plan 998 run <n>): <one sentence of evidence>.
```

| Result | Meaning | Overview table in plan 999 §2 |
|---|---|---|
| **open** | reproduced with the same wrong output | unchanged |
| **changed** | still wrong, but the output differs; update "Wrong output" | summary updated |
| **fixed in X** | the expected output from the entry is produced | append `— **fixed in X**` |
| **resolved** | the tool changed its design so the entry no longer applies (as UB-17) | append `— **resolved** with X` |
| **not reproducible** | the wrong output is gone, but no release note explains it; re-check the input before calling it fixed | append `— not reproducible on X` |
| **regression** | an entry marked fixed is wrong again | severity raised one level, append `— **regression in X**` |

Also update plan 999 §1: the "Version here" column, and the sentence about
which entries are re-tested (`re-tested on <versions>, <date>, plan 998`).

## 4. Run procedure

### 4.1 Shadow clone

```bash
S="<session scratchpad>/shadow998"      # never inside the repository
git clone --no-local "$PWD" "$S/repo"   # full clone: markers on main and content/cv-platform
git -C "$S/repo" fetch origin '+refs/heads/*:refs/remotes/origin/*'
```

Use a clone, not `git worktree`: it does not write to the repository's
`.git`, and Sphinx-Codelinks fails in a worktree (CL-01). Do not run the
repository's `tools/*.sh` in the repository itself, because they write to
`build/`; in the clone they are fine.

### 4.2 Environment

```bash
uv venv "$S/repo/.venv" --python 3.12
uv pip install --python "$S/repo/.venv/bin/python" -r "$S/repo/requirements.txt"
uv pip install --python "$S/repo/.venv/bin/python" "<tool>==<new version>"   # only the triggered tool(s)
export UBC="<path of the new ubc>"   # T1; else the current one
"$UBC" --version; "$S/repo/.venv/bin/pip" freeze | grep -iE 'sphinx|codelinks|mounts|test-reports'
```

`tools/env.sh` picks up the clone's `.venv` and the exported `UBC`. A new
ubCode extension updates the IDE too; for an older ubc to compare against,
use the previous extension folder (several are kept in
`~/.vscode/extensions/`). Record every version in the run log (§7).

Change one tool at a time where possible. If two tools are released together
(as on 2026-10-14), first raise both, then for every entry that is now fixed
or changed, find out which of the two did it by reverting one.

### 4.3 Re-check the entries

For each entry in scope (§6 lists how to reproduce each one):

1. Check out the entry's **marker** commit in the clone (`git -C "$S/repo" checkout <commit>`),
   or build the scratch project the marker describes under `$S/mini/<id>`.
2. Apply the entry's **Input** (e.g. remove the workaround line named in the
   marker) and run the command it names, with the new version.
3. Compare with **Wrong output** and **Expected**; pick the result from §3.
4. If the result is not **open**: repeat on the current `main` HEAD of the
   clone with the workaround removed. A fix that holds only on the old marker
   commit is "changed", not "fixed".
5. A marker that no longer reproduces anything because the branch or the
   repository moved on (not the tool) is updated: reproduce on a pushed commit
   and replace the marker (rule in plan 999 header).

### 4.4 Full build on the new version

```bash
cd "$S/repo" && git checkout main
tools/test_all.sh            # every product with ubc + Sphinx, parity, L1–L6
```

Compare with the same run on the pinned versions (in the clone, first run
with the pins, then with the new version; keep both logs under `$S/logs/`).
Every new warning, failure or parity difference that is caused by the tool is
a candidate entry for plan 999 (rule 4). Reproduce it on a pushed commit
before writing the entry.

### 4.5 Record

1. Plan 999: Status lines, overview table, version table (§3); new entries at
   the end of their tool's section.
2. This plan: one row per run in §7 and the per-entry results in §6 (column
   "Last check").
3. Report to the user: versions, fixed / changed / new entries, follow-ups
   (§5). Plan changes stay uncommitted.

### 4.6 Cleanup (mandatory)

```bash
rm -rf "$S"; test ! -e "$S" && echo removed
git status --short      # only the plan files 998 / 999 changed (other agents' files excepted)
```

## 5. Outcome → follow-up

| Outcome | Follow-up (never done inside the run) |
|---|---|
| Full build (§4.4) green on the new version | Propose a version raise to the user: pins in `requirements.txt` / `.github/actions/setup/action.yml` (`UBC_VERSION`, `UBC_SHA256`), on a feature branch, as plan 20 did |
| Full build red because of a tool problem | New plan 999 entry; no version raise until there is a workaround |
| Entry **fixed** and it has a workaround in the repository | Add the workaround removal to the version-raise branch (§6 column "On fix"); a test that pins the bug (e.g. an `xfail`) is turned into a normal test |
| Entry **fixed** that blocks a plan | Re-open the blocked plan: STR-01 / STR-02 / STR-03 / UB-16 / PH-12 / PH-13 → plan 110 trigger T3; PH-01 → manual step M-04; UB-12 → named variants in `if` (M§) |
| Entry **changed** or **open** | Nothing beyond the record |
| Entry handed to useblocks (M-12) and now fixed | Tell the user, so the useblocks contact can be closed |

## 6. Entry checklist

How to reproduce each open entry quickly, and what to do when it is fixed.
"Marker" refers to the entry in plan 999; "scratch" means the minimal project
the entry describes, built under `$S/mini/<id>`. Last check: the version the
result in plan 999 was made on (update after every run).

### 6.1 ubc / ubCode (T1)

| ID | Reproduce | Fixed when | On fix | Last check |
|---|---|---|---|---|
| UB-01 | `ubc build needs -o x.json`, any product | `docname` present, no absolute paths | drop the path rewriting in `tools/pin_bms.py` and `tools/make_site.py` | 0.35.0 |
| UB-02 | marker: `nullable = false` on `code_url` | per-need diagnostic; other needs imported | allow `nullable = false` on `code_url` | 0.35.0 |
| UB-03 | scratch: `var.hv.class` key | ubc reports the keyword | none (generator check stays) | 0.35.0 |
| UB-04 | marker: `[variants] data_file` form | variants loaded, or a diagnostic | may switch to `[variants]` (both tools must read it) | 0.35.0 |
| UB-05 | marker: `-c` on `[codelinks.projects.vcu]` | keys merged | gates may use `-c` | 0.35.0 |
| UB-06 | marker, product `truck_diesel_eu` | `[]` written | drop the absent = `[]` rule in `tools/eval_expect.py`, `tools/tests/normalize.py` | 0.35.0 |
| UB-07 | marker, any BEV product: `allocated_from` | backlinks filled | BMS usage report may use ubc output | 0.35.0 |
| UB-08 | marker: remove `builder_filter = ""` | ubc honours it | — (SN-03 decides) | 0.35.0 |
| UB-09 | marker: `REQ_CELL_VOLTAGE_LIMITS.content` | role text resolved | — | 0.35.0 |
| UB-10 | any `ubc check` | info gone or reworded | — | 0.35.0 |
| UB-12 | marker: `if` with a named variant | resolved in **both** tools | spelled-out conditions may use named variants | 0.35.0 / SN 8.5.0 |
| UB-13 | marker: remove type `test_result` | diagnostic for dropped needs / fields | — | 0.35.0 / SN 8.5.0 |
| UB-14 | marker: `ubc build html` | links, no local path | drop the HTML rewriting in `tools/make_site.py` | 0.35.0 |
| UB-15 | marker: `REQ_MAX_CHARGE_POWER` | `<link>_back` exported | tests may read backlinks (`tools/tests/system_model.py`) | 0.35.0 |
| UB-16 | scratch (plan 110 E9) | source imported | plan 110 route D unblocked | 0.37.0 |
| UB-19 | scratch (plan 110 E8 control) | same need set in both tools | — | 0.37.0 / SN 9.0.0 |

### 6.2 Pharaoh (`ubc agent`, T1)

| ID | Reproduce | Fixed when | On fix | Last check |
|---|---|---|---|---|
| PH-01 | marker: verdicts for the two alternatives | verdict per need instance / product | remove `PH01_EXCLUDED` in `tools/tests/test_l4_content.py`; revisit M-04 | 0.35.0 |
| PH-02 | marker: `requirements.rst:65` | fingerprint changes with the resolved value | — | 0.35.0 |
| PH-03 | marker: grandchild change | fingerprint follows the full chain | — | 0.35.0 |
| PH-04 | marker `main@c10bbd7` | trace attributed to both stages | `bms_allocation` may use `direction = "both"` | 0.35.0 |
| PH-05 (+ addendum) | marker `main@37257e1`; plan 7 `part_of` | per-stage filter | type `bms_block` and the `outgoing` membership traces may be revisited | 0.35.0 |
| PH-06 | marker, `truck_bev_nmc_eu` | exempt needs not counted | drop the `-c 'needs.external_needs = []'` checks | 0.35.0 |
| PH-07 | marker: `review-brief arch` | exempt needs not listed | drop "skip `BMS_*`" from the review instructions | 0.35.0 |
| PH-08 | marker: `agent audit --id …` | fields and links shown | — | 0.35.0 |
| PH-09 | marker: change the `.agents` copy | `doctor` reports it | `tools/check_skill_mirrors.py` may stay as a second check | 0.35.0 |
| PH-10 | marker: any `review-brief` | documented | — | 0.35.0 |
| PH-11 | marker: `review-brief --ids A,B` | comma list accepted | skills may use the documented form | 0.35.0 |
| PH-12 | scratch (plan 110 E7b / E16) | `[test_reports]` type counts as declared | plan 110: drop the `-c 'needs.types = […]'` doctor workaround | 0.37.0 |
| PH-13 | scratch (plan 110 E16) | only the stage's link meets the obligation | plan 110 route B caveat gone | 0.37.0 |

### 6.3 Sphinx-Needs (T2)

| ID | Reproduce | Fixed when | On fix | Last check |
|---|---|---|---|---|
| SN-01 | marker: remove the `suppress_warnings` entry | `info` / `violation` severities not warnings | drop `suppress_warnings` in `docs/conf.py` | 8.5.0 |
| SN-02 | marker: `needs_external_needs` in `conf.py` | `conf.py` value kept | — | 8.5.0 |
| SN-03 | marker: remove `builder_filter = ""` | external needs exported | `builder_filter = ""` may go (with UB-08) | 8.5.0 |
| SN-05 | marker: remove `items` in `schemas.json:979` | accepted | — | 8.5.0 |
| SN-06 | marker: `BMS_SWBMS_…` in imported text | text unchanged | DOC-10 may compare `content` | 8.5.0 |
| SN-07 | marker: `style` of imported needs | same in both tools | DOC-10 may compare `style` | 8.5.0 / ubc 0.35.0 |

### 6.4 Sphinx-Codelinks (T3), sphinx-mounts (T4), ubc-action (T6)

| ID | Reproduce | Fixed when | On fix | Last check |
|---|---|---|---|---|
| CL-01 | marker: build in a `git worktree` | build passes | worktrees allowed for builds | 1.4.0 |
| CL-02 | marker: remove `add_executable(test_vcu …)` | warning for the skipped file | — | 1.4.0 / ubc 0.35.0 |
| CL-03 | marker: compare `remote-url` / `local-url` | same meaning in both exports | `tools/eval_expect.py` may compare them | 1.4.0 / ubc 0.35.0 |
| CL-04 | marker: source page CSS | no 404 | — | 1.4.0 |
| CL-05 | marker: `git gc`, then build | correct `blob/<commit>` links | WEB-03 check simplified | 1.4.0 |
| SM-01 | marker: `if = "var.charging.mcs"` | same behaviour as ubc | `tools/check_variants.py` `== True` rule may be relaxed | 0.2.0 |
| UA-01 | action README / `action.yml` | macOS / Windows runners | M-06: a Windows job becomes possible | — |
| UA-02 | `action.yml` at the new SHA | nested actions SHA-pinned, checksum | may switch from the direct download in `.github/actions/setup/action.yml` to the action | `393f60b` |

### 6.5 Sphinx-Test-Reports (T5)

| ID | Reproduce | Fixed when | On fix | Last check |
|---|---|---|---|---|
| STR-01 | scratch (plan 110 §4.3, `DISABLED TRUE`) | `skipped` | plan 110 | 3.0.0 / 1.1.0 |
| STR-02 | scratch: converter with prefix | prefix used, ids match `id_regex` | plan 110 route D | 3.0.0 / 1.1.0 |
| STR-03 | scratch: type in both places | Sphinx builds | PH-12 workaround not needed | 3.0.0 / SN 9.0.0 |
| STR-04 | scratch: `test-results` without `errors` | `0` in both tools | `test-results` may replace the `needtable` | 3.0.0 / ubc 0.37.0 |

## 7. Run log

| Run | Date | Trigger | Versions tested | Open / changed / fixed / new | Notes |
|---|---|---|---|---|---|
| 1 | — | first run (plan 999 §1: not re-tested on the raised versions) | ubc 0.37.0, SN 9.0.0, CL 2.0.0, mounts 0.3.0, STR 3.0.0 / 1.1.0 | — | open |
