# Plan 4: Content — small and short, covering everything

Step 4 of the [roadmap](00-roadmap.md). Fills the basic setup
([02-basic-setup.md](02-basic-setup.md), `B§`) with user stories, requirements,
architecture, BMS allocations, C code, tests, reports and the demo showcases.
Every item is **short** (one or two sentences, one function), but together
they **cover every type, link, field, mechanism and product** (§1.1).

Builds on:

- [02-basic-setup.md](02-basic-setup.md) (`B§`) — structure, metamodel, build,
  BMS import, AI workflow, entry points
- [03-mechanism-evaluation.md](03-mechanism-evaluation.md) (`V§`) — proven
  patterns per mechanism; the generic elements there are the templates here
- [variant-mechanisms.md](variant-mechanisms.md) (`M§`) — how documents consume
  `var.*`
- [kconfig-variant-configuration.md](kconfig-variant-configuration.md) (`K§`) —
  Kconfig, CMake and CMake Tools selection

Testing the content is [05-test.md](05-test.md) (`T§`); automating builds and
publishing is [06-automation.md](06-automation.md) (`A§`).

## 0. Goals and prerequisites

Goals:

1. A small but complete V-model per product: user story → vehicle req →
   architecture (incl. BMS allocation) → software req → code → test.
2. **Every variant mechanism** of M§2 used at least once in a meaningful place.
3. Content that makes the **demo** visible: switching products in CMake Tools
   changes needs, BMS data and code needs.

Prerequisites: the basic setup definition of done (B§0, D1–D8) is met, and
the mechanism evaluation exit criteria (V§6) are met — every pattern used here
has been proven on `eval/mechanisms`.

Work happens on `content/*` branches with pull requests to `main`, one per
rollout step (§9).

**Keep it short:** one or two sentences per need, one small function per
`impl`, one test per `swreq`. Add an item only if it covers something not yet
covered (§1.1).

## 1. Content map

| Folder (B§3) | Content | Gating |
|---|---|---|
| `docs/vehicle/user_stories.rst` | vehicle-level user stories | `if` per story where needed |
| `docs/vehicle/requirements.rst` | vehicle requirements | `if`, alternatives, field variants |
| `docs/system/` | overview text + component diagram (VCU, CHG, ENG, BMS) | diagram notes BEV-/diesel-only parts |
| `docs/subsystems/vcu/` | VCU architecture, swreqs, code trace | `if` inside (VCU exists everywhere) |
| `docs/subsystems/chg/` | CHG architecture, swreqs, code trace | whole folder BEV-only (file variant) |
| `docs/subsystems/eng/` | ENG architecture, swreqs, code trace | whole folder diesel-only (file variant) |
| `docs/subsystems/bms/` | BMS black boxes (`bms_block`) with `allocates`, integration page | whole folder BEV-only (file variant) |
| `docs/region/{eu,na}/` | market annex requirements | file variant per region, `if bev` inside |
| `docs/_global/` | risks, decisions (authored); test results, gaps (imported) | `if` where a risk / decision is variant-specific |
| `docs/reports/` | report pages (§7) | per product build |
| `src/<x>/`, `tests/<x>/` | C code and tests with markers | component selection + `#if CONFIG_*` |

### 1.1 Coverage matrix

The content is complete when every row has at least one item (IDs from §2–§5):

