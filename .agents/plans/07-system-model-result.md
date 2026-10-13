# Result of plan 7: System model

Outcome of [07-system-model.md](07-system-model.md) (`S§`).

| Phase | Branch | Status |
|---|---|---|
| 1 system and subsystems | `model/system` | implemented 2026-10-12, PR open |
| 2 missing BMS capabilities as requirements | `model/bms-requirements` | not started |
| 3 interfaces and external systems | `model/interfaces` | not started |

## 1. Phase 1: what was built

- **Metamodel** (`ubproject.toml`): types `system` (`SYS_`) and `subsystem`
  (`SUB_`); links `part_of` (incoming `has_part`) and `covers` (incoming
  `covered_by`, `parse_variants`); named variants `pantograph`, `eu`, `na`;
  `gap_link` / `gap_need_type` enums; `orphan_exempt_types`; quality configs
  (arch criteria). `satisfies` is unchanged.
- **Content:** `SYS_VEHICLE` and `SUB_VCU`, `SUB_CHG` (`bev`), `SUB_BMS`
  (`bev`), `SUB_ENG` (`diesel`) in `docs/system/overview.rst`, with tables of
  the subsystems and of the vehicle-level needs (`covered_by`); `:part_of:` on
  all 8 `arch` blocks (incl. every alternative) and all 4 `bms_block`s.
- **Rules** (`metamodel/schemas.json`): `id-prefix-system`,
  `id-prefix-subsystem`, `trace-subsystem-covers`, `trace-subsystem-part_of`,
  `trace-arch-part_of` (arch and bms_block, exactly one subsystem),
  `system-is-root`, `coverage-subsystem-part_of-back`,
  `coverage-system-part_of-back`, `coverage-req-covers-back`;
  `select-spec-need` includes both types. Each verified by a mutation in ubc.
- **Workflow:** stage `subsystems` (covers → req `both`, part_of → system
  `outgoing`); `archs` / `bms_allocation` depend on it and trace `part_of` →
  subsystem (`outgoing`); authoring texts name `:part_of:`.
- **Docs:** subsystem need table on each `subsystems/<x>/index.rst`;
  `method/architecture.rst`, `method/metamodel.rst`, `index.rst`, README; new
  report section "Subsystems → requirements and elements".
- **Tests:** `tools/tests/system_model.py` (shared checks); CNT-07 … CNT-09
  (L4), NEG-17 … NEG-22 (L5), oracle `PRESENT` / `COVERS` / `SUBSYSTEM_PAGE`,
  CNT-01 type set; golden files regenerated (M-14); `SUB_VCU`, `SUB_CHG` in
  `PH01_EXCLUDED`; `tools/import_gaps.py` knows `part_of` / `covers`.

## 2. Probe results (S§3 step 1)

| Question | Result |
|---|---|
| `covers` with variant functions: ubc = Sphinx? | yes, in MCS/EU and non-MCS/NA products |
| tables with incoming-link columns (`has_part`, `covered_by`) | render identically in ubCode and Sphinx HTML |
| backlinks in `needs.json` | Sphinx exports `*_back`, ubc none → plan 99 **UB-15**; tests compute `has_part` from `part_of` |
| two `trace` entries in one stage, different `up` types | accepted |
| `part_of` `direction = "both"` in stage `archs` | `SUB_BMS` owes an `arch` part (traces count per type) → `outgoing` in both stages, the "every subsystem has a part" duty is the schema warning → plan 99 **PH-05 addendum** |
| does `part_of` / `covered_by` outdate verdicts? | not by itself; **once the stage traces `part_of`**, every `arch` / `bms_block` verdict is outdated, and rewording a subsystem outdates its parts again (fingerprint includes the parent's content, PH-03). Per-product `covers` of a parent does not change a child's fingerprint (PH-02) |
| `review-brief --ids` | comma list rejected, type + ids refused → plan 99 **PH-11** |

## 3. Deviations from the plan

- **Report needflow unchanged.** S§3 step 5 named "subsystem in the needflow";
  left out so that existing reports stay untouched (decision D1 rationale).
  Only a new report section was added.
- **Subsystem index pages** keep their "… products only." sentence and add the
  subsystem table below it, instead of replacing the sentence.
- **`SYS_VEHICLE`** has no stage and no verdict (exempt, written by hand).
- **Subsystem wording** was made concrete after the first review round
  (`SUB_VCU` variant_consistency 1 → 2), which required a second review round
  of all parts.

## 4. Reviews (S§3 step 8)

Independent review agent (separate context), 2026-10-12. All verdicts fresh
in the product they were reviewed in; `PH01_EXCLUDED` covers the rest. No
score below a floor.

| Need | Product | Below max |
|---|---|---|
| `SUB_ENG` | truck_diesel_eu | — |
| `SUB_BMS` | truck_bev_nmc_eu | completeness 1: no permitted charging power → phase 2 |
| `SUB_VCU` | bus_bev_lfp_eu | design_clarity 1: no concrete interfaces → phase 3 |
| `SUB_CHG` | bus_bev_lfp_eu | — |
| `ARCH_*`, `BB_*` (12) | per first pass | scores unchanged from plan 4 (M-02 points: power-to-torque ownership VCU / ENG, drive-axle tolerance, standstill, range fallback; `BB_CHARGE_LIMITS` allocation_complete 0 → phase 2) |

## 5. Notes for the next phases

- **Phase 2 (D4):** Sphinx already suppresses
  `sn_schema_warning.network_contains_too_few` (plan 99 SN-01), so an
  unsatisfied req does not fail `sphinx-build -W`; the probe must still check
  `ubc check` and CNT-02.
- **Phase 3:** `SUB_VCU` design_clarity asks for the interfaces;
  `ARCH_ENG_TORQUE_INTERFACE` consistency 1 (who converts power to torque)
  becomes explicit with `IF_ENG_POWER_LIMIT`.

## 6. Tests

`tools/test_all.sh` (all four products, ubc + Sphinx, L1–L6) on 2026-10-12:
**151 passed, 1 skipped** (DOC-06, `choose` release-gated, plan 20). The
golden files were regenerated twice (after the content and after the subsystem
rewording); the diff contains only `SYS_VEHICLE` / `SUB_*` and `part_of` on
existing needs (M-14).

## 7. Open

- Manual: M-14 (golden diff), IDE-08 (plan 8).
- PR and merge of `model/system` (CI green required).
