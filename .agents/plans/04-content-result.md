# Result of plan 4: Content

Outcome of [04-content.md](04-content.md) (`C§`), executed 2026-10-09 on the
local branch `content/cv-platform` (14 commits on top of `main` `cda14bc`, not
pushed). Process (decision 2026-10-09): one branch, one commit per workflow
stage, an independent AI review round (separate subagent context) after the
stages, one stop at the end for your review.

**Status: content complete and warning-free in all four products —
`tools/build_all.sh` green (`ubc check` without warnings, `sphinx-build -W`,
ubc / Sphinx parity, all repository checks). Open: your review of the branch,
then merge + push; `choose` migration (§5) waits for the release.**

## 1. Content per product

Local (non-BMS) needs per product, identical in ubc and Sphinx:

| Product | user_story | req | arch | bms_block | swreq | impl | test | risk | decision | test_result | gap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `truck_diesel_eu` | 2 | 3 | 4 | – | 4 | 4 | 4 | – | – | 4 | 0 |
| `truck_bev_nmc_eu` | 5 | 7 | 5 | 4 | 7 | 7 | 7 | 1 | 2 | 7 | 8 |
| `bus_bev_lfp_eu` | 7 | 8 | 6 | 4 | 8 | 8 | 8 | 2 | 2 | 8 | 8 |
| `truck_bev_lfp_na` | 5 | 6 | 5 | 4 | 6 | 6 | 6 | 1 | 2 | 6 | 2 |

Plus 205 imported `BMS_*` needs in each BEV product (NMC resp. LFP).

Demo walk-through (C§8.1), as built:

| Product | Showcase A `REQ_ENERGY_SOURCE` | Showcase B `ARCH_CHG_INLET` | Market `ARCH_CHG_SESSION_CONTROL` | Values (traction / charging) | Code |
|---|---|---|---|---|---|
| D | fuel level | — (CHG absent) | — | 450 kW / – | `IMPL_VCU_ENERGY_DISPLAY` from `#else` (fuel), ENG |
| N | state of charge | MCS interface | CCS2 (EU) | 450 / 1000 kW | SoC branch, CHG incl. MCS |
| B | state of charge | roof pantograph | CCS2 (EU) | 250 / 350 kW | SoC branch, door interlock, CHG incl. pantograph |
| A | state of charge | none (CCS only) | CCS1 (NA) | 450 / 350 kW | SoC branch, CHG |

## 2. Coverage matrix (C§1.1)

| Must be covered | By | ✓ |
|---|---|---|
| every type | all 10 + `bms_block` (see §1) | ✓ |
| every link | traces_to, satisfies, refines, implements, verifies, mitigates, affects, allocates, results_for, gap_for (motivates: declared, unused as in the BMS) | ✓ |
| fields status, value (variant), product (evidence) | `REQ_TRACTION_POWER_LIMIT` / `REQ_MAX_CHARGE_POWER`, importers | ✓ |
| field `<<>>` named | `<<bus: …>>`, `<<mcs: …>>` | ✓ |
| field `<<[inline]>>` | not used in the content (proven in V02); `value` uses named variants | ~ |
| `:variant:` in text | `REQ_RANGE_ESTIMATE`, landing page, integration and report pages | ✓ |
| link variant | `ARCH_VCU_POWER_MGMT` `allocates: <<bev: BMS_REQ_POWER_DERATING>>` | ✓ |
| `if` | BEV / bus / MCS / pantograph needs | ✓ |
| alternatives | `REQ_ENERGY_SOURCE` (2), `ARCH_CHG_INLET` (3), `ARCH_CHG_SESSION_CONTROL` (2, per market) | ✓ |
| file variants | `subsystems/chg|eng|bms`, `region/eu|na` | ✓ |
| combined gating | `REQ_EU/NA_CHARGING_STANDARD` (region file + `if` BEV) | ✓ |
| external needs + allocation | 4 `bms_block`, integration page | ✓ |
| code: same id `#if`/`#else`, feature `#if`, unbuilt component | `energy_display.c`; `hv_shutdown.c`, `door_interlock.c`, `mcs.c`, `pantograph.c`; CHG / ENG | ✓ |
| Kconfig in code | `session.c` uses `CONFIG_HV__VOLTAGE__V800` for the pack voltage | ✓ |
| AI workflow, every stage | authored per stage; reviews for user_story, req, arch, bms_block, swreq, decision (93 verdict submits in 4 rounds) | ✓ |
| reports | `docs/reports/index.rst` (tables, needflow) | ✓ (variant comparison → plan 6) |

## 3. Deviations from the seeds (C§2)