| Must be covered | By |
|---|---|
| every need type: user_story, req, arch, swreq, impl, test, risk, decision (+ imported test_result, gap) | §2.1–§2.5, §5; importers |
| every link: traces_to, satisfies, refines, implements, verifies, mitigates, affects, allocates, results_for, gap_for | §2, §3, §5; importers |
| every field: status, value (variant), product (evidence) | §2.2, importers |
| every product: D / N / B / A | §8.1 walk-through table |
| field `<<>>` named + inline, `<{ }>` | `REQ_TRACTION_POWER_LIMIT`, `REQ_MAX_CHARGE_POWER`, `REQ_RANGE_ESTIMATE` |
| link variant | `ARCH_VCU_POWER_MGMT` |
| `if` | BEV / bus / MCS / pantograph needs |
| alternatives (complementary `if`; later `choose`) | `REQ_ENERGY_SOURCE`, `ARCH_CHG_INLET` |
| file variant (subsystem + region) | `subsystems/chg|eng|bms`, `region/eu|na` |
| combined gating (file + `if`) | `REQ_EU_CHARGING_STANDARD` |
| external needs + allocation | §3 |
| code: alternative implementations with the **same need ID** in `#if` / `#else` (switched by `compile_commands.json`), feature `#if` with a gated swreq, unbuilt component | §5 |
| AI workflow: every stage run at least once | §6.1 |
| reports | §7 |

## 2. Content seeds

A deliberately small set — enough to show every mechanism, small enough to
review; each item is one or two sentences. IDs are proposals; the workflow (§6) authors and reviews them.

### 2.1 User stories (`docs/vehicle/user_stories.rst`)

| ID | Story (short) | Present in |
|---|---|---|
| `US_RANGE_AWARENESS` | The driver knows the remaining energy and range. | all |
| `US_PREDICTABLE_POWER` | The driver gets predictable traction power; limits are announced. | all |
| `US_FAST_DEPOT_CHARGING` | The fleet operator recharges a vehicle within a driver break. | BEV (`if bev`) |
| `US_OPPORTUNITY_CHARGING` | The bus operator tops up at terminal stops. | bus with pantograph (`if`) |
| `US_HV_SAFETY` | Drivers and workshop staff are protected from high-voltage hazards. | BEV (`if bev`) |
| `US_PASSENGER_DOOR_SAFETY` | Bus passengers are safe at the doors. | bus (`if bus`) |
| `US_MARKET_COMPLIANCE` | The vehicle meets the regulations of its market. | all |

### 2.2 Vehicle requirements (`docs/vehicle/requirements.rst`, `docs/region/*`)

| ID | Requirement (short) | Traces to | Present in | Mechanism |
|---|---|---|---|---|
| `REQ_ENERGY_SOURCE` | display remaining energy: state of charge (BEV) / fuel level (diesel) | `US_RANGE_AWARENESS` | all | **alternatives** (showcase A, §4.1) |
| `REQ_RANGE_ESTIMATE` | estimate remaining range from the energy source | `US_RANGE_AWARENESS` | all | `<{ var.powertrain.type }>` in text |
| `REQ_TRACTION_POWER_LIMIT` | never exceed the announced traction power limit | `US_PREDICTABLE_POWER` | all | field `value: <<[bus]: 250 kW, 450 kW>>` |
| `REQ_MAX_CHARGE_POWER` | accept charging up to the rated power | `US_FAST_DEPOT_CHARGING` | BEV | `if bev`; field `value: <<mcs: 1000 kW, 350 kW>>` |
| `REQ_MCS_CHARGING` | support megawatt charging sessions | `US_FAST_DEPOT_CHARGING` | MCS trucks | `if mcs` |
| `REQ_PANTOGRAPH_CHARGING` | support roof-pantograph opportunity charging | `US_OPPORTUNITY_CHARGING` | bus with pantograph | `if` |
| `REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT` | open the HV system on an isolation fault | `US_HV_SAFETY` | BEV | `if bev` |
| `REQ_DOOR_DRIVE_INTERLOCK` | inhibit traction while a passenger door is open | `US_PASSENGER_DOOR_SAFETY` | bus | `if bus` |
| `REQ_EU_CHARGING_STANDARD` | charge via CCS2 | `US_MARKET_COMPLIANCE` | EU + BEV | file `region/eu/**` + `if bev` inside |
| `REQ_NA_CHARGING_STANDARD` | charge via CCS1 / NACS | `US_MARKET_COMPLIANCE` | NA + BEV | file `region/na/**` + `if bev` inside |

