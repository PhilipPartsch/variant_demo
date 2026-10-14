# Plan 120: Webinar episode 7 — from skeleton to final deck

AI execution plan. Turns the skeleton
`rollout/Webinar/Episode-07/Episode-7-Variants-as-Code-Part-2.marp.md`
(created 2026-10-14, 25 slides, `TODO` markers) into the final, rehearsed deck
for **"Variants-as-Code, Part 2"**: `if`, sphinx-mounts (file variants, mounts
with `attach_to`), Codelinks + libclang. The live demo runs on this repository
(`variant_demo`).

Two repositories are involved:

| Repository | Path | What changes | Git |
|---|---|---|---|
| webinar | `/Users/philippartsch/Developer/demos/rollout/Webinar` | the deck, rendered outputs, `package.json`, `README.md` | the `rollout` repo has unrelated local changes of the user — **never commit or stage there**; the user commits |
| demo | `/Users/philippartsch/Developer/demos/variant_demo` | demo content for part 2 (mounted bundle), version updates | branch per step, PR, CI green (roadmap rules) |

Referenced: [30-demo.md](30-demo.md) (demo script), [20-choose-migration.md](20-choose-migration.md),
[99-tool-bugs.md](99-tool-bugs.md), [08-manual-steps.md](08-manual-steps.md).

## 0. Rules for the agent

1. **Stop at every 🛑 stop point** and wait for the user's answer; do not
   continue with the next phase on your own.
2. **Verify every product statement** (syntax, option names, versions,
   diagnostics) against the current documentation before it goes on a slide —
   ubcode MCP `search_docs` / `fetch_doc_page`, or the project docs
   (sphinx-needs, sphinx-mounts, codelinks). Note the source and date in the
   speaker notes of the slide (`Source:` line, removed in phase 7).
3. **Everything shown live must have run** in `variant_demo` on the demo
   machine; no slide claims a result that the demo does not produce.
4. **Style of the series** (episode 6): one assertion per slide title, short
   sentences, plain words; one idea per slide; speaker notes with `Say:`,
   `Do:` and `Timing:`. No new CSS unless needed; reuse the classes of the
   front matter.
5. **No AI attribution** in commits, PRs or the deck. No invented directives,
   markers or options (released, ubCode-supported features only; unreleased
   ones are labelled "coming").
6. **Tool problems found on the way** go into plan 99 (marker on a pushed
   commit, input, wrong output, two solutions).
7. Edit only `Episode-07/`, `package.json` (scripts) and `README.md` (episode
   table) in the webinar folder.

## 1. Inputs to collect (phase 1) 🛑

Ask the user for the facts the agent cannot know; one message, all at once:

| # | Input | Used on |
|---|---|---|
| I1 | date of the session | title slide, series slide, README |
| I2 | moderator and presenter(s) (names, LinkedIn links like episode 3) | title slide |
| I3 | length (default 40 min incl. 10 min questions) | timings |
| I4 | episode 8 topic and date, if known | takeaway slide |
| I5 | public links to show: demo repository, GitHub Pages site, docs | takeaway, part 4 |
| I6 | how open about limitations (backup slide): public / only on request / remove | backup slide |
| I7 | seasonal decoration (as the Halloween theme of episode 6) yes / no | front matter |

🛑 **Stop:** wait for I1–I7.

**Answers (2026-10-14):**

| # | Answer |
|---|---|
| I1 | **2026-10-14** — the session is on the day the plan runs; every phase is compressed into hours |
| I2 | moderator **Andreas Pabinger**, presenter **Philip Partsch** |
| I3 | **60 min** (content ≈ 45 min, questions ≈ 15 min) |
| I4 | episode 8: **TBD** |
| I5 | links on the slides: **tool documentation only** (Sphinx-Needs, sphinx-mounts, Codelinks); no demo repository or site URL on a slide |
| I6 | limitations: **only on request** (backup slide) |
| I7 | no seasonal decoration |

## 2. Verify the facts (phase 2)