| Seed | Built | Why |
|---|---|---|
| `US_MARKET_COMPLIANCE` (all) | `US_MARKET_CHARGING` (BEV) | the only market reqs are charging standards; diesel would carry an untraced story (warning-free rule) |
| `ARCH_CHG_SESSION_CONTROL` (one element) | alternatives per market (EU / NA), "CCS inlet and charging session" | `satisfies` has no link variants; a region req can only be satisfied by an element gated like it. Review: the CCS inlet was owned by no element |
| `ARCH_CHG_INLET` "charging inlet" | "high-power charging interface" (MCS / pantograph / none) | the CCS inlet moved to the session element |
| — | `SWREQ_CHG_INTERFACE_DERATING` (all BEV) | `ARCH_CHG_INLET` needs a swreq in the CCS-only product (A) |
| `SWREQ_CHG_PANTOGRAPH_SEQUENCE` gated `pantograph` | `pantograph and not mcs` | same condition as its parent branch |
| `ARCH_BMS_*` (arch) | `BB_*` (`bms_block`) | V§5 #8 |
| `DEC_BMS_AS_EXTERNAL_PRODUCT` affects `ARCH_BMS_*` | affects `ARCH_VCU_POWER_MGMT` | `affects` targets `arch` |
| `REQ_HV_SHUTDOWN…` "100 Ω/V" | "after the BMS sets the isolation fault" | the BMS uses 500 Ω/V; values are referenced, not copied |
| importers (B§3, deferred in plan 2) | `tools/import_test_results.py`, `tools/import_gaps.py` | each test case prints `PASS/FAIL <TEST id>`; results and gaps per product in `if var.meta.product == …` blocks |

## 4. Basic-setup fixes found here (on `main`, local, not pushed)

| Commit | Fix |
|---|---|
| `c10bbd7` | `variant_consistency` criterion asked for named variants in `if` (impossible) — now accepts spelled-out conditions, folders, `CONFIG_*` |
| `9abdd2c` | stage `bms_allocation`: `satisfies` trace `outgoing` only — with `both` ubc made every req owe a black box (4 false gaps per product) |
| `cda14bc` | schema `field-gap-category` accepts `review` (emitted by ubc 0.35) |

Process slip (corrected before anything was pushed): one `git commit -a`
swept your uncommitted plan edits into a fix commit; split again, plans are
uncommitted as before.

## 5. Findings (tools)

| # | Finding | Effect | Handling |
|---|---|---|---|
| C-1 | verdicts are stored **one file per need id** (`.pharaoh/verdicts/<ID>.json`) | alternatives with one id (and needs whose fingerprint follows them: children one level down, decisions via `affects`) flip between products; `verdict-check` cannot be green in all products at once — now 8 outdated in N/B, 2 in A, 0 in D | feedback to useblocks (key by id + fingerprint / variant); gaps imported honestly (18 review gaps) |
| C-2 | resolved per-product `value` fields and link variants are **not part of the review fingerprint** | a verdict on 1000 kW also counts for the 350 kW products | feedback to useblocks |
| C-3 | `review-brief` lists imported `BMS_*` needs; `agent audit` omits `value`, `tags`, and `refines` / `allocates` in `trace` | reviewers need extra queries | feedback |
| C-4 | `verdict-check` has a `stale` bucket (verdict for a need absent in the product) — not an error | works well for a product line | — |
| C-5 | ubCode extension shows the gaps live in the editor (diagnostics on `user_stories.rst`) | — | — |

## 6. Open review points (scores of 1, for your review — not yet applied)

Last round, all above the floors; no `variant_consistency` below 2:

- `SWREQ_CHG_CURRENT_LIMIT`: derive the limit from the BMS-permitted limits, not
  P / nominal voltage (parent fit, feasibility).
- `SWREQ_CHG_INTERFACE_DERATING`: name the interface, add hysteresis; give the
  pantograph and CCS-only branches temperature monitoring.
- `SWREQ_VCU_POWER_LIMIT_APPLY` / `ARCH_VCU_POWER_MGMT` / `ARCH_ENG_TORQUE_INTERFACE`:
  define "active power limit", standstill rule, ownership VCU vs ENG of the
  power-to-torque conversion.
- `SWREQ_ENG_*`: moving average, period, units / TSC1 encoding.
- `REQ_RANGE_ESTIMATE`: nominal consumption as a value (field variant).
- `BB_CHARGE_LIMITS` (allocation_complete 0), `BB_HV_PROTECTION`: open points
  for the BMS team (named in the elements).
- decisions: consequences / follow-on work; rationale of `DEC_CHARGING_INLET_PRIORITY`.

## 7. Not done / next

- **`choose` (C§8.2):** not released; showcases A/B stay as complementary `if`
  blocks (fallback of §8.2).
- **Variant comparison report:** with the side-by-side Pages (plan 6).
- **V16 / V17 IDE check** (deferred from plan 3): first VS Code session with this
  branch — switch the four products, watch `IMPL_VCU_ENERGY_DISPLAY`,
  `ARCH_CHG_INLET`, the BMS integration page.
- **Decisions for you:** (1) review `content/cv-platform`; (2) merge into `main`
  and push `main` (3 fixes + content); (3) apply the §6 review points now or
  later; (4) commit the plan updates.