`REQ_EU_CHARGING_STANDARD` shows **combined gating**: the region decides the
file, the powertrain decides the need inside it (the diesel EU truck has the
EU annex, but no charging requirement).

### 2.3 Architecture (`docs/subsystems/<x>/architecture.rst`)

| ID | Subsystem | Satisfies | Present in | Mechanism |
|---|---|---|---|---|
| `ARCH_VCU_ENERGY_DISPLAY` | VCU | `REQ_ENERGY_SOURCE`, `REQ_RANGE_ESTIMATE` | all | — |
| `ARCH_VCU_POWER_MGMT` | VCU | `REQ_TRACTION_POWER_LIMIT` | all | **link variant**: `allocates: <<[bev]: BMS_REQ_POWER_DERATING>>` |
| `ARCH_VCU_HV_SHUTDOWN` | VCU | `REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT` | BEV | `if bev` |
| `ARCH_VCU_DOOR_INTERLOCK` | VCU | `REQ_DOOR_DRIVE_INTERLOCK` | bus | `if bus` |
| `ARCH_CHG_INLET` | CHG | `REQ_MAX_CHARGE_POWER`, `REQ_MCS_CHARGING` / `REQ_PANTOGRAPH_CHARGING` per branch | BEV | **alternatives** (showcase B, §4.1) |
| `ARCH_CHG_SESSION_CONTROL` | CHG | `REQ_MAX_CHARGE_POWER`, `REQ_EU_/NA_CHARGING_STANDARD` | BEV | links to region reqs gated like the targets |
| `ARCH_ENG_FUEL_LEVEL` | ENG | `REQ_ENERGY_SOURCE` | diesel | file variant |
| `ARCH_ENG_TORQUE_INTERFACE` | ENG | `REQ_TRACTION_POWER_LIMIT` | diesel | file variant |
| `BB_ENERGY_STATE` | BMS | `REQ_ENERGY_SOURCE`, `REQ_RANGE_ESTIMATE` | BEV | allocation (§3) |
| `BB_POWER_LIMITS` | BMS | `REQ_TRACTION_POWER_LIMIT` | BEV | allocation (§3) |
| `BB_HV_PROTECTION` | BMS | `REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT` | BEV | allocation (§3) |
| `BB_CHARGE_LIMITS` | BMS | `REQ_MAX_CHARGE_POWER` | BEV | allocation (§3) |

### 2.4 Software requirements (`docs/subsystems/<x>/software_requirements.rst`)

| ID | Refines | Present in |
|---|---|---|
| `SWREQ_VCU_ENERGY_DISPLAY` | `ARCH_VCU_ENERGY_DISPLAY` | all — one need, implemented differently per product (§5.1) |
| `SWREQ_VCU_POWER_LIMIT_APPLY` | `ARCH_VCU_POWER_MGMT` | all |
| `SWREQ_VCU_HV_SHUTDOWN` | `ARCH_VCU_HV_SHUTDOWN` | BEV |
| `SWREQ_VCU_DOOR_INTERLOCK` | `ARCH_VCU_DOOR_INTERLOCK` | bus |
| `SWREQ_CHG_SESSION_START` | `ARCH_CHG_SESSION_CONTROL` | BEV |
| `SWREQ_CHG_CURRENT_LIMIT` | `ARCH_CHG_SESSION_CONTROL` | BEV |
| `SWREQ_CHG_MCS_HANDSHAKE` | `ARCH_CHG_INLET` | MCS (`if mcs`) |
| `SWREQ_CHG_PANTOGRAPH_SEQUENCE` | `ARCH_CHG_INLET` | pantograph (`if`) |
| `SWREQ_ENG_FUEL_LEVEL_REPORT` | `ARCH_ENG_FUEL_LEVEL` | diesel |
| `SWREQ_ENG_TORQUE_LIMIT` | `ARCH_ENG_TORQUE_INTERFACE` | diesel |

Each swreq gets one `impl` and at least one `test` marker (§5).

### 2.5 Risks and decisions (`docs/_global/`)