| # | Check | How | Result goes to |
|---|---|---|---|
| F1 | released Sphinx-Needs version; is `choose` (8.6.0) released? | PyPI `sphinx-needs`, changelog | slide "announced → released"; `if` part outlook |
| F2 | ubc / ubCode version; does it support `choose`? | ubCode changelog; probe as in plan 20 §3 step 1 | same; plan 20 gate table |
| F3 | sphinx-mounts version (0.3.0 on 2026-10-14) and changes vs the repo's 0.2.0 | changelog; `pip index versions sphinx-mounts` | part 2; step 3.1 |
| F4 | `variant_sources` / mount keys, diagnostic name for excluded toctree entries (`mounts.variant_excluded_reference`) | sphinx-mounts configuration page | part 2 slides |
| F5 | Codelinks `analyse.preprocessor` key names, file rules, limitations | codelinks analyse page (preprocessor section) | part 3 slides |
| F6 | `if` rules: added in 8.2.0, grammar, warning `needs.if` | sphinx-needs `if` page | part 1 slides |
| F7 | which backup limitations are still true (UB-12, CL-02, PH-01) | plan 99 + a quick re-check | backup slide |
| F8 | Kconfig facts for the introduction (§4.1): origin, language elements (`config`, `choice`, `depends on`, `default … if`, `help`), tools (`menuconfig`, `defconfig`, `savedefconfig`), users (Linux, Zephyr, …), `kconfiglib` version in `requirements.txt` | Linux kernel docs `Documentation/kbuild/kconfig-language.rst`, kconfiglib on PyPI / GitHub, this repository | §4.1 slides |

🛑 **Stop:** report F1–F7 in a table (fact, source, date, consequence for the
deck). The user confirms before any slide changes.

**Result (2026-10-14)** — all four useblocks tools released on the day:

| # | Fact | Source | Consequence for the deck |
|---|---|---|---|
| F1 | **Sphinx-Needs 9.0.0** (2026-10-14): `choose` / `when` / `otherwise`, `[variants]` table in `ubproject.toml`, computed values in dependency order; Python ≥ 3.11 | PyPI; changelog 9.0.0 | "announced → released": `choose` **released in 9.0.0** (not 8.6.0 as in the skeleton) |
| F2 | **ubCode / ubc 0.37.0** (2026-10-14), "lockstep with Sphinx-Needs 9.0.0": `choose`, `[variants]`, STR directives | ubCode changelog 0.37; Marketplace | `choose` supported in IDE and CLI → shown **live** (plan 20 done, IDE check OK) |
| F3 | **sphinx-mounts 0.3.0** (2026-10-14): moved into the Sphinx-Needs repository, reads `[variants]`; `attach_to` / `if` unchanged | changelog 0.3.0 | version on the slide 0.3.0; already pinned (plan 20) |
| F4 | `mounts.variant_excluded_reference` exists (since 0.2.0); `attach_to` unchanged | changelog 0.2.0 / 0.3.0 | skeleton TODO answered |
| F5 | **Sphinx-Codelinks 2.0.0** (2026-10-14): requires Sphinx-Needs 9; preprocessor keys unchanged (`compile_commands`, `includes`, `defines`); a `.c` file without a database entry is skipped, headers use `defines` only; new: multi-line needs, `@need-ids:` attached during the build; duplicate code ids warn (CL-06 fixed); docs under `/en/latest/` | changelog 2.0.0; analyse page | key names correct; docs link with `/en/latest/` |
| F6 | `if` since Sphinx-Needs 8.2.0; ubCode 0.37: `if` without variant data reports `if.invalid_expression` (not this project) | changelog 8.2.0; ubCode 0.37 | part 1 unchanged |
| F7 | UB-12, CL-02, PH-01: no fix in the changelogs; not re-tested on the new versions | plan 99; changelogs | backup slide "as of the demo versions", only on request |

## 3. Prepare the demo repository (phase 3)

Work on a branch `demo/episode-7` from `main`, PR, CI green, merge — as every
other change (roadmap rules).

