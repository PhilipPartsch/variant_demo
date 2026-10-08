# CV platform — variant management demo

A commercial vehicle (CV) platform — truck or bus, diesel or battery-electric —
documented as one 150 % model and built per product. The battery-electric
products use a separate product, the Battery Management System (BMS), whose
needs are imported for the product's cell chemistry.

| Tool | Role |
|---|---|
| **Kconfig** (`Kconfig`, `configs/*_defconfig`) | feature model and product configurations — the single source of variant data |
| **CMake** + VS Code **CMake Tools** | product selection; configuring a product generates its variant data, selects the BMS needs and the compile database |
| **sphinx-needs**, **sphinx-mounts**, **sphinx-codelinks** | Sphinx build: variant-aware needs, file variants, needs from C code (libclang preprocessor) |
| **ubCode** / `ubc` | IDE and CLI on the same configuration (`ubproject.toml`), plus the AI workflow (`ubc agent`) |

## Products

| Product | Vehicle | Powertrain | BMS chemistry | HV | Charging | Market |
|---|---|---|---|---|---|---|
| `truck_diesel_eu` | truck | diesel | — | — | — | EU |
| `truck_bev_nmc_eu` | truck | BEV | NMC | 800 V | MCS | EU |
| `bus_bev_lfp_eu` | bus | BEV | LFP | 400 V | pantograph | EU |
| `truck_bev_lfp_na` | truck | BEV | LFP | 800 V | — | NA |

## Layout

```
Kconfig, configs/          feature model and one defconfig per product
variants/                  generated variant data per product (committed, drift-checked)
docs/                      Sphinx source (documentation only)
src/<x>/, tests/<x>/       C code and tests per subsystem: vcu (all), chg (BEV), eng (diesel)
metamodel/                 schema rules and review criteria
third_party/bms/<version>/ pinned BMS needs per chemistry
tools/                     generator, checks and build entry points
build/                     everything generated (git-ignored)
```

## Prerequisites

- CMake ≥ 3.24, Ninja, a C compiler
- Python 3.12 with the docs toolchain:

  ```bash
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  ```

- `ubc` — the ubCode extension ships it; the scripts use the bundled one, or
  set `UBC=<path to ubc>`

## Select a product in VS Code

1. Open the folder; install the recommended extensions (CMake Tools, C/C++, ubCode).
2. Once per workspace: **CMake: Select a Kit** → `cv-platform`.
3. Pick the product in the CMake Tools status bar — the only choice; the
   build type is always Debug.
4. CMake configures the product and writes `build/active/` — ubCode, code
   analysis and IntelliSense follow. The landing page shows the active product.
5. If the ubCode Needs Index still shows the previous product's code needs,
   run **CMake: Configure** once.

Targets `docs` (sphinx-needs) and `docs_ubc` (ubCode) build the HTML of the
active product into `build/site/<product>/`.

## Command line

```bash
tools/build_product.sh truck_bev_nmc_eu   # one product: configure, build, CTest, ubc check, both HTML outputs
tools/build_all.sh                        # every product + drift, variant, BMS-pin and skill-mirror checks
```

Output: `build/site/<product>/{sphinx,ubcode}/` and both `needs.json` exports.
`build_all.sh` restores `build/active/`, so the IDE keeps its product.

Change the configuration with the task **CV: configure product (menuconfig)**,
or edit `Kconfig` / a defconfig and run
`tools/kconfig2variants.py --all --vscode` (CI checks with `--check`).

## BMS update

```bash
tools/pin_bms.py --bms ../rollout-demo-bms   # export both chemistries into third_party/bms/<version>/
tools/pin_bms.py --check                      # version in cmake/bms.cmake, folder, ubproject.toml agree
```

## AI workflow

`ubc agent next` names the next workflow stage; skills live identically in
`.claude/skills/`, `.agents/skills/` and `.github/agents/`
(`tools/check_skill_mirrors.py`). `.mcp.json` starts `ubc serve mcp`.

## Licence

MIT — see [LICENSE](LICENSE).