| ID | Type | Links | Present in |
|---|---|---|---|
| `RISK_HV_EXPOSURE` | risk | `mitigates` → `REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT` | BEV |
| `RISK_DOOR_TRAP` | risk | `mitigates` → `REQ_DOOR_DRIVE_INTERLOCK` | bus |
| `DEC_BMS_AS_EXTERNAL_PRODUCT` | decision | `affects` → a CV `arch` (`affects` targets `arch`; `BB_*` black boxes are not `arch`) (why import, not mount — B§5.1) | BEV |
| `DEC_CHARGING_INLET_PRIORITY` | decision | `affects` → `ARCH_CHG_INLET` (branch order of showcase B) | BEV |

### 2.6 Expected size

| Type | Count (approx.) |
|---|---|
| user_story | 7 |
| req | 10 |
| arch | 12 (4 of them BMS allocations) |
| swreq | 11 |
| impl / test | 11 / 11–20 |
| risk / decision | 2 / 2 |

## 3. BMS allocation content

`docs/subsystems/bms/architecture.rst`, authored through the `bms_allocation`
stage (B§7.2). Each black box satisfies the vehicle req **and** the req keeps a
CV `arch` of its own (the `archs` gate needs one; a black box does not count).



| BMS black box (`bms_block`) | Allocates (imported, `BMS_` prefix) | Why |
|---|---|---|
| `BB_ENERGY_STATE` | `BMS_REQ_SOC_ACCURACY`, `BMS_REQ_SOC_INVALID_FLAG` | range estimation and display |
| `BB_POWER_LIMITS` | `BMS_REQ_POWER_DERATING`, `BMS_REQ_PACK_OVERCURRENT` | VCU power management |
| `BB_HV_PROTECTION` | `BMS_REQ_ISOLATION_FAULT`, `BMS_REQ_FAULT_REACTION_TIME` | HV shutdown, safety timing |
| `BB_CHARGE_LIMITS` | `BMS_REQ_CELL_VOLTAGE_LIMITS`, `BMS_REQ_HEATING_REQUEST`, `BMS_REQ_COOLING_REQUEST` | charging limits (chemistry-specific values) |

Linking rules:

1. CV needs link only to BMS **interface needs** (B§5.2.3).
2. Every link to a `BMS_*` need is gated to BEV — by the BEV-only folder, an
   `if bev`, or a link variant (`ARCH_VCU_POWER_MGMT`). Otherwise the diesel
   build has dangling links (M§8.1).
3. Chemistry-specific values are **not copied** into CV needs; CV pages show
   them from the imported BMS needs (needtable filtered on
   `id.startswith("BMS_")`). Switching NMC ↔ LFP changes these values without
   touching CV content.
4. BMS needs are read-only in CV; changes go through the BMS repository.

The integration page (`docs/subsystems/bms/integration.rst`) gets a needtable of
all allocated BMS needs with their chemistry-specific values, and the active
BMS version and chemistry (`<{ var.bms.chemistry }>`).

## 4. Use of the variant mechanisms (per M§2)

| Mechanism | Where (§2) |
|---|---|
| Field `<<>>` | `REQ_TRACTION_POWER_LIMIT.value`, `REQ_MAX_CHARGE_POWER.value` |
| Field `<{ }>` | `REQ_RANGE_ESTIMATE` text, BMS integration page, landing page |
| Named variants | `bev`, `bus`, `mcs` (B§2.3) in `<<name: a, b>>` variant functions; `if` needs the spelled-out condition (`if bev` in the tables = `.. if:: var.powertrain.type == 'bev'`, M§5) |
| Link variant | `ARCH_VCU_POWER_MGMT` `allocates` `BMS_REQ_POWER_DERATING` only if BEV |
| `if` | BEV / bus / MCS / pantograph needs (§2.1–§2.5) |
| Alternatives — `choose` (**not released yet**; interim complementary `if` blocks, M§5.1) | showcases A and B (§4.1) |
| `variant_sources` | `subsystems/chg|bms/**` BEV-only, `subsystems/eng/**` diesel-only, `region/{eu,na}/**` |
| Code: component selection + `#if CONFIG_*` | §5 |
| Mount | not used (B§5.1); later option (§10) |

