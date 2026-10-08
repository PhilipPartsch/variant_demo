# Plan: Kconfig as the variant configurator for sphinx-needs and sphinx-mounts

Product-independent plan. It extends [variant-mechanisms.md](variant-mechanisms.md):
that plan describes how documents **consume** variant data (`var.*`); this plan
describes how the variant data is **defined, configured, validated and
generated** with Kconfig instead of hand-written JSON, and how a developer
**selects the active variant in VS Code with the CMake Tools extension**.

Names such as `COMP_A`, `FEATURE__X` or `market` are placeholders.

Points that are conventions of this plan (not features of the tools) are marked
**Convention**. Points not yet confirmed are marked **Verify**.

Reference implementation used for comparison: the SPLed example (spl-core),
which already combines Kconfig, CMake Tools and sphinx-needs.

## 0. Principles

1. **Kconfig is the single source of variant truth.** Nobody edits
   `variants*.json` by hand; it is generated.
2. **Separation of roles** (equivalent to a commercial PLE tool):

   | Role | Realised by |
   |---|---|
   | Feature model (options, types, constraints) | `Kconfig` files |
   | Variant description (one product configuration) | `configs/*_defconfig` (+ fragments) |
   | Family model (which artifact depends on which feature) | `var.*` conditions in the docs: `<<>>`, `<{ }>`, `if` (complementary `if` blocks for alternatives until `choose` is released, M§5.1), `variant_sources`, mounts; component selection in CMake |

3. **A product variant is not a build configuration.** Requirements,
   architecture and tests do not change between build kits (e.g. prod / test)
   or build types (Debug / Release). These axes are therefore **not part of the
   variant information model**: they never appear in Kconfig, in the generated
   variant data or in any `var.*` condition. They exist only in CMake / CMake
   Tools. **In the CV platform the build type is fixed to `Debug`** and is not
   offered as a choice (decision 2026-10-08); only the compiler kit remains a
   build-only setting.
4. **One configuration drives docs and code.** The same `.config` generates
   `variants.json` for the documentation and the CMake/C config for the code.
5. **Invalid configurations never reach a build.** Every Kconfig warning is fatal.
6. **Composable products.** Each component/product owns its Kconfig fragment and
   its `var.*` namespace; an integrating product composes them.
7. **Select once, everything follows.** Selecting a variant in the CMake Tools
   status bar switches code build, IntelliSense and the ubCode/sphinx-needs view
   to that variant.

## 1. Data flow

```
VS Code CMake Tools: variant = <product>   (kit: build-only; build type fixed to Debug)
                          │  .vscode/cmake-variants.json → -DVARIANT=<product>
                          ▼
CMake configure ─► kconfig2variants  Kconfig + configs/<product>_defconfig
                          │          (fails on any Kconfig warning)
        ┌─────────────────┼───────────────────────┬────────────────────┐
        ▼                 ▼                       ▼                    ▼
  autoconf.h        autoconf.cmake          variants.json          .config
  (C code)          (component selection,        │                (traceability)
                     CMake options)              │
                                                 ├─► copy ─► build/active/variants.json
                                                 │            └─ ubproject.toml variant_data_file (IDE)
                                                 └─► `docs` target: sphinx-build -D needs_variant_data_file=…

CI / review: variants/<product>.json committed, regenerated and drift-checked
```

## 2. Phase 1: Tooling setup

| Step | Action |
|---|---|
| 1.1 | Choose the Kconfig implementation: `kconfiglib` (pure Python, PyPI) — or the copy vendored by Zephyr / spl-core if the organisation already uses it. Upstream `kconfiglib` is barely maintained: **pin the version** and keep the generator's dependency on it small. |
| 1.2 | Add it to the docs toolchain dependencies (same Python environment as Sphinx / sphinx-needs / sphinx-mounts). |
| 1.3 | CMake ≥ 3.24 and Ninja; VS Code extensions `ms-vscode.cmake-tools`, `ms-vscode.cpptools` (C/C++ only) and the ubCode extension, listed in `.vscode/extensions.json`. |
| 1.4 | Configurator entry points: `menuconfig` (terminal), `guiconfig` (Tk GUI), `savedefconfig` (write minimal defconfig back) — exposed as VS Code tasks (Phase 7) and project scripts. |
| 1.5 | Set `KCONFIG_CONFIG` / `srctree` explicitly in every script and task, so results do not depend on the working directory. |