| # | Step | Done when |
|---|---|---|
| 3.1 | ~~sphinx-mounts upgrade~~ — **done in plan 20** (all four tools pinned to the 2026-10-14 releases, PR #4) | ✓ |
| 3.2 | **Mounted bundle for part 2:** a small external bundle (e.g. `bundles/bus-annex/index.rst` with one need, tracing to an existing user story) mounted with `[[source.mounts]] dir`, `mount_at`, `attach_to = "index"` and `if = "var.vehicle.type == 'bus'"` | present only in `bus_bev_lfp_eu`, in ubc **and** Sphinx; toctree entry added by `attach_to`; `-W` and `ubc check` warning-free in all four products |
| 3.3 | **Tests** for the bundle: oracle (`PRESENT`, `PAGES`), golden files regenerated and shown to the user (🛑 approval, as M-03) | `tools/test_all.sh` green |
| 3.3a | **Kconfig live step** (§4.1): the VS Code task *CV: configure product (menuconfig)* opens and shows the bus product; no change is saved in the demo | task runs on the demo machine; `git status` clean afterwards |
| 3.4 | **Demo script** [30-demo.md](30-demo.md): add the bundle to act 4 / a new act for mounts; align acts with the deck's live slides | acts match the slide order |
| 3.5 | **Site:** CI deploy after the merge; check the bundle on the published bus pages | URL answers 200 |
| 3.6 | ~~plan 20~~ — **done 2026-10-14** (PR #4): the alternatives are `choose` on `main`; part 1 shows `choose` live (`REQ_ENERGY_SOURCE`, `ARCH_CHG_INLET`) | ✓ |

🛑 **Stop:** PR link and test result; the user approves the merge.

## 4. Fill the skeleton (phase 4)

Replace every `TODO` (search the file) and the placeholders with verified
content:

| # | Area | Work |
|---|---|---|
| 4.1 | title, series, takeaway | I1, I2, I4, I5 |
| 4.2 | "announced → released" table | F1–F5 versions (`choose`: released in Sphinx-Needs 9.0.0 / ubCode 0.37.0); wording for the toctree item ("solved by sphinx-mounts, not a toctree option") |
| 4.3 | part 1 `if` **and `choose`** | F6; a live `choose` slide (showcase B: order of the `when` branches = decision); the "named variants are spelled out" rule only in the backup (I6) |
| 4.4 | part 2 sphinx-mounts | real bundle from step 3.2 instead of `../bundles/bus-annex` placeholder; diagnostic name from F4; live slide step 3 |
| 4.5 | part 3 Codelinks | key names from F5; real file and line numbers from the repo |
| 4.6 | part 4 + adoption | screenshots of landing page, compare page, CI job summary; shown live in the browser, **no demo URL on a slide** (I5) |
| 4.7 | backup slide | I6 + F7; delete the `TODO` row |
| 4.8 | speaker notes | every slide: `Say:` / `Do:` / `Timing:`; timings add up to I3 |
| 4.9 | **Kconfig introduction** (new, user request 2026-10-14) | two slides plus an optional live step, see §4.1; F8 |

Remove the `Source:` lines only in phase 7.

### 4.1 Kconfig introduction (new)

**Why:** Episode 3 named Kconfig only as one possible "external resolver";
episode 7's demo is driven by it. The audience needs to know what it is and
how it is used before part 1, without turning it into a Kconfig tutorial.

**Where:** after "Four products from one repository", before part 1 (`if`) —
section "0 · Kconfig in three minutes". Timing **≈ 4 min** (2 slides, optional
1 min live), taken from the 60 min (I3).

**Slide A — "Kconfig: a feature model as a text file"** (what it is)

- The configuration language of the Linux kernel; also used by Zephyr,
  U-Boot, Buildroot, coreboot … (verify the list, F8).
- Language elements: `config` (a feature, bool / string / int), `choice` (one
  of N), `depends on` (constraints), `default … if` (derived features),
  `help` (documentation in the model).
- Tools: `menuconfig` (interactive), `defconfig` / `savedefconfig` (one
  minimal file per product), checked against the model on load.
- Code example: a real excerpt from `Kconfig` of this repo
  (`choice POWERTRAIN__TYPE`, `config BMS__ENABLED … default y if
  POWERTRAIN__TYPE__BEV`) and `configs/bus_bev_lfp_eu_defconfig` (six lines).

**Slide B — "One product = one defconfig — the build turns it into variant
data"** (how it is used here)

- Diagram (mermaid): `Kconfig` + `configs/<product>_defconfig` →
  `tools/kconfig2variants.py` (kconfiglib) → `variants/<product>.json`
  (`var.*`, read by Sphinx-Needs, ubCode, sphinx-mounts) **and**
  `autoconf.h` (`CONFIG_*`, read by the C code and the Codelinks preprocessor).
- Naming rule: `POWERTRAIN__TYPE` → `var.powertrain.type`; a choice becomes
  one string (`"bev"`); a disabled feature becomes `false` / `""`.
- CMake / CMake Tools select the product; build type and kit are **not**
  variant data.
- Message: Kconfig resolves the variant **outside** the documentation;
  everything after it only reads `var.*` (link to the episode 3 "external
  resolver" slide; any other resolver works the same way).

**Optional live (1 min):** task *CV: configure product (menuconfig)* for the
bus: show the menu, the hidden "Cell chemistry" for diesel (`depends on`),
quit without saving (step 3.3a). Fallback: a screenshot.

**Likely questions (moderator notes):** "Do I need Kconfig?" → no, any
resolver that writes the variant data; "Why not pure::variants?" → works the
same way, the docs only read `var.*`; "Is Kconfig only for Linux?" → no, a
standalone Python implementation (kconfiglib) is used here.

🛑 **Stop:** send a slide-by-slide change summary (title → what changed); the
user reviews the deck in the preview (phase 5 command).

## 5. Render and visual check (phase 5)

| # | Step | Command / check |
|---|---|---|
| 5.1 | npm scripts for episode 7 in `package.json`, as for episodes 1–3 (`build:ep7`, `html:ep7`, `pdf:ep7`, `png:ep7`, `preview:ep7`) | `npm run build:ep7` renders the Mermaid diagrams |
| 5.2 | HTML and PDF | `npm run html:ep7`, `npm run pdf:ep7` without errors |
| 5.3 | overflow check: every slide fits (no text below the fold, tables inside the slide) | look at `npm run png:ep7` images; fix with shorter text, not smaller fonts |
| 5.4 | presenter notes for pdfpc (as episode 6: `Episode-7-….pdfpc` with the notes per page) | notes present for every page |
| 5.5 | `README.md` episode table: add episode 7 | row with date and file link |

🛑 **Stop:** PDF and PNG overview to the user.

## 6. Rehearsal (phase 6)

| # | Step | Owner |
|---|---|---|
| 6.1 | dry run of the live parts on the demo machine (plan 8 M-11), following the deck — including the menuconfig step of §4.1 | user, agent prepares the checklist |
| 6.2 | IDE checklist (plan 8 M-05) on the demo machine | user |
| 6.3 | timing per part against I3; cut or move slides that run over | agent proposes, user decides |
| 6.4 | fallbacks ready: published site URLs, local site (`python3 -m http.server -d build/site 8000`) | agent |
| 6.5 | likely questions: final list in the takeaway notes (from episode 3 Q&A topics and the demo plan) | agent |

🛑 **Stop:** the user confirms the rehearsal.

## 7. Final (phase 7)

| # | Step |
|---|---|
| 7.1 | remove the `Source:` lines from the speaker notes (keep a copy of the sources in this plan's result file) |
| 7.2 | final `npm run pdf:ep7` and `html:ep7` |
| 7.3 | the day before the session: re-check F1–F3 (no release between rehearsal and session that changes a statement) |
| 7.4 | result file `120-webinar-episode-7-result.md`: sources, versions, open points, what changed against the skeleton |

## 8. Definition of done

- No `TODO` left in the deck; every product statement has a verified source.
- Every live step ran on the demo machine in the rehearsal.
- HTML and PDF render without errors; no slide overflows.
- Demo repository changes merged with CI green; the published site shows the
  mounted bundle in the bus product.
- The user approved the deck (phase 4), the outputs (phase 5) and the
  rehearsal (phase 6).