### 4.1 Demo showcases for alternatives (`choose`)

`choose` / `when` / `otherwise` is documented in sphinx-needs `latest` but **not
in a release yet** (stable 8.5.0 has only `if`). Until it is released, the CV
platform writes alternatives as complementary plain `if` blocks that define the
same need ID (M§5.1) — no additional directives or markers, so ubCode
understands everything. It is expected to be released before the first demo,
so two showcases are prepared in both forms and switched with one migration
step (M§5.2).

**Showcase A — two alternatives: energy source** (`docs/vehicle/requirements.rst`)

Interim (works with the released sphinx-needs):

```rst
.. if:: var.powertrain.type == "bev"

   .. req:: Energy source state
      :id: REQ_ENERGY_SOURCE
      :status: draft
      :traces_to: US_RANGE_AWARENESS

      The vehicle shall display the remaining energy as the state of charge
      reported by the battery management system.

.. if:: not (var.powertrain.type == "bev")

   .. req:: Energy source state
      :id: REQ_ENERGY_SOURCE
      :status: draft
      :traces_to: US_RANGE_AWARENESS

      The vehicle shall display the remaining energy as the fuel tank level.
```

Demo form (after the release):

```rst
.. choose::

   .. when:: var.powertrain.type == "bev"

      .. req:: Energy source state
         :id: REQ_ENERGY_SOURCE
         ...
         The vehicle shall display the remaining energy as the state of charge
         reported by the battery management system.

   .. otherwise::

      .. req:: Energy source state
         :id: REQ_ENERGY_SOURCE
         ...
         The vehicle shall display the remaining energy as the fuel tank level.
```

What it shows: **one ID, one trace position** (`REQ_ENERGY_SOURCE` is always
satisfied by `ARCH_VCU_ENERGY_DISPLAY`), but different content per product; the
other branch is never parsed.

**Showcase B — three alternatives, first true wins: charging inlet**
(`docs/subsystems/chg/architecture.rst`, the whole file is BEV-only)

```rst
.. choose::

   .. when:: var.charging.mcs == True

      .. arch:: Charging inlet
         :id: ARCH_CHG_INLET
         ...  MCS inlet, up to 1000 kW at 800 V; satisfies REQ_MCS_CHARGING

   .. when:: var.charging.pantograph == True

      .. arch:: Charging inlet
         :id: ARCH_CHG_INLET
         ...  roof pantograph plus CCS2 inlet; satisfies REQ_PANTOGRAPH_CHARGING

   .. otherwise::

      .. arch:: Charging inlet
         :id: ARCH_CHG_INLET
         ...  CCS inlet only
```

Interim form: three plain `if` blocks, each defining `ARCH_CHG_INLET`, with
conditions `var.charging.mcs == True`,
`var.charging.pantograph == True and not (var.charging.mcs == True)`,
`not (var.charging.mcs == True) and not (var.charging.pantograph == True)` —
the repeated negations are exactly what `choose` removes.

What it shows: **order matters**. A bus with 800 V, MCS *and* a pantograph
(allowed by Kconfig) gets the MCS branch; the order is recorded in
`DEC_CHARGING_INLET_PRIORITY`. Each branch links only to requirements gated
like the branch (`variant_consistency`).

## 5. Code content