## 3. Phase 2: Repository layout

**Convention:**

```
Kconfig                       # top level: product options + rsource of components
components/<comp>/Kconfig     # one fragment per component/product, owned by its team
configs/
  <product>_defconfig         # one per shipped product configuration
  fragments/<topic>.config    # optional reusable fragments (market, ...)
variants/<product>.json       # GENERATED, committed, drift-checked (review + CI)
tools/kconfig2variants.py     # the generator (Phase 5)
CMakeLists.txt                # calls cmake/kconfig.cmake, selects components, `docs` target
cmake/kconfig.cmake           # runs the generator at configure time
.vscode/
  cmake-variants.json         # GENERATED from configs/ (variant picker)
  cmake-kits.json             # one project kit (compiler only, build-only)
  settings.json               # build dir, configureOnOpen, compile commands
  tasks.json                  # configurator tasks; `inputs` GENERATED from configs/
build/                        # gitignored
  cmake/<product>/             # one CMake build dir per product (always Debug)
  active/variants.json        # copy of the currently configured variant (IDE)
```

For an external product that is mounted (sphinx-mounts), its Kconfig fragment
lives in **its own repository** and is pulled in with `rsource`/`osource` from
the same checkout that the mount points at, so docs and options stay in lockstep.

## 4. Phase 3: Kconfig authoring conventions

### 4.1 Naming and nesting (**Convention**)

Kconfig symbols are flat; `var.*` is nested. Use a **double underscore `__` as
nesting separator**; single underscores stay part of a name:

| Kconfig symbol | `var.*` path |
|---|---|
| `MARKET__REGION` | `var.market.region` |
| `COMP_A__LIMITS__MAX_CURRENT` | `var.comp_a.limits.max_current` |
| `FEATURE__REMOTE_DIAG` | `var.feature.remote_diag` |

- First segment = owner namespace (product or component). No symbol without a
  namespace.
- Lower-case the path in the generated JSON.
- Legacy `var.*` keys that cannot follow the scheme go into an explicit
  mapping table (`tools/var_map.toml`), not into special cases in code.

### 4.2 Types

| Kconfig type | JSON leaf | Rule |
|---|---|---|
| `bool` | `true` / `false` | Conditions compare type-strictly: write `var.x == True` (bare `var.x` works in `if`, but sphinx-mounts rejects it). |
| `int`, `hex` | integer | Use `range` to constrain. |
| `string` | string | Keep strings for values rendered into prose (e.g. `"2.50"`). Do not use free strings for alternatives — use a choice (§4.3). |
| `tristate` | — | **Not used** (module semantics are meaningless for docs). |

### 4.3 Choices → enums (**Convention**)

Use **named choices** for mutually exclusive alternatives. The generator emits
the selected option as a string, so conditions read naturally and typos are
impossible:

```kconfig
choice MARKET__REGION
    prompt "Target market"
    default MARKET__REGION__EU
config MARKET__REGION__EU
    bool "EU"
config MARKET__REGION__NA
    bool "North America"
endchoice
```

→ `var.market.region == "eu"` (the suffix after the choice name, lower-cased).
The individual option bools are **not** emitted to the variant data (they are
still available to C code and CMake).

### 4.4 Feature sets → booleans (+ optional list)

Kconfig has no lists. Model optional features as bools under a common prefix
(`FEATURE__*`). The generator emits each as a bool **and** may derive a list
(`var.features = ["remote_diag", ...]`) for `in` conditions. Pick one style per
namespace and record it.

### 4.5 Constraints

- `depends on` for "only possible if", `select` sparingly (it bypasses
  dependencies), `imply` for soft defaults.
- Every product-level rule that would otherwise live in a reviewer's head goes
  into Kconfig (e.g. "option X requires choice Y").
- Every visible symbol has a `help` text: it is the feature documentation and
  can be rendered into the docs later.

### 4.6 Values of disabled symbols (**Convention**)

