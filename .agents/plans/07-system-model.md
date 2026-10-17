# Plan 7: Model the remaining prose as needs (system, subsystems, BMS requirements, interfaces)

Step 7 of the roadmap (`S§`), after plan 6 and before the open manual steps
of [plan 8](08-manual-steps.md) (decision 2026-10-12). Some architecture
content is still prose or a plain table, so it is not in the needs graph. The
four **subsystems** are the main case: they appear in four places
(`docs/system/overview.rst`, `docs/method/architecture.rst`, the
`docs/subsystems/<x>/index.rst` headings and the README), but no need says which
requirements a subsystem covers or which architecture elements it contains.
Above them, the **system** itself (the vehicle) is not a need either, so the
vehicle-level elements in `docs/vehicle` belong to no element of the graph.

This plan adds the missing types and links, then converts the prose into needs,
in three phases (scope decided 2026-10-12):

1. **System and subsystems** (`system`, `subsystem`, links `covers` / `part_of`), §2–§3.
2. **Missing BMS capabilities become requirements** in the repo, not implemented yet, §4.
   There are no "open points for the BMS" any more (decision 2026-10-12):
   what the CV platform needs from the BMS is always a requirement.
3. **Interfaces and external systems** (`sys_interface`, `ext_system`), §5.

Existing reports and tables stay untouched: every phase only adds sections.
Open decisions are in §6.

Referenced: [04-content.md](04-content.md) (`C§`), [05-test.md](05-test.md) (`T§`),
[08-manual-steps.md](08-manual-steps.md), [999-tool-bugs.md](999-tool-bugs.md),
[variant-mechanisms.md](variant-mechanisms.md) (`M§`),
[20-choose-migration.md](20-choose-migration.md).

Global rules that apply here:

- **Released features only.** New types, links, fields, named variants and
  schema rules are all standard `ubproject.toml` / `schemas.json`
  configuration. No invented directives, markers or conventions.
- **Per-product result stays warning-free** in ubc and Sphinx, with no dangling
  link in any product (T§ CNT-02, CNT-03).
  Only exception: the named not-implemented reqs of phase 2 (D4).
- **Skills are mirrored three times** (`.claude/skills`, `.agents/skills`,
  `.github/agents`). Project-specific authoring rules go into the stage
  `authoring` text in `ubproject.toml`, not into the installed skills, so that
  a Pharaoh reinstall does not overwrite them.
- Every useblocks tool bug found on the way goes into plan 999, with a
  `branch@commit` marker.

## 1. Analysis: what is already a need, what is not

### 1.1 Already needs (no action)

| Content | Type | Where |
|---|---|---|
| User stories | `user_story` | `docs/vehicle/user_stories.rst` |
| Vehicle requirements (incl. market annexes) | `req` | `docs/vehicle/requirements.rst`, `docs/region/{eu,na}/annex.rst` |
| Architecture elements of VCU / CHG / ENG | `arch` | `docs/subsystems/{vcu,chg,eng}/architecture.rst` |
| BMS black boxes | `bms_block` | `docs/subsystems/bms/architecture.rst` |
| Software requirements | `swreq` | `docs/subsystems/{vcu,chg,eng}/software_requirements.rst` |
| Implementation / tests | `impl` / `test` (codelinks markers) | `src/<x>/`, `tests/<x>/` |
| Test results, workflow gaps | `test_result`, `gap` (generated) | `docs/_global/{test_results,gaps}.rst` |
| Risks, decisions | `risk`, `decision` | `docs/_global/{risks,decisions}.rst` |
| BMS requirements | external `BMS_*` | `third_party/bms/<version>/` |

### 1.2 Not needs yet: candidates