| File | Content | Gating |
|---|---|---|
| `src/vcu/energy_display.c` | **same need ID** `IMPL_VCU_ENERGY_DISPLAY` in both branches: SoC display (`#if CONFIG_POWERTRAIN__TYPE__BEV`) / fuel display (`#else`) | preprocessor (§5.1) |
| `src/vcu/power_limit.c` | applies the traction power limit | — |
| `src/vcu/hv_shutdown.c` | HV shutdown request on isolation fault | `#if CONFIG_POWERTRAIN__TYPE__BEV` |
| `src/vcu/door_interlock.c` | traction inhibit with open door | `#if CONFIG_VEHICLE__TYPE__BUS` |
| `src/chg/session.c` | session start, current limit | component BEV-only |
| `src/chg/mcs.c` | MCS handshake | `#if CONFIG_CHARGING__MCS` |
| `src/chg/pantograph.c` | pantograph sequence | `#if CONFIG_CHARGING__PANTOGRAPH` |
| `src/eng/fuel.c`, `src/eng/torque.c` | fuel level report, torque limit | component diesel-only |

### 5.1 Code showcase: one need ID, two implementations

The code counterpart of the documentation alternatives (§4.1): **one**
software requirement, **one** implementation need, but variant-specific code.
Both branches carry the **same need ID**; which marker becomes the need is
decided by the codelinks preprocessor with the active product's
`compile_commands.json` (`[codelinks.projects.vcu.analyse.preprocessor]
compile_commands = "build/compile_commands.json"`, B§6.2), which CMake Tools
refreshes on every product switch.

`src/vcu/energy_display.c`:

```c
#include "autoconf.h"

#if CONFIG_POWERTRAIN__TYPE__BEV
// @need: Show remaining energy (state of charge), IMPL_VCU_ENERGY_DISPLAY, [SWREQ_VCU_ENERGY_DISPLAY]
void energy_display_update(void) { /* read BMS SoC, render */ }
#else
// @need: Show remaining energy (fuel level), IMPL_VCU_ENERGY_DISPLAY, [SWREQ_VCU_ENERGY_DISPLAY]
void energy_display_update(void) { /* read fuel sensor, render */ }
#endif
```

| Product | `IMPL_VCU_ENERGY_DISPLAY` comes from | Title |
|---|---|---|
| D | `#else` branch | Show remaining energy (fuel level) |
| N, B, A | `#if` branch | Show remaining energy (state of charge) |

What it shows: the trace `SWREQ_VCU_ENERGY_DISPLAY ← IMPL_VCU_ENERGY_DISPLAY ←
TEST_VCU_ENERGY_DISPLAY` is identical in every product; the **source link**
(file and line) and the title switch with the product. Proven on the
experiment branch (E-R E6): one need per product in ubc and Sphinx; without the
`#if` / `#else` both tools report a duplicate ID.

Rules for this pattern:

1. Exactly one branch is active in every product (`#if` / `#else`, or
   `#if` / `#elif` / `#else` covering all cases) — like complementary `if`
   blocks in the docs (M§5.1).
2. Both markers link to the **same** targets; only title and code differ.
3. The test marker is not duplicated: one `TEST_VCU_ENERGY_DISPLAY` that runs in
   every product (or the same pattern in the test file).

### 5.2 Code showcase: feature code with a gated requirement

`src/vcu/hv_shutdown.c` — different need, present only where its requirement
exists:

```c
#include "autoconf.h"

#if CONFIG_POWERTRAIN__TYPE__BEV
// @need: Request HV shutdown on isolation fault, IMPL_VCU_HV_SHUTDOWN, [SWREQ_VCU_HV_SHUTDOWN]
void hv_shutdown_on_isolation_fault(void) { /* open HV contactors */ }
#endif
```

In the diesel product the preprocessor drops `IMPL_VCU_HV_SHUTDOWN`, exactly
where `SWREQ_VCU_HV_SHUTDOWN` is gated out — no dangling link, no false gap.

Subsystem Kconfig fragments (`src/<x>/Kconfig`) get symbols only for options
the code really needs beyond the platform symbols (e.g. a VCU display unit);
the demo can work with the platform symbols alone.

**Coding rules:**

1. **All variant macros come from Kconfig** via `autoconf.h` (`CONFIG_*`). No
   hand-written `-DVARIANT_A` and no variant macros in codelinks `defines`.
