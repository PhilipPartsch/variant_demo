# Plan 30: Demo — variant management for a CV platform

How to present the project. Two lengths: a **short demo (10 min)** that shows
the core idea, and a **long demo (30 min)** for engineers who want to see how
it works. Both use the same story and the same setup.

Referenced: [04-content-result.md](04-content-result.md) (content per product),
[08-manual-steps.md](08-manual-steps.md) (M-05 IDE session, M-11 dry run),
[20-choose-migration.md](20-choose-migration.md), [99-tool-bugs.md](99-tool-bugs.md).

## 0. Message

> **One documentation source, four products.** Pick a product in the IDE and
> requirements, architecture, BMS data, code needs and test evidence follow —
> in ubCode and in Sphinx, with the same result.

Three take-aways for the audience:

1. **Variants are configured once** (Kconfig) and used everywhere: docs, code,
   build, CI.
2. **Product lines stay traceable**: every product has a complete,
   warning-free V-model; links never dangle in any product.
3. **Two toolchains, one result**: ubCode (IDE, CLI) and sphinx-needs build
   the same needs — published side by side.

## 1. Audiences and which acts to show

| Audience | Length | Acts (§3) |
|---|---|---|
| Management, sales, first contact | 10 min | 1, 2, 3, 8 (short) |
| Engineers, tool users | 30 min | 1–8 |
| useblocks product teams | 30 min + | 1–8, then §5 "tool findings" |

## 2. Preparation (the day before and 15 min before)

### 2.1 The day before

| # | Step | Check |
|---|---|---|
| 1 | `git switch main && git pull` | working tree clean |
| 2 | `tools/test_all.sh` | 121 passed, 1 skipped |
| 3 | CI on `main` green, site up to date | https://philippartsch.github.io/variant_demo/ shows today's commit in the header |
| 4 | dry run of §3 once in full (plan 8 **M-11**) | note anything that looks different |
| 5 | IDE checklist done at least once (plan 8 **M-05**) | product switching works on this machine |

### 2.2 15 minutes before

- **VS Code**: open the repository; CMake Tools kit `cv-platform`; product
  **`truck_diesel_eu`** selected and configured (start from the simplest
  product); ubCode extension active; close all editors.
- Open these tabs in VS Code (in this order):
  1. `docs/vehicle/requirements.rst` (ubCode preview side by side)
  2. `docs/subsystems/chg/architecture.rst`
  3. `src/vcu/energy_display.c`
  4. `configs/bus_bev_lfp_eu_defconfig`
- **Browser** tabs:
  1. https://philippartsch.github.io/variant_demo/ (landing page)
  2. https://philippartsch.github.io/variant_demo/bus_bev_lfp_eu/compare.html
  3. the last green CI run (GitHub → Actions → `ci` on `main`, job summary)
- **Terminal** in the repository root, font large, history cleared.
- Font size / zoom for the projector; notifications off; dark / light theme as the room needs.

## 3. Script

Each act: what you do, what the audience sees, what you say. Times for the
long demo; the short demo uses the parts marked **(short)**.

### Act 1 — The problem and the product line (3 min) **(short)**

- **Do:** browser tab 1, the landing page.
- **See:** four products: diesel truck (EU), battery-electric truck NMC with
  megawatt charging (EU), battery-electric bus LFP with pantograph (EU),
  battery-electric truck LFP (North America).
- **Say:** "A commercial vehicle platform: truck or bus, diesel or
  battery-electric, two markets. The battery-electric ones use a separate
  product, the battery management system (BMS), in two cell chemistries. Four
  products — but we write the documentation **once**."

### Act 2 — Select a product, everything follows (6 min) **(short)**

- **Do:** VS Code, tab `requirements.rst` with the ubCode preview, product
  `truck_diesel_eu`.
- **Show:** `REQ_ENERGY_SOURCE` says "fuel tank level"; `REQ_TRACTION_POWER_LIMIT`
  value **450 kW**; no charging requirements.
- **Do:** CMake Tools status bar → product **`bus_bev_lfp_eu`** (configure runs
  automatically).
- **Show:** the same file now: "state of charge"; traction power **250 kW**;
  charging requirements appear; the door interlock appears.
- **Say:** "Nothing was copied. The bus and the truck share one source; the
  conditions are evaluated for the selected product."
- **Do:** switch to **`truck_bev_nmc_eu`**: megawatt charging appears,
  charging power **1000 kW**.
- **Show (plan 7):** `system/overview.rst`: the vehicle `SYS_VEHICLE` and its
  subsystems; `SUB_CHG` covers MCS charging here, the pantograph in the bus,
  and does not exist in the diesel truck (no `SUB_ENG` in BEV products).
- **Say:** "The allocation of requirements to subsystems follows the product
  too, and every architecture element belongs to exactly one subsystem."
- **If the Needs Index lags:** run **CMake: Configure** once (known IDE
  behaviour; the preview is always right).

### Act 3 — The same in the published documentation (3 min) **(short)**

- **Do:** browser tab 2, `bus_bev_lfp_eu/compare.html`.
- **See:** left sphinx-needs, right ubCode, the same page.
- **Do:** page selector → `vehicle/requirements`; product selector →
  `truck_diesel_eu`.
- **Say:** "Two toolchains, one result. CI builds every product with both and
  checks that the needs are identical — the needs diff is empty for all four."
- **Do:** back to the landing page, point at "✓ identical" and the test column.

### Act 4 — Variant mechanisms in detail (5 min)

Show one example per mechanism, in the editor (source, 150 %) and the preview:

| Mechanism | Where | Point out |
|---|---|---|
| value per product | `REQ_TRACTION_POWER_LIMIT` `:value: <<bus: 250 kW, 450 kW>>` | one need, the value is resolved per product |
| need only in some products | `if` around `REQ_DOOR_DRIVE_INTERLOCK` (bus) | the need does not exist in a truck |
| alternatives, one id | `ARCH_CHG_INLET` in `subsystems/chg/architecture.rst`: MCS / pantograph / none | one id, three designs, exactly one active; the order is a recorded decision |
| whole files | `subsystems/chg` (battery-electric only), `region/eu` vs `region/na` | the diesel build has no charging chapter at all |
| link only in some products | `ARCH_VCU_POWER_MGMT` `:allocates: <<bev: BMS_REQ_POWER_DERATING>>` | the link to the BMS exists only where there is a BMS |

- **Say:** "And the rule behind it: a need is gated at least as strongly as
  its parent, so no link dangles in any product — checked automatically."

### Act 5 — The BMS: a product inside a product (4 min)

- **Do:** product `truck_bev_nmc_eu`, open the BMS integration page
  (`docs/subsystems/bms/integration.rst` preview, or in the browser).
- **Show:** the four black boxes and the BMS interface needs; chemistry **NMC**.
- **Do:** switch to `truck_bev_lfp_na` → the imported BMS needs are now the
  **LFP** release (`chemistry` column); the CV content did not change.
- **Do not promise** visible cell-voltage values: the BMS writes them as
  `:variant:` roles in the text, which the export keeps unresolved (plan 99
  UB-09) — only fields such as `chemistry` change.
- **Say:** "The BMS is developed and released separately. We import its
  released needs per chemistry and link only to its interface. The vehicle
  configuration selects the chemistry."
- **Optional:** hover over `BMS_REQ_POWER_DERATING` in the editor — the
  imported need is known to ubCode.

### Act 6 — Code follows the product (4 min)

- **Do:** tab `src/vcu/energy_display.c`; product `truck_diesel_eu`, then
  `bus_bev_lfp_eu`.
- **Show:** IntelliSense greys out the inactive branch; in the code-trace page
  `IMPL_VCU_ENERGY_DISPLAY` is "(fuel level)" for diesel and "(state of
  charge)" for the bus — **the same need id**, different code.
- **Say:** "The C preprocessor decides which marker becomes the need, with the
  compile database of the selected product. Requirements, code and tests are
  traced per product."
- **Do (optional):** `src/chg/mcs.c` exists only in the MCS truck's trace.

### Act 7 — Quality: AI workflow, review, tests, CI (4 min)

- **Do:** terminal:
  ```bash
  ubc agent gaps -p . | head -20         # what is missing for this product
  ubc check                              # warning-free
  ```
- **Say:** "Each stage — user stories, requirements, architecture, software
  requirements, code, tests — was authored in the AI workflow and reviewed by
  an independent AI review against criteria such as atomicity, verifiability
  and *variant consistency*; the verdicts are in the repository."
- **Do:** browser tab 3, the CI job summary: four products, parity, tests.
- **Say:** "121 automated tests: from the variant generator to deliberately
  injected defects that every check must catch."

### Act 8 — Wrap-up (1 min) **(short)**

- **Do:** landing page.
- **Say:** the three take-aways of §0; "Next: the `choose` directive of
  sphinx-needs 8.6 will make the alternatives even simpler — migration is
  prepared (plan 20)."

## 4. Likely questions

| Question | Answer (short) | Where to show |
|---|---|---|
| Why Kconfig and not pure::variants? | open, text-based, reviewable, the same model drives code (`autoconf.h`) and docs (`var.*`) | `Kconfig`, `configs/*_defconfig` |
| How do I add a product? | one defconfig; CMake Tools, CI matrix and site pick it up | `configs/`, `.vscode/cmake-variants.json` (generated) |
| How do you avoid dangling links? | gating rule + per-product warning-free build + negative tests | Method → Metamodel page |
| What if a variant combination is invalid? | Kconfig dependencies; the generator fails, the IDE shows the error | e.g. MCS on a 400 V bus |
| Debug / release builds? | not part of the variant model; always Debug | Method → Test strategy |
| Does the review work per product? | yes, but one verdict per id — alternatives need care (known limitation) | plan 99 PH-01 |
| Can I see the BMS docs? | linked out; mounting is a later option | integration page |

## 5. For a useblocks audience: tool findings

Optional 5–10 minutes with [99-tool-bugs.md](99-tool-bugs.md): pick three
entries with a live reproduction, e.g. **PH-01** (verdicts per id; show
`ubc agent verdict-check` in two products), **SN-06** (`id_prefix` rewrites
ids in text; show the BMS gap need in ubc vs Sphinx in the needs diff
normalisation), **UA-02** (ubc-action blocked by SHA pinning; show the CI
setup step). Each entry has a marker on a pushed commit.

## 6. Fallbacks

| If … | then … |
|---|---|
| CMake Tools does not reconfigure / IDE misbehaves | show acts 2 and 6 in the browser: product selector of `compare.html` |
| the Needs Index lags | **CMake: Configure** once; the preview is always correct |
| no network | local site: `python3 -m http.server -d build/site 8000` (after `tools/build_all.sh` and `tools/make_site.py`) |
| a build fails live | do not debug on stage; switch to the published site and the last green CI run |
| time is short | acts 1, 2, 3, 8 (10 min) |

## 7. Before the first demo

- Dry run (M-11) and IDE checklist (M-05) on the demo machine.
- Decide whether to show the open review points (plan 4 result §6) or not.
- `choose` is released and migrated (plan 20, 2026-10-14): act 4 shows the
  `choose` form.