| # | Content (today) | Where | Proposed | Value | Phase |
|---|---|---|---|---|---|
| C0 | **System**: the vehicle built from the CV platform. Root of the architecture; owner of the vehicle-level `user_story` / `req` | `docs/index.rst`, `docs/system/overview.rst` (prose only) | new type `system` (`SYS_`), exactly one need `SYS_VEHICLE`; subsystems `part_of` it | **high**: closes the hierarchy (system → subsystem → element) and draws the system boundary for the external systems | **1** |
| C1 | **Subsystems** VCU, CHG, ENG, BMS: products, integration, code folder | `docs/system/overview.rst` (table), `docs/method/architecture.rst` (table), `docs/subsystems/<x>/index.rst` (headings + "Battery-electric products only."), README | new type `subsystem` (`SUB_`), new links `part_of` (arch / bms_block → subsystem) and `covers` (subsystem → req) | **high**: requirement allocation per subsystem, the elements of each subsystem, subsystem coverage in reports and in `ubc agent gaps` | **1** |
| C2 | **Missing BMS capabilities**, today written as "Open point" sentences in the content of `BB_HV_PROTECTION` ("no BMS requirement bounds the isolation-fault reaction time yet") and `BB_CHARGE_LIMITS` ("no BMS interface requirement publishes a permitted charging power yet"). Both confirmed against the BMS 0.1.0 export: `BMS_REQ_FAULT_REACTION_TIME` covers cell-protection limits only, and no BMS requirement publishes a charging power | `docs/subsystems/bms/architecture.rst` | two new `req`s, covered by `SUB_BMS`, **not implemented yet** (no `satisfies`) | **medium**: the open points become trackable work items in the V-model and close through the normal workflow when the BMS delivers | **2** |
| C3 | **Interfaces / signals** between subsystems and to external systems: SoC, permitted discharge power, isolation fault, contactor request (VCU↔BMS); fuel level, power limit (VCU↔ENG); TSC1 torque control (ENG→engine ECU); cell limits (BMS→CHG); ISO 15118 session (CHG↔charger); energy / range / warnings (VCU→instrument cluster); door status (doors→VCU); HV consumer shutdown (VCU→consumers) | prose in `arch` and `swreq` content | new type `sys_interface` (`IF_`). **Not** named `interface`, because that is already a BMS tag. Links `provided_by` / `used_by` → subsystem or external system | **high**: shows who exchanges what with whom, per product | **3** |
| C4 | **External systems** (instrument cluster, engine control unit, charger, passenger doors, HV consumers) | prose in `arch` content | new type `ext_system` (`EXT_`): the endpoints of interfaces outside the CV platform | medium: completes the interface view (system context) | **3** |

## 2. Phase 1 design: system and subsystems

### 2.1 Metamodel

```
 user_story ◄─traces_to── req ◄──covers──── subsystem ──part_of──► system (SYS_VEHICLE)
                           ▲                    ▲
                           │ satisfies          ├────part_of── arch ◄──refines── swreq …
                           │                    └────part_of── bms_block ──allocates──► BMS_REQ_*
                           └──────────── arch / bms_block
```

**System (decision 2026-10-12, D8):** a separate type `system` with exactly
**one** need, `SYS_VEHICLE`: the commercial vehicle of the active product
(its content names the product with `:variant:`; one id, not one per product).
Subsystems are `part_of` it. External systems (phase 3) are outside it. The
vehicle-level `user_story` and `req` belong to the system **by their level**
(option A): no link from the reqs, no `covers` on the system. Ownership is
shown on the system page (needtable) and enforced indirectly, because every
req must be covered by a subsystem that is `part_of` the system.

**Why a separate link and not `satisfies` (decision 2026-10-12):** `covers`
leaves every existing report, rule and workflow stage untouched:

- `satisfies` keeps its current config (no `parse_variants`).
- `satisfied_by` on the reqs keeps listing only `arch` / `bms_block`, so the
  req entries in the golden files only gain `covered_by`.
- `coverage-req-satisfies-back` and the `archs` stage trace (`satisfies`,
  `both`) keep their meaning without a type filter.
- The tables in `reports/index.rst` and `subsystems/bms/integration.rst` show
  the same rows.

`covers` is written on the subsystem, so the req sources are not edited.
`allocates` was not reused, because it is reserved for BMS interface needs
(`alloc-target-*` rules, the `allocated_from` column).

`ubproject.toml`:

```toml
[[needs.types]]
directive = "system"
title = "System"
prefix = "SYS_"
color = "#A5B4FC"
style = "package"

[[needs.types]]
directive = "subsystem"
title = "Subsystem"
prefix = "SUB_"
color = "#C7D2FE"
style = "package"

[needs.links.part_of]
incoming = "has_part"
outgoing = "part_of"

# subsystem -> req: system-level allocation. Variant functions, because a
# subsystem covers some reqs only in some products. `satisfies` is unchanged.
[needs.links.covers]
incoming = "covered_by"
outgoing = "covers"
parse_variants = true

# Named variants for the market and the pantograph (used by SUB_CHG).
[needs.variants]
# existing: bev, bus, mcs
pantograph = "var.charging.pantograph == True"
eu = "var.market.region == 'eu'"
na = "var.market.region == 'na'"
```

Also:

- `gap_need_type` enum: add `system`, `subsystem`. `gap_link` enum: add `part_of`, `covers`.
- `[workflow] orphan_exempt_types`: add `system`, `subsystem`.
- `[quality.type_configs.system]` and `[quality.type_configs.subsystem]`: `criteria_file = "metamodel/quality/arch.toml"`.
- No new field. Integration (own code / imported) and code folder go into the
  content. The products follow from the gating.

### 2.2 Needs (content)

All in `docs/system/overview.rst` (system architecture level, one global
stage), the system first:

| Id | Gate | Content | `has_part` (backlinks) |
|---|---|---|---|
| `SYS_VEHICLE` | — (all) | The commercial vehicle of product :variant:`meta.product` (vehicle :variant:`vehicle.type`, powertrain :variant:`powertrain.type`, market :variant:`market.region`). Vehicle level = system level: the user stories and vehicle requirements are its stakeholder and system requirements | the `SUB_*` of the product |

Below the system need: a `needtable` of the vehicle-level `user_story` / `req`
("requirements of this system") and a `needtable` of this product's
subsystems (replaces the prose table). Then the four subsystems, each with
`:part_of: SYS_VEHICLE`.
Gating follows the file variants in `[[source.variant_sources]]` (checked in
step 6).

| Id | Gate | `covers` (derived from today's `satisfies` of its arch / bms_block) | `has_part` (backlinks) |
|---|---|---|---|
| `SUB_VCU` | — (all) | `REQ_ENERGY_SOURCE, REQ_RANGE_ESTIMATE, REQ_TRACTION_POWER_LIMIT, <<bev: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT>>, <<bus: REQ_DOOR_DRIVE_INTERLOCK>>` | `ARCH_VCU_ENERGY_DISPLAY`, `ARCH_VCU_POWER_MGMT`, `ARCH_VCU_HV_SHUTDOWN`, `ARCH_VCU_DOOR_INTERLOCK` |
| `SUB_CHG` | `if bev` | `REQ_MAX_CHARGE_POWER, <<mcs: REQ_MCS_CHARGING>>, <<pantograph: REQ_PANTOGRAPH_CHARGING>>, <<eu: REQ_EU_CHARGING_STANDARD>>, <<na: REQ_NA_CHARGING_STANDARD>>` | `ARCH_CHG_INLET`, `ARCH_CHG_SESSION_CONTROL` |
| `SUB_ENG` | `if not bev` | `REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT` | `ARCH_ENG_FUEL_LEVEL`, `ARCH_ENG_TORQUE_INTERFACE` |
| `SUB_BMS` | `if bev` | `REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT, REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT, REQ_MAX_CHARGE_POWER` | `BB_ENERGY_STATE`, `BB_POWER_LIMITS`, `BB_HV_PROTECTION`, `BB_CHARGE_LIMITS` |

Every subsystem has `:part_of: SYS_VEHICLE`. Every `arch` and `bms_block` gets exactly one `:part_of: SUB_<X>`.

Note on `covers: <<pantograph: REQ_PANTOGRAPH_CHARGING>>`: by `DEC_CHARGING_INLET_PRIORITY`,
a product with both MCS and a pantograph would not satisfy the pantograph
requirement. No such product exists today. The consistency check (step 6)
compares per real product and fails as soon as one appears. At that point the
link needs the stricter condition.

### 2.3 Rules (`metamodel/schemas.json`, local needs only)

| Id | Severity | Rule |
|---|---|---|
| `id-prefix-system`, `id-prefix-subsystem` | violation | prefixes `SYS_`, `SUB_` |
| `trace-subsystem-part_of` | violation | every subsystem is `part_of` exactly one system |
| `trace-subsystem-covers` | violation | every subsystem covers ≥ 1 req |
| `covers-target-req` | violation | `covers` targets only `REQ_*` |
| `trace-arch-part_of` | violation | every arch is `part_of` exactly one subsystem (`minItems 1`, `maxItems 1`) |
| `trace-bms_block-part_of` | violation | the same for bms_block |
| `part_of-target-level` | violation | `part_of` of `arch` / `bms_block` targets only `SUB_*`; of `subsystem` only `SYS_*`. A `system` has no `part_of` |
| `coverage-subsystem-part_of-back` | warning | every subsystem has ≥ 1 part |
| `coverage-system-part_of-back` | warning | the system has ≥ 1 subsystem |
| `status-present-on-spec-needs` | violation | extend the selector to `system`, `subsystem` |
| `coverage-req-covers-back` | warning | every req is covered by ≥ 1 subsystem (backward, owed by stage `subsystems`) |

"Exactly one system per product" is a pytest (step 6), not a schema rule.

Transitive consistency is **not expressible in the schema** (it would mean "the
reqs of SUB_X = the union of the reqs of its parts"). It is checked by a
pytest per product instead (step 6). If ubc / Sphinx-Needs offer a released
mechanism for it, record that in plan 999 as a feature gap, not as a bug.

### 2.4 Workflow

New stage between `reqs` and `archs` / `bms_allocation`:

```toml
[[workflow.stages]]
id = "subsystems"
produces = "subsystem"
depends_on = ["reqs"]
review_skill = "review-arch"
authoring = "Allocate every vehicle requirement to the subsystems that realise it (system architecture). One subsystem per CV subsystem and one for the BMS, each part_of SYS_VEHICLE. Gate a subsystem like its documentation folder; gate a requirement link with a variant function at least as strongly as the requirement."
[workflow.stages.route]
scope = "global"
granularity = "single"
path = "docs/system/overview.rst"
[[workflow.stages.trace]]
link = "covers"
up = "req"
direction = "both"
min = 1
[[workflow.stages.trace]]
link = "part_of"
up = "system"
direction = "outgoing"
min = 1
```

- `SYS_VEHICLE` is written once by hand and has no stage of its own (exempt
  like `gap`, via `orphan_exempt_types`). It is not a work item of the
  workflow.

- `direction = "both"`: every req owes a subsystem. This works because
  `covers` is its own link; with `satisfies` it would have mixed with the
  `archs` trace.
- `archs` and `bms_allocation`: `depends_on` adds `subsystems`, plus a
  `[[workflow.stages.trace]] link = "part_of", up = "subsystem", direction = "both", min = 1`.
  `both` means that each subsystem owes at least one element.
- Extend the `authoring` text of `archs` / `bms_allocation`: "Set `:part_of:`
  to the subsystem of the folder."
- Probe first (step 1): does ubc 0.35 accept two `trace` entries with
  different `up` types in one stage, and `direction = "both"` on `part_of`?
  If not, put it in plan 999 and fall back to `outgoing`.

## 3. Phase 1 steps

Branch `model/system` from `main`, PR to `main`. Each step ends with
`tools/test_all.sh` green, unless the step says otherwise.

| # | Step | Files | Done when |
|---|---|---|---|
| 1 | **Probe** on a throw-away commit: types `system` / `subsystem` + links `covers` (`parse_variants`) / `part_of` + new named variants + one `SUB_` with `<<mcs: …>>` in `covers`; second `trace` in the `archs` stage. Build one MCS and one non-MCS product with ubc and Sphinx. Also check whether the new backlinks (`covered_by` on a req, `has_part` on a subsystem) change the Pharaoh review fingerprint of the **target** need: run `ubc agent verdict-check` before and after | `ubproject.toml`, `docs/system/overview.rst` | both toolchains give the same `covers` per product; fingerprint behaviour known; findings → plan 999; design adjusted |
| 2 | **Metamodel**: types `system` / `subsystem`, links `covers` / `part_of`, named variants, enums, `orphan_exempt_types`, quality config | `ubproject.toml` | `ubc check` clean on all 4 products (no needs yet → no new rule fires) |
| 3 | **Schema rules** §2.3 | `metamodel/schemas.json` | rules load in ubc and Sphinx; before step 4 the `trace-arch-part_of` violations are **expected** (local check only, not committed separately; steps 3 + 4 in one commit) |
| 4 | **Content**: `SYS_VEHICLE` and four `SUB_*` (each `:part_of: SYS_VEHICLE`) in `overview.rst` (needtables of the vehicle-level needs and of the subsystems replace the prose table); `:part_of:` on all 8 `arch` blocks (incl. all alternatives of `ARCH_CHG_INLET` / `ARCH_CHG_SESSION_CONTROL`) and all 4 `bms_block` | `docs/system/overview.rst`, `docs/subsystems/*/architecture.rst` | `ubc check` warning-free on all 4 products; no dangling link |
| 5 | **Docs**: `subsystems/<x>/index.rst` shows its `SUB_` need (`needtable` or `needflow` filtered on the id) instead of the "… products only" line; `method/architecture.rst` table → reference to `SUB_*`; `method/metamodel.rst` chain, type and link table, and the sentence "vehicle level = system level, root `SYS_VEHICLE`"; `index.rst` points to the system need; `reports/index.rst`: section "Subsystems → requirements", subsystem in the needflow; README table stays (repository overview), with a pointer | `docs/**`, `README.md` | Sphinx `-W` and ubc HTML clean |
| 6 | **Tests**: L4 CNT-01 type/link sets (`system`, `subsystem`, `part_of`, `covers`); exactly one `system` need per product, and every subsystem `part_of` it; new L4 check per product and toolchain: `set(SUB_X.covers) == ⋃ satisfies of has_part`, and `SUB_X` exists ⇔ `docs/subsystems/<x>/` is in the build (file-variant consistency); oracle: `SUB_*` presence per product; L5 negative tests: subsystem without `part_of`, a second system, arch `part_of` the system directly, arch without `part_of`, `part_of` → non-subsystem, subsystem covers a req that none of its parts satisfies, a part satisfies a req its subsystem does not cover, SUB_CHG in a diesel product; golden files regenerated (`tools/tests/update_golden.py`); the diff of existing needs may only add `part_of` (arch / bms_block) and `covered_by` (req); new needs `SYS_VEHICLE`, `SUB_*` | `tools/tests/**` | every new check fails on its defect (L5) and passes on the clean repo |
| 7 | **Workflow** §2.4: stage `subsystems`, `part_of` traces, authoring texts. `ubc agent gaps` per product: no `trace_*` gaps | `ubproject.toml` | `ubc agent next` / `gaps` consistent on all 4 products |
| 8 | **Reviews**: review `SYS_VEHICLE` and `SUB_*` (review-arch). Re-review every `arch` / `bms_block` (fingerprint changed by `part_of`) and the `swreq`s whose fingerprint follows them (PH-03). Extend `PH01_EXCLUDED` with `SUB_VCU`, `SUB_CHG` (`covers` differs per product). If step 1 showed that `covered_by` changes the req fingerprint: re-review the reqs too Regenerate gaps / test results with the importers | `.pharaoh/verdicts/`, `tools/tests/test_l4_content.py`, `docs/_global/{gaps,test_results}.rst` | L4 CNT-05 green on all products |
| 9 | **Manual**: add to plan 8: review of the golden-file diff (as M-03), ubCode IDE check (Needs Index shows `SYS_VEHICLE` and `SUB_*` per product, link `part_of` navigable), short note in plan 30 (demo act "architecture": "which reqs does CHG cover in this product") | `.agents/plans/08-manual-steps.md`, `30-demo.md` | entries added |
| 10 | **CI + PR**: CI green on the PR; merge | — | `main` contains phase 1; GitHub Pages shows the system and its subsystems per product |

## 4. Phase 2: missing BMS capabilities as requirements (C2)

Starts after phase 1 is merged. Branch `model/bms-requirements`.

### 4.1 Design

Each missing BMS capability becomes a vehicle `req`: what the CV platform needs from the
BMS, written as a normal shall-clause. It is **not implemented yet**, which
means that no `arch` / `bms_block` satisfies it, because no BMS requirement
realises it. When a BMS release delivers the requirement, the black box
satisfies the req and allocates the new `BMS_REQ_*`, and the requirement is
implemented through the normal workflow. That is a good demo story for a supplier change.

| Id (draft) | Gate | `traces_to` | Covered by | Statement (draft, final wording by `draft-requirement`) | Replaces the sentence in |
|---|---|---|---|---|---|
| `REQ_PERMITTED_CHARGE_POWER` | `bev` | `US_FAST_DEPOT_CHARGING` | `SUB_BMS` | The battery management system shall publish the permitted charging power of the pack, and the vehicle shall not request more than this power from the charger. *(Review: may need splitting into the BMS part and the CHG part; one shall per req.)* | `BB_CHARGE_LIMITS` |
| `REQ_ISOLATION_FAULT_REACTION_TIME` | `bev` | `US_HV_SAFETY` | `SUB_BMS` | The battery management system shall set the isolation fault within *t* ms after the isolation resistance falls below the limit. *(t is open: agree it with the BMS team or put it in `value`.)* | `BB_HV_PROTECTION` |

- Location: `docs/vehicle/requirements.rst`, section "Charging and high
  voltage", in the existing `bev` block.
- `SUB_BMS :covers:` gains both ids. The phase-1 consistency check therefore
  becomes: `SUB_X.covers − ⋃ satisfies of its parts` = exactly the
  **known not-implemented reqs** (a named list in the test, like
  `PH01_EXCLUDED`). Any other difference fails.
- Both black boxes lose their "Open point for the BMS team …" sentence. That
  changes their content and requires a re-review. From then on, no need
  content carries open points; a missing capability is always a `req`.
- New report section in `reports/index.rst`: "Requirements not implemented",
  a `needtable` with `type == "req" and len(satisfied_by) == 0` (probe the
  filter in ubc and Sphinx).

### 4.2 Conflict with the warning-free rule (decision D4)

A req without `satisfies` triggers the existing warning
`coverage-req-satisfies-back` (and the `archs` stage trace, `direction = both`).
`ubc agent gaps` reports it, and it is imported as a `GAP_` need. That makes
it visible, which is intended. But it breaks the project rule "`ubc check` is
warning-free for every product" (T§ CNT-02, `docs/method/metamodel.rst`).
Decided (D4 = A, 2026-10-12): the req stays unsatisfied. The warning and the
`GAP_` need are the intended signal. CNT-02 allows exactly the named
not-implemented reqs (by id), and `docs/method/metamodel.rst` documents the
exception to the warning-free rule.

### 4.3 Steps

| # | Step | Done when |
|---|---|---|
| 1 | Probe: one unsatisfied req; check the ubc check output, the Sphinx `-W` build, `ubc agent gaps`, and the `len(satisfied_by) == 0` filter in both toolchains | behaviour known; D4 confirmed or revised; findings → plan 999 |
| 2 | Content: two reqs, `SUB_BMS :covers:`, remove the sentences from both black boxes | builds per D4 |
| 3 | Docs: report section; `method/requirements.rst` paragraph "Not implemented requirements"; `method/metamodel.rst` warning-free rule per D4 | Sphinx `-W` and ubc HTML clean |
| 4 | Tests: L4 consistency check with the named not-implemented list; CNT-02 per D4; L5: an unlisted unsatisfied req fails; golden files | `tools/test_all.sh` green |
| 5 | Reviews: both new reqs (review-requirement), both black boxes; gaps re-imported | CNT-05 green |
| 6 | Plan 8 (golden review; M-13 reduced to interface tags and release artifacts), plan 30 (demo: "not-implemented requirement → a BMS release implements it"), CI, PR | merged |

## 5. Phase 3: interfaces and external systems (C3, C4)

Starts after phase 1 is merged (independent of phase 2). Branch
`model/interfaces`.

### 5.1 Metamodel

```
 ext_system ◄─┐                             ┌─► subsystem
              ├──provided_by── IF_* ──used_by──┤
 subsystem  ◄─┘                             └─► ext_system
```

```toml
[[needs.types]]
directive = "ext_system"
title = "External System"
prefix = "EXT_"
color = "#E5E7EB"
style = "actor"

[[needs.types]]
directive = "sys_interface"
title = "System Interface"
prefix = "IF_"
color = "#FBCFE8"
style = "interface"

[needs.links.provided_by]
incoming = "provides"
outgoing = "provided_by"

[needs.links.used_by]
incoming = "uses"
outgoing = "used_by"
parse_variants = true
```

- External systems are **not** `part_of` `SYS_VEHICLE`: they are outside
  the system boundary. A rule forbids `part_of` on `ext_system`.
- Both links point from the interface to its endpoints. On a subsystem or an
  external system, the backlinks then read naturally: `SUB_BMS provides
  IF_BMS_POWER_LIMIT`, `SUB_VCU uses IF_BMS_POWER_LIMIT`.
- The interface is defined at **system level** only. The arch elements and
  their text stay unchanged, so there is no review churn on the architecture
  level. An arch-level link (`arch` → `IF_`) is not in scope.
- BMS values are **referenced** in the interface text (`:need:` role to the
  `BMS_REQ_*`), never copied. `allocates` is not used, so the BMS reports stay
  untouched.
- Enums: `gap_need_type` + `ext_system`, `sys_interface`; `gap_link` +
  `provided_by`, `used_by`. `orphan_exempt_types` + both. Quality:
  `sys_interface` → `metamodel/quality/arch.toml`.

### 5.2 Needs (content)

External systems go to `docs/system/overview.rst`, next to the subsystems
(section "System context"). Interfaces go to a new page
`docs/system/interfaces.rst` (Vehicle toctree, after the overview).

| Id | Gate | Content |
|---|---|---|
| `EXT_INSTRUMENT_CLUSTER` | — | shows energy, range and warnings to the driver |
| `EXT_ENGINE_ECU` | `not bev` | engine control unit, J1939 |
| `EXT_CHARGER` | `bev` | depot / public charger (CCS, MCS) or pantograph station |
| `EXT_PASSENGER_DOORS` | `bus` | door controllers with closed-and-locked signals |
| `EXT_HV_CONSUMERS` | `bev` | high-voltage consumers switched off on an isolation fault |

| Id | Gate | `provided_by` | `used_by` | Content (from today's arch prose) |
|---|---|---|---|---|
| `IF_BMS_STATE_OF_CHARGE` | `bev` | `SUB_BMS` | `SUB_VCU` | SoC and its validity flag (refs `BMS_REQ_SOC_ACCURACY`, `BMS_REQ_SOC_INVALID_FLAG`) |
| `IF_BMS_POWER_LIMIT` | `bev` | `SUB_BMS` | `SUB_VCU` | permitted discharge power (ref `BMS_REQ_POWER_DERATING`) |
| `IF_BMS_ISOLATION_FAULT` | `bev` | `SUB_BMS` | `SUB_VCU` | isolation fault (ref `BMS_REQ_ISOLATION_FAULT`) |
| `IF_BMS_CONTACTOR_REQUEST` | `bev` | `SUB_VCU` | `SUB_BMS` | request to open the main contactors |
| `IF_BMS_CELL_LIMITS` | `bev` | `SUB_BMS` | `SUB_CHG` | cell voltage limits for the charging current limit (ref `BMS_REQ_CELL_VOLTAGE_LIMITS`) |
| `IF_ENG_FUEL_LEVEL` | `not bev` | `SUB_ENG` | `SUB_VCU` | fuel level in % of tank capacity |
| `IF_ENG_POWER_LIMIT` | `not bev` | `SUB_VCU` | `SUB_ENG` | traction power limit |
| `IF_ECU_TORQUE_CONTROL` | `not bev` | `SUB_ENG` | `EXT_ENGINE_ECU` | SAE J1939 TSC1 torque/speed control |
| `IF_CLUSTER_DISPLAY` | — | `SUB_VCU` | `EXT_INSTRUMENT_CLUSTER` | remaining energy, range, (BEV) HV warning |
| `IF_CHARGER_SESSION` | `bev` | `SUB_CHG` | `EXT_CHARGER` | charging session, ISO 15118-2 (MCS: -20) |
| `IF_DOOR_STATUS` | `bus` | `EXT_PASSENGER_DOORS` | `SUB_VCU` | closed-and-locked per door |
| `IF_HV_CONSUMER_SHUTDOWN` | `bev` | `SUB_VCU` | `EXT_HV_CONSUMERS` | switch-off command |

An interface is gated at least as strongly as both of its endpoints, so no
link dangles (CNT-03). Product-specific users go into `used_by` with variant
functions.

### 5.3 Rules

| Id | Severity | Rule |
|---|---|---|
| `id-prefix-ext_system`, `id-prefix-sys_interface` | violation | prefixes |
| `trace-sys_interface-provided_by` | violation | exactly one provider, target `SUB_*` or `EXT_*` |
| `trace-sys_interface-used_by` | violation | ≥ 1 user, targets `SUB_*` or `EXT_*` |
| `coverage-ext_system-interface` | warning | every external system provides or uses ≥ 1 interface |
| `status-present-on-spec-needs` | violation | selector + `sys_interface`, `ext_system` |

The pytest checks that the provider is not also a user.

### 5.4 Workflow

- Stage `interfaces` (produces `sys_interface`, depends on `subsystems`, route
  `docs/system/interfaces.rst`, `review_skill = "review-arch"`).
- A stage `trace` has a single `up` type, but providers can be a `subsystem`
  or an `ext_system`. Probe this. Fallback: only the schema rules, no stage
  trace.
- `ext_system`: an optional stage `context` (route `docs/system/overview.rst`),
  or no stage at all (exempt like `gap`). Decide in the probe.

### 5.5 Steps

| # | Step | Done when |
|---|---|---|
| 1 | Probe: both types, both links, one IF with `used_by` variant function, stage trace with mixed endpoint types | behaviour known; findings → plan 999 |
| 2 | Metamodel + rules (§5.1, §5.3) | ubc check clean |
| 3 | Content: 5 `EXT_*` in `overview.rst`, 12 `IF_*` in `interfaces.rst` | warning-free on all 4 products, no dangling link |
| 4 | Docs: `interfaces.rst` with a `needflow` (subsystems, external systems, interfaces of this product); the `subsystems/<x>/index.rst` pages list `provides` / `uses`; `method/architecture.rst` and `method/metamodel.rst` updated; new report section "Interfaces" (the existing sections stay) | Sphinx `-W` and ubc HTML clean |
| 5 | Tests: CNT-01 sets; oracle: `IF_*` / `EXT_*` per product; L5: IF without provider, provider = user, IF to a missing endpoint in one product; golden files | green |
| 6 | Workflow (§5.4), reviews of all `IF_*`, gaps re-imported | CNT-05 green |
| 7 | Plan 8 (golden review, IDE check), plan 30 (demo: "what does the VCU get from the BMS in this product"), CI, PR | merged |

## 6. Decisions (all taken 2026-10-12)

| Id | Question | Options | Recommendation |
|---|---|---|---|
| D1 | How does a subsystem know its requirements? | **A** explicit link on the subsystem (top-down allocation), checked against its parts by a test; **B** derived only (subsystem ← `part_of` ← arch → `satisfies` → req), shown via reports / Cypher | **decided 2026-10-12: A, with the separate link `covers`** (not `satisfies`, so that existing reports, rules and stages stay untouched) |
| D2 | Where are the `SUB_*` defined? | **A** all in `docs/system/overview.rst` (global stage, explicit `if` gates); **B** each in `docs/subsystems/<x>/index.rst` (gated for free by the file variants, but BMS is not a stream and VCU/CHG/ENG would need a stream stage) | **decided 2026-10-12: A**, with the file-variant consistency test (step 6) against duplicated gates |
| D3 | Link name / direction for membership | **A** `part_of` on arch / bms_block (upwards; changes the arch needs → re-review); **B** `contains` on the subsystem (arch untouched, but a downward link with duplicated gating); **C** reuse `refines` | **decided 2026-10-12: A** |
| D4 | How does a not-implemented req (phase 2) coexist with the warning-free rule? | **A** keep it unsatisfied: the warning and the `GAP_` need are the intended signal; CNT-02 allows exactly the named not-implemented reqs (by id); `metamodel.rst` states the exception. *Probe: does the schema warning fail Sphinx `-W`?* **B** the black box satisfies the req (CV design complete, warning-free); "not implemented" is only visible because the black box allocates no BMS requirement for it, which no check can see. **C** extend the `status` enum (e.g. `open`) and exclude that status from `coverage-req-satisfies-back`: warning-free and checkable, but `status` is the review lifecycle | **decided 2026-10-12: A**. If the probe (§4.3 step 1) shows that the warning fails Sphinx `-W`, come back to this decision before any content change |
| D5 | Scope of phase 3 | interfaces, external systems, standards | **decided 2026-10-12: interfaces + external systems; no standards** |
| D7 | Interface link names / direction | **A** `provided_by` / `used_by` on the interface (backlinks `provides` / `uses` on the endpoints); **B** `provides` / `uses` on subsystems and external systems | **decided 2026-10-12: A**: the interface owns its endpoints; one place to edit, gated with the interface |
| D8 | Is the system a need, and how do the vehicle-level elements belong to it? | type `system` with one need / a generic type for system and subsystem (`block` with a `level` field, or a recursive `system`); ownership **A** by level, **B** `covers` on the system, **C** `part_of` on every req | **decided 2026-10-12: separate type `system`, one need `SYS_VEHICLE`, ownership A** (no change to reqs / user stories). A generic type was considered and not adopted: it would need level-dependent rules and one shared stage |

## 7. Risks

- **Review churn**: adding `part_of` changes the fingerprint of every `arch` /
  `bms_block`, and through PH-03 also of their `swreq`s. Phase 1 therefore
  means a full re-review of the architecture level. Plan the reviews as one
  batch (step 8).
- **PH-01 (one verdict per id)**: `SUB_VCU` / `SUB_CHG` have per-product
  `covers`, so their verdicts can only be fresh in one product. They are
  excluded by name, like the existing alternatives.
- **Backlinks and fingerprints**: if Pharaoh includes incoming links in the
  fingerprint, `covered_by` outdates every req verdict as well (step 1 probe;
  then the reqs join the batch review in step 8).
- Pharaoh may not support a stage with two `trace` entries of different `up`
  types (step 1 probe). Fallback: the `part_of` trace only as a schema rule,
  not as a workflow trace.
- **Phase 2 deliberately allows warnings** (D4 = A). Probe first: if Sphinx
  `-W` fails on the schema warning, reopen D4 before any content change.
- **Interface granularity**: 12 interfaces is one per signal group. If reviews
  ask for single signals, the count grows fast. Keep signal groups and list
  the signals in the content.