2. **Never gate markers on build macros** (`NDEBUG`, `DEBUG`, compiler or kit
   macros): code needs must not depend on how the code is built (K§0 P3). The
   build is always `Debug`; markers still must not rely on that.
3. **Same symbol on both sides:** a marker inside `#if CONFIG_CHARGING__MCS`
   links only to needs gated by `var.charging.mcs == True` (or ungated needs).
4. Every C file that uses `CONFIG_*` includes `autoconf.h` directly.
5. Markers go into `.c` files; headers rely on the preprocessor fallback path.
6. **Alternative implementations share one need ID** in mutually exclusive
   branches (`#if` / `#else`), never two active markers with the same ID
   (§5.1); every traced `.c` file is built by CMake (B§6.2 step 6.2.6).

## 6. Authoring through the AI workflow

### 6.1 Order

Content is authored stage by stage as configured in B§7.2; `ubc agent next`
names the next stage, `drive-workflow` executes one step at a time.

| Step | Stage | Seeds | Author | Review |
|---|---|---|---|---|
| 1 | `user_stories` | §2.1 | human (seeded) | `review-feat` |
| 2 | `reqs` | §2.2 | `draft-requirement` | `review-requirement` |
| 3 | `archs` | §2.3 (VCU, CHG, ENG) | `draft-arch` | `review-arch` |
| 4 | `bms_allocation` | §2.3 (BMS), §3 | `draft-allocation` | `review-arch` |
| 5 | `swreqs` | §2.4 | `draft-requirement` | `review-requirement` |
| 6 | `code` | §5 | `draft-impl` | human code review |
| 7 | `tests` | §5 | `draft-test` | human code review |
| 8 | `risks`, `decisions` | §2.5 | human / `record-decision` | `review-decision` |
| 9 | `test_results` | — | importer in CI (per product) | — |

A stage counts as done only when it is complete **in every product**
(B§7.5). Each step is reviewed by a human before the next stage starts;
verdicts land in `.pharaoh/verdicts/`.

### 6.2 Authoring rules (agents and humans)

1. **Author in the 150 % source.** Gating (`if` / later `choose`, file
   variants, `#if CONFIG_*`) is part of what is written.
2. **Use the named variants** (`bev`, `bus`, `mcs`) and the variant folders;
   no ad-hoc conditions.
3. **Child gating ⊇ parent gating** (`variant_consistency`): a child is gated by
   the same or a stronger condition than its parent.
4. **Alternatives** are complementary `if` blocks with one shared ID until
   `choose` is released (M§5.1).
5. **Imported BMS needs are context, not work items:** read them (via MCP) to
   write allocations; never edit or review them; never copy their values.
6. **No build-type or kit conditions** anywhere (K§0 P3).
7. **Code markers** follow the coding rules of §5.
8. **Warning-free** (decision 2026-10-09): `ubc check` passes **without
   warnings** for every product, and there are no lint ignores. Backward
   coverage (`coverage-*-back`) is a warning, so a change is only green when
   its stream is complete down the V (req → arch → swreq → impl + test); author
   in complete slices. Sphinx suppresses only the backward-coverage subtype
   (`docs/conf.py`), `ubc check` does not.

## 7. Reports (`docs/reports/`)

Per product build:

1. **Vehicle → subsystem coverage:** every vehicle `req` is satisfied by a CV
   `arch`; every BMS black box (`bms_block`) `allocates` ≥1 BMS interface need.
2. **BMS usage report:** which BMS interface needs the CV platform uses, per
   chemistry; unused interface needs listed.
3. **Cross-product needflow:** user story → CV req → CV arch → BMS req (external,
   linked to the BMS docs).
4. **Variant comparison:** diff of `needs.json` between products, e.g. NMC vs
   LFP truck shows exactly the BMS value differences.
5. **Version report:** which BMS version and chemistry each product build used
   (`var.bms.chemistry`, `var.meta.product`, the pinned version).

## 8. Demo