Symbols whose dependencies are not met are **still emitted** with a typed
"off" value (`false`, `0`, `""`), never omitted. Otherwise sphinx-mounts treats
conditions on them as unevaluable (`mounts.variant_rule_unevaluable`).
(spl-core's JSON writer omits them — a known gap to avoid.) Both tools
evaluate these "off" values identically (evaluated, A6).

### 4.7 No build-configuration symbols (**Convention**, from Principle 3)

- No Kconfig symbol for build kit, build type, optimisation, debug output,
  test instrumentation or toolchain. These come from CMake
  (`CMAKE_BUILD_TYPE`, kit / toolchain file) only.
- If code needs a debug-only switch, it reads the CMake build type, not Kconfig.
- Review rule: a new symbol that would differ between Debug and Release of the
  same product is rejected.

## 5. Phase 4: Product configurations (defconfigs)

- One `configs/<product>_defconfig` per shipped configuration; keep it
  **minimal** (`savedefconfig`), so diffs show only real decisions.
- Optional layering with fragments: `base` + `market` + `product`. The
  generator loads them in a fixed order (`load_config(..., replace=False)`).
- Naming: `<product>_<axis values>_defconfig`, e.g. `<family>_<market>_defconfig`.
  The `<product>` part is the name shown in the CMake Tools variant picker.
- A defconfig is a **reviewed artifact**: changing it changes a product.

## 6. Phase 5: Generator `kconfig2variants`

Inputs: `Kconfig`, one defconfig (+ fragments), output directory.
**No build kit / build type input** (Principle 3) — the output for a product is
byte-identical in every build directory.

Responsibilities, in order:

1. Load `Kconfig` and the defconfig (+ fragments).
2. **Fail** on any warning: undefined symbol assigned, value changed by
   dependencies, out-of-range value. kconfiglib accepts an assignment with
   unmet dependencies **silently**, so the generator compares every assigned
   value with the resolved value itself (evaluated, F-4).
3. Walk all defined symbols and named choices; apply §4 (nesting, types,
   choices, disabled values, mapping table).
4. Validate the result against the `var.*` rules of variant-mechanisms §1.5
   (nested dicts, scalar or uniform-list leaves, no `_`-prefixed keys).
5. Write, with **sorted keys and stable formatting** (reviewable diffs) and
   only when the content changed (avoids needless rebuilds):
   - `variants.json` — documentation variant data
   - `autoconf.h` — C defines (`CONFIG_*`)
   - `autoconf.cmake` — CMake variables (component selection, options)
   - `.config` — full resolved configuration (traceability)

Modes:
- `--all`: regenerate `variants/*.json` for every defconfig (used by CI).
- `--vscode`: regenerate `.vscode/cmake-variants.json` and the variant `inputs`
  in `.vscode/tasks.json` from `configs/*_defconfig` — **one variant list**
  instead of several hand-maintained ones.
- `--check`: regenerate everything in memory and fail if committed files differ
  (drift check).

**Commit or generate?** Commit `variants/*.json` and the generated `.vscode`
files; enforce `--check` in CI. Configuration changes are then visible in
review. The IDE uses the active copy (Phase 7), not the committed files.

## 7. Phase 6: CMake integration

| Step | Action |
|---|---|
| 6.1 | `CMakeLists.txt` requires the cache variable `VARIANT` and fails early if `configs/${VARIANT}_defconfig` does not exist. |
| 6.2 | `cmake/kconfig.cmake` runs `kconfig2variants` with `execute_process` at configure time into `${PROJECT_BINARY_DIR}/kconfig/`; non-zero exit → `FATAL_ERROR`. |
| 6.3 | Register `Kconfig`, all `components/*/Kconfig`, the defconfig and fragments as `CMAKE_CONFIGURE_DEPENDS`, so editing them reconfigures automatically. |
| 6.4 | `include(autoconf.cmake)` and **select components from Kconfig** (e.g. `if(COMP_A__ENABLED) add_subdirectory(components/comp_a)`), instead of a separate hand-written parts list per variant. Code and docs then follow the same feature selection. |
| 6.5 | Add `autoconf.h` to the include path (C/C++ products). |
| 6.6 | **Active-variant copy:** after a *successful* generator run, copy `variants.json` to `${CMAKE_SOURCE_DIR}/build/active/variants.json` (`configure_file(... COPYONLY)`). On failure, **delete** the copy, so the IDE never silently shows a stale variant. Same idea as `cmake.copyCompileCommands`. |
| 6.7 | Optionally write `build/active/VARIANT` (plain text) so tools and the status of the IDE can show which variant the copy belongs to. |
| 6.8 | **`docs` target:** runs `sphinx-build -W -b html -D needs_variant_data_file=<build>/kconfig/variants.json <src> ${CMAKE_SOURCE_DIR}/build/docs/${VARIANT}`. The docs output is per **variant only**, not per kit / build type (Principle 3); building docs from Debug or Release gives the same result. Optionally a `needs` target that runs `ubc build needs` the same way. |
| 6.9 | Projects without C/C++ can still use CMake as the driver: `project(<name> NONE)` with only the generator and `docs` target. |

## 8. Phase 7: VS Code / CMake Tools integration

### 8.1 Variant picker (`.vscode/cmake-variants.json`, generated)

**One** axis in the CMake Tools status bar: the product. There is no
`buildType` axis — the build type is always `Debug` (set by
`cmake.configureSettings` and as default in `CMakeLists.txt`).

| Axis | Source | Part of the variant model? |
|---|---|---|
| `variant` | one choice per `configs/<product>_defconfig`, sets `VARIANT` | **yes** |

```json
{
  "variant": {
    "default": "<default product>",
    "choices": {
      "<product>": { "short": "<product>", "long": "Product <product>",
                     "settings": { "VARIANT": "<product>" } }
    }
  }
}
```

The compiler comes from one project kit in `.vscode/cmake-kits.json`
(build-only, B§6.3).

`cmake-variants.json` (variants mode) is preferred over `CMakePresets.json`:
the product list is generated from `configs/` and needs no per-product preset
boilerplate. Switch to presets only if the organisation standardises on them.

### 8.2 Settings (`.vscode/settings.json`)

| Setting | Value | Why |
|---|---|---|
| `cmake.buildDirectory` | `${workspaceFolder}/build/cmake/${variant:variant}` | One build dir per product, shared with the command line; switching does not wipe others. |
| `cmake.configureOnOpen` | `true` | The active-variant copy exists right after opening a fresh clone. |
| `cmake.configureSettings` | `{ "CMAKE_BUILD_TYPE": "Debug" }` | Build type fixed; never feature values — those come from the defconfig. |
| `cmake.copyCompileCommands` | `${workspaceFolder}/build/compile_commands.json` | IntelliSense follows the selection (C/C++). |
| `C_Cpp.default.configurationProvider` | `ms-vscode.cmake-tools` | Same. |

### 8.3 ubCode / sphinx-needs in the IDE

- `ubproject.toml`: `variant_data_file = "build/active/variants.json"`.
- Selecting another variant in CMake Tools → reconfigure → generator → copy
  → ubCode resolves the new variant.
- **Verify:** CMake Tools reconfigures automatically on a variant switch.
- **Verify:** the ubCode extension re-indexes when `build/active/variants.json`
  changes outside the editor (`index_on_save` only covers editor saves). If
  not, add a post-configure task "Reload ubCode index" or document the manual
  reload.
- Sanity check: the generator always emits a fixed key (e.g. `var.meta.product`)
  so a missing or empty file is visible immediately (a `<{ var.meta.product }>`
  in the docs landing page shows the active variant).

### 8.4 Tasks (`.vscode/tasks.json`)

| Task | Command |
|---|---|
| Configure features of a variant | `guiconfig` / `menuconfig` with `KCONFIG_CONFIG=build/<variant>/.config`, `KCONFIG=Kconfig`, input = variant pick list (generated) |
| Save variant | `savedefconfig` → `configs/<variant>_defconfig` (minimal), then CMake reconfigure |
| Build docs of active variant | `cmake --build <build dir> --target docs` (also reachable via the CMake Tools target picker) |
| Open docs of active variant | open `build/docs/<variant>/index.html` |
| Regenerate variant list | `kconfig2variants --vscode` after adding / removing a defconfig |

Editing the full `.config` and saving back as a minimal defconfig keeps
committed files small (spl-core edits the full `config.txt` directly).

### 8.5 Developer workflow

1. Open the folder → CMake Tools configures the default variant → docs and
   code show it.
2. Pick another variant in the status bar → reconfigure → code, IntelliSense and
   ubCode switch.
3. Change features: task "Configure features" → "Save variant" → review the
   defconfig and the regenerated `variants/<product>.json` in the diff.
4. Build code (always Debug) or the `docs` target — docs do not depend on the
   kit.

## 9. Phase 8: Wiring into sphinx-needs, ubc and sphinx-mounts outside the IDE

| Step | Action |
|---|---|
| 8.1 | CLI and CI **configure the product first** and then build against its active copies. A `-c "needs.variant_data_file = …"` override alone switches docs but not code analysis (evaluated, F2). Where overrides are used, use **absolute paths** — relative `-c` paths resolve against the working directory, and a missing file may resolve silently to empty values. |
| 8.2 | Named variants (`[needs.variants]`, e.g. `pro = "var.edition == 'pro'"`): keep them hand-written, but only over generated keys. Optionally generate one per choice option later. |
| 8.3 | sphinx-mounts reads the **same** variant data; no second data source and no build-configuration data (Principle 3). |

## 10. Phase 9: Products composed of products

1. Each component/product ships `Kconfig` (its options, own namespace), its own
   `configs/` and its own `cmake-variants.json` for **standalone** builds.
2. The integrating product `rsource`s the component fragments and sets their
   options in its defconfigs — or derives them with `select`/`imply`/`default`
   from product-level choices (e.g. a product choice determines a component
   parameter).
3. **Namespace contract:** a component's docs read only `var.<its namespace>.*`.
   When mounted, the component's docs see the host's generated data, so the
   host must produce exactly that subtree.
4. A component may publish **interface symbols** (values other products depend
   on); changing them is an interface change and needs review by both sides.
5. Pin the component version (submodule / CMake `FetchContent` / CI checkout)
   so its Kconfig fragment, its code and its mounted docs come from the same
   revision.

## 11. Phase 10: CI

- **Matrix over `configs/*_defconfig`** (not over JSON files): `cmake -S . -B
  build/cmake/<product> -DVARIANT=<product>` (Debug) → `cmake --build
  build/cmake/<product> --target docs` → `ubc` build → export `needs.json`
  per product. One job per product.
- **Drift check:** `kconfig2variants --all --vscode --check`.
- **Consistency checks** (extend variant-mechanisms §8.3/§9):
  - every `var.*` key used in a condition exists in the generated schema (union
    of all products);
  - every Kconfig symbol is used by at least one condition, CMake selection or
    code path (otherwise it is dead configuration);
  - every condition is true in ≥1 and false in ≥1 defconfig (branch coverage);
  - no build-configuration names in Kconfig or `var.*` (§4.7).
- **Kconfig hygiene:** all visible symbols have `help`; no `tristate`; every
  symbol has a namespace prefix.

## 12. Phase 11: Workflows and governance

| Task | Steps |
|---|---|
| Add a feature | Add symbol (+ help, constraints) → regenerate → use `var.*` in docs (variant-mechanisms §2) and/or CMake selection → enable it in ≥1 defconfig → CI coverage passes |
| Add a product configuration | Configure features from the closest variant → save as new `configs/*_defconfig` → `kconfig2variants --all --vscode` → appears in the CMake Tools picker → add to publish variants if used |
| Retire a feature | Remove all conditions / CMake uses → remove symbol → regenerate → CI dead-symbol check confirms |
| Review | Kconfig changes by the variant-model owner; defconfig changes by the product owner; kit / toolchain changes by the build owner (they never touch the variant model) |

## 13. Rollout order

1. Tooling + layout + generator with drift check (Phases 1, 2, 5)
2. Convert the existing hand-written variant data into Kconfig + one defconfig
   per existing variant; generated JSON must equal the old JSON (regression gate)
3. CMake integration with active-variant copy and `docs` target (Phase 6)
4. VS Code / CMake Tools integration (Phase 7), incl. the two **Verify** points
5. CLI / CI wiring, CI matrix and consistency checks (Phases 8, 10)
6. Component fragments and composition (Phase 9)
7. Optional: feature-model analysis (UVL export + flamapy)

## 14. Open points and risks

- **kconfiglib maintenance:** pinned, little upstream activity; fallback is the
  Zephyr- or spl-core-vendored copy. Keep the generator thin.
- **Disabled-symbol semantics:** confirm sphinx-needs and sphinx-mounts treat
  `false`/`""` identically (§4.6).
- **ubCode re-index on external change** of `build/active/variants.json` (§8.3).
- **Reconfigure on variant switch** in CMake Tools (§8.3).
- **Stale copy:** the active copy reflects the last *successful* configure; the
  delete-on-failure rule (6.6) and the `var.meta.product` marker (§8.3) make
  this visible.
- **Multi-root workspaces:** one active copy per CMake project folder; a
  composed product with several CMake projects needs one top-level project that
  owns the variant selection.
- **List vs. bool features:** choose one style per namespace (§4.4).
- **No model analysis:** Kconfig does not detect dead features or count valid
  configurations; add UVL + flamapy only if required.