### 8.1 Walk-through (switch products in the CMake Tools status bar)

| Product | Showcase A | Showcase B | BMS needs | Code needs |
|---|---|---|---|---|
| `truck_diesel_eu` | fuel level | — (CHG excluded) | none | VCU (`IMPL_VCU_ENERGY_DISPLAY` from the fuel branch), ENG |
| `truck_bev_nmc_eu` | state of charge | MCS | NMC values | VCU (BEV), CHG incl. MCS |
| `bus_bev_lfp_eu` | state of charge | pantograph | LFP values | VCU (BEV + door interlock), CHG incl. pantograph |
| `truck_bev_lfp_na` | state of charge | CCS | LFP values | VCU (BEV), CHG; NA annex |

Story line: same repository, one click → different product; the BMS stays a
separate product whose chemistry follows the vehicle configuration; code needs
follow the same switch.

### 8.2 Demo readiness (release gate for `choose`)

1. Track the sphinx-needs release that contains `choose`; pin it
   (`sphinx-needs>=<that version>`).
2. Confirm ubc / the ubCode extension evaluate `choose` identically
   (same per-product `needs.json`). **Verify.**
3. Migrate both showcases from complementary `if` blocks to `choose` (M§5.2);
   per-product `needs.json` must be unchanged.
4. Fallback if the release slips: demo the complementary `if` form and show the
   `choose` form side by side from the `latest` docs as "coming next".

## 9. Rollout

1. Seed user stories (§2.1) — stage `user_stories`.
2. Vehicle requirements incl. showcase A interim form (§2.2, §4.1).
3. Architecture for VCU / CHG / ENG incl. showcase B interim form (§2.3).
4. BMS allocations and integration page (§3).
5. Software requirements (§2.4).
6. Code and tests with markers and `#if CONFIG_*` (§5).
7. Risks and decisions (§2.5).
8. Report pages (§7).
9. Demo readiness: `choose` pin and migration (§8.2), dry run of §8.1 — manual, [07-manual-steps.md](07-manual-steps.md) M-10, M-11.
10. Afterwards: [05-test.md](05-test.md) and [06-automation.md](06-automation.md).

**Tool findings → plan 99:** every bug or gap found in a useblocks tool (ubc / ubCode, Pharaoh, Sphinx-Needs, Sphinx-Codelinks, sphinx-mounts, ubc-action, ubTrace, ubConnect, Sphinx-Test-Reports) is added to [99-tool-bugs.md](99-tool-bugs.md) in the same session: summary, marker `branch@commit` + file:line on a pushed branch, input, wrong output, workaround, two solutions.

## 10. Later options

- **Mount the BMS docs** instead of linking out (needs the BMS ontology in CV and
  a solution for the BMS code-trace pages).
- **BMS code integration:** BMS as a versioned Python package / CMake
  dependency, selected by `BMS__ENABLED`.
- **Second BMS consumer** (e.g. a stationary storage product) to show reuse of
  one BMS across product lines.
- **Feed CV configuration back to the BMS:** a BMS voltage-class axis, so
  `HV__VOLTAGE` selects BMS variants too (today the BMS varies by chemistry only).

## 11. Open points and risks

- **`choose` release:** not in stable sphinx-needs (8.5.0). The demo depends on
  it; interim complementary `if` blocks and the fallback of §8.2 cover a slip.
  **Verify** the release version and ubc support.
- **Link variant syntax** for `allocates`: answered — per item,
  `<<bev: BMS_REQ_POWER_DERATING>>` (E-R B1).
- **BMS variant axis mismatch:** CV has `HV__VOLTAGE`, the BMS does not; until the
  BMS supports it, HV-class differences live only in CV needs.
- **Version skew:** CV pins a BMS version; the BMS may change interface IDs —
  handled by the pin and interface rules (B§5.2.3, B§9) and the
  `change-request` skill (B§7.4).
- **Content size vs. demo time:** keep the seed set (§2.6); add content only if
  it shows a new mechanism.
