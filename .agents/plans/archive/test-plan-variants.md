# Test plan: variant management with Kconfig, CMake Tools, sphinx-needs and sphinx-mounts

Product-independent test plan for:

- [variant-mechanisms.md](variant-mechanisms.md) — how documents consume `var.*`
  (fields, links, `if`/`choose`, `variant_sources`, mounts)
- [kconfig-variant-configuration.md](kconfig-variant-configuration.md) — how
  variant data is defined (Kconfig), generated, built (CMake) and selected in
  VS Code (CMake Tools)

Section references like `K§6` point to the Kconfig plan, `M§4` to the
mechanisms plan.

## 1. Scope

| In scope | Out of scope |
|---|---|
| Generator `kconfig2variants` (conversion rules, validation, outputs) | Correctness of the product's own requirements content |
| CMake integration (configure, active-variant copy, component selection, `docs` target) | Code functionality of the product |
| VS Code / CMake Tools / ubCode behaviour on variant selection | kconfiglib, Sphinx, sphinx-needs internals (only their observable behaviour) |
| All doc-level variant mechanisms, in ubc **and** sphinx-build | Publishing (ubTrace etc.) beyond `needs.json` export |
| CI checks (drift, registry, coverage, hygiene) — including that they **fail** when they should | |
| Composition of products (fragments, namespaces, mounts) | |

## 2. Test strategy

| Level | What | How | Automation |
|---|---|---|---|
| L0 Spikes | Open **Verify** points from both plans | Throw-away prototypes, result recorded as a decision | Manual, once |
| L1 Unit | Generator conversion and validation | pytest on small fixture Kconfigs | Full, every PR |
| L2 Integration | CMake configure/build, docs build per product | pytest/ctest driving `cmake`, `ubc`, `sphinx-build` | Full, every PR |
| L3 Golden | Per-product expected docs/needs | Compare `needs.json` against committed golden files | Full, every PR |
| L4 Negative / mutation | CI checks catch defects | Apply a known defect to a copy of the fixture, expect failure | Full, every PR |
| L5 IDE | VS Code + CMake Tools + ubCode behaviour | Manual checklist (later: VS Code extension test harness) | Manual, per release / tool upgrade |
| L6 Platform | Paths, symlinks, shells | L1–L3 on Linux, macOS, Windows | CI matrix, nightly |

**Rule:** every **Verify** point is resolved by a spike (L0) **before** the
conventions depending on it are frozen.

## 3. Test fixture: reference product

A minimal, product-neutral fixture that exercises every mechanism. It lives in
`tests/fixture/` and is not a real product.

### 3.1 Feature model (`tests/fixture/Kconfig`)

| Symbol | Type | Purpose |
|---|---|---|
| `PROD__FAMILY` | named choice: `A`, `B` | enum conversion, complementary `if` / `choose` |
| `MARKET__REGION` | named choice: `EU`, `NA` | second axis, `variant_sources` |
| `FEATURE__X` | bool | `if`, link variant, component selection |
| `FEATURE__Y` | bool, `depends on FEATURE__X` | disabled-symbol value, dependency warning |
| `COMP__LIMIT` | int, `range 1 100` | int conversion, range violation |
| `COMP__LABEL` | string `"2.50"` | string stays string |
| `BUNDLE__EXT` | bool | mount with `if` |
| `components/comp/Kconfig` | `rsource`d fragment, namespace `COMP__` | composition |

### 3.2 Product configurations

Designed so that **every condition is true in ≥1 and false in ≥1 product**:

| Product | FAMILY | REGION | X | Y | LIMIT | EXT |
|---|---|---|---|---|---|---|
| `p1_defconfig` | A | EU | n | (n, disabled) | 10 | n |
| `p2_defconfig` | B | EU | y | y | 50 | y |
| `p3_defconfig` | A | NA | y | n | 100 | n |

### 3.3 Docs fixture (one example per mechanism)

| ID | Mechanism | Content |
|---|---|---|
| D1 | Field `<<[...]>>` | `REQ_F1.limit_class: <<[var.comp.limit > 40]: high, low>>` |
| D2 | Field `<{ }>` | `REQ_F2.label: <{ var.comp.label }>` |
| D3 | Named variant | `[needs.variants] fam_b = "var.prod.family == 'b'"`, used in `REQ_F3` |
| D4 | Link variant | `SPEC_L1` links `REQ_BASE` always, `REQ_X` only if `FEATURE__X` |
| D5 | `if` | `REQ_X` inside `if var.feature.x == True` |
| D6a | complementary `if` (interim) | `REQ_C` in two complementary `if` blocks by `var.prod.family`, same ID |
| D6b | `choose` (**release-gated**) | the same content as D6a written with `choose`/`when`/`otherwise`; enabled once the pinned sphinx-needs contains `choose` |
| D7 | `variant_sources` | `region/na/**` only if `var.market.region == 'na'` |
| D8 | Mount | `tests/fixture_bundle/` mounted if `var.bundle.ext == True` |
| D9 | Marker | landing page shows `<{ var.meta.product }>` |

### 3.4 Oracle (golden expectations)

| Check | p1 | p2 | p3 |
|---|---|---|---|
| `REQ_F1.limit_class` | low | high | high |
| `REQ_F2.label` | 2.50 | 2.50 | 2.50 |
| `REQ_X` exists | no | yes | yes |
| `SPEC_L1` links | REQ_BASE | REQ_BASE, REQ_X | REQ_BASE, REQ_X |
| `REQ_C` branch | A | B | A |
| `region/na/*` built | no | no | yes |
| Bundle mounted | no | yes | no |
| `comp` code built | no | yes | yes |

Golden files: `tests/golden/<product>.needs.json` and
`tests/golden/<product>.variants.json`.

## 4. L0 — Spikes (resolve Verify points first)

| ID | Question | Pass = decision recorded | Plan ref |
|---|---|---|---|
| SP-01 | Exact variant syntax for link fields with several IDs | Working syntax + example in M§4 | M§4 |
| SP-02 | `[variants]` vs `[needs] variant_data*`: which do sphinx-needs, ubc, sphinx-mounts read? | One location usable by all three | M§1.4 |
| SP-03 | Minimum versions of sphinx-needs / ubc / sphinx-mounts for `var.*`, `if`, `variant_sources`; **release version of `choose`** (not in stable 8.5.0) and ubc support for it | Versions pinned; `choose` release tracked | M§11 |
| SP-04 | Do needs and mounts treat `false` / `0` / `""` of disabled symbols identically? | Same result in both | K§4.6 |
| SP-05 | ubc vs sphinx-build parity for `variant_sources` and mounts | Identical document set per product | M§9 |
| SP-06 | Does CMake Tools reconfigure automatically on a variant switch? | Yes, or a documented workaround | K§8.3 |
| SP-07 | Does the ubCode extension re-index when `build/active/variants.json` changes externally? | Yes, or a reload task | K§8.3 |
| SP-08 | Codelinks markers linking to a need gated by `if`/file rule | Chosen pattern (gate above marker level or gated `src-trace` pages) | M§11 |
| SP-09 | Bare boolean `var.x` in `if` vs sphinx-mounts grammar | Confirm `== True` works everywhere | K§4.2 |

## 5. L1 — Generator unit tests

| ID | Test | Expected | Ref |
|---|---|---|---|
| GEN-01 | `A__B__C` symbol | nested `var.a.b.c` | K§4.1 |
| GEN-02 | Upper-case symbol | lower-case keys | K§4.1 |
| GEN-03 | Symbol without namespace (`FOO`) | generator error | K§4.1 |
| GEN-04 | Legacy key in mapping table | mapped path used | K§4.1 |
| GEN-05 | `bool` y / n | `true` / `false` (JSON booleans) | K§4.2 |
| GEN-06 | `int`, `hex` | JSON integers | K§4.2 |
| GEN-07 | `string "2.50"` | `"2.50"` (not `2.5`) | K§4.2 |
| GEN-08 | `tristate` symbol in model | generator error | K§4.2 |
| GEN-09 | Named choice | one string, e.g. `"b"`; option bools **absent** from JSON, **present** in `autoconf.h` | K§4.3 |
| GEN-10 | Feature list derivation (if enabled for a namespace) | uniform list of enabled names | K§4.4 |
| GEN-11 | Symbol with unmet dependency (`FEATURE__Y` in p1) | emitted as `false` | K§4.6 |
| GEN-12 | Defconfig assigns undefined symbol | error, non-zero exit | K§6 |
| GEN-13 | Defconfig assigns `FEATURE__Y=y` without `FEATURE__X` | error ("assigned y but got n") | K§6 |
| GEN-14 | `COMP__LIMIT=500` (out of range) | error | K§6 |
| GEN-15 | Fragments `base` + `market` + product | later fragment wins, fixed order | K§5 |
| GEN-16 | Run twice | byte-identical outputs, sorted keys | K§6 |
| GEN-17 | Run twice, unchanged input | output files not rewritten (mtime unchanged) | K§6 |
| GEN-18 | Output validated against `var.*` rules (no `_` keys, uniform lists) | invalid data → error | K§6 |
| GEN-19 | `var.meta.product` present | equals defconfig name | K§8.3 |
| GEN-20 | Generator CLI | has **no** kit / build-type parameter | K§0 P3 |
| GEN-21 | `autoconf.h`, `autoconf.cmake`, `variants.json` | consistent values for every symbol | K§6 |
| GEN-22 | `--vscode` | `cmake-variants.json` has one choice per defconfig; tasks `inputs` match | K§6 |
| GEN-23 | `--check` with a hand-edited committed JSON | fails, names the file | K§6 |

## 6. L2 — CMake integration tests

| ID | Test | Expected | Ref |
|---|---|---|---|
| CMK-01 | Configure without `VARIANT` / unknown `VARIANT` | configure fails with clear message | K§7 6.1 |
| CMK-02 | Configure p1 | `kconfig/` outputs exist; `build/active/variants.json` equals them | K§7 6.2, 6.6 |
| CMK-03 | Configure with a broken defconfig | `FATAL_ERROR`; `build/active/variants.json` **deleted** | K§7 6.6 |
| CMK-04 | Touch `Kconfig`, a fragment, the defconfig; run build | reconfigure + regenerate happen | K§7 6.3 |
| CMK-05 | Component selection p1 vs p2 | `comp` target absent in p1, present in p2 | K§7 6.4 |
| CMK-06 | `autoconf.h` on include path | test source using `CONFIG_*` compiles | K§7 6.5 |
| CMK-07 | Same product, Debug vs Release vs other kit | `variants.json` byte-identical in all build dirs | K§0 P3 |
| CMK-08 | `docs` target from Debug and from Release | same output dir `build/docs/<product>`; identical `needs.json` | K§7 6.8 |
| CMK-09 | `project(<name> NONE)` driver | generator + `docs` target work without compilers | K§7 6.9 |
| CMK-10 | `build/active/VARIANT` marker | equals the last successfully configured product | K§7 6.7 |
| CMK-11 | Switch build dir p1 → p2 → p1 | active copy follows the last configure | K§7 6.6 |

## 7. L3 — Documentation mechanism tests (per product, both toolchains)

Each test runs for p1, p2, p3 with **ubc** and with **sphinx-build -W**, and
compares against the oracle (§3.4).

| ID | Test | Expected | Ref |
|---|---|---|---|
| DOC-01 | D1 field `<<[...]>>` | value per oracle | M§3 |
| DOC-02 | D2 `<{ }>` | `"2.50"` rendered unchanged | M§3 |
| DOC-03 | D3 named variant | value per family | M§3 |
| DOC-04 | D4 link variant | link targets per oracle; incoming links mirrored | M§4 |
| DOC-05 | D5 `if` | `REQ_X` present/absent per oracle | M§5 |
| DOC-06a | D6a complementary `if` | correct block per oracle; same ID; needs of the other block do not exist | M§5.1 |
| DOC-06b | D6b `choose` (**release-gated**) | same result as DOC-06a, in ubc and sphinx-build | M§5 |
| DOC-06c | Migration D6a → D6b (**release-gated**) | per-product `needs.json` identical before and after | M§5.2 |
| DOC-07 | D7 `variant_sources` | files absent in p1/p2; toctree reference reported as INFO; `-W` passes | M§6 |
| DOC-08 | D8 mount with `if` | bundle docnames under `mount_at` only in p2; attached to toctree | M§7 |
| DOC-09 | D9 marker | landing page shows the product name | K§8.3 |
| DOC-10 | ubc vs sphinx `needs.json` | identical per product (after normalising volatile fields) | K§11 |
| DOC-11 | Golden comparison | `needs.json` equals `tests/golden/<product>.needs.json` | — |

## 8. L4 — Negative and mutation tests (the checks must fail)

Each test copies the fixture, applies one defect, and expects the named check
to fail with a message pointing at the defect.

| ID | Injected defect | Expected failing check | Ref |
|---|---|---|---|
| NEG-01 | Unconditional link to `REQ_X` (gated) | `-W` build fails for p1 (dangling link) | M§8.1 |
| NEG-02 | `variant_sources` rule using unknown `var.foo` | `mounts.variant_rule_unevaluable` reported → CI fails | M§6 |
| NEG-03 | Condition uses key not in the generated schema | condition-registry check fails | K§11 |
| NEG-04 | Kconfig symbol used nowhere | dead-symbol check fails | K§11 |
| NEG-05 | Condition true in all products | branch-coverage check fails | K§11 |
| NEG-06 | Kconfig symbol `BUILD__DEBUG` / `var.build.*` used | build-configuration check fails | K§4.7 |
| NEG-07 | Visible symbol without `help` / with `tristate` / without prefix | hygiene check fails | K§11 |
| NEG-08 | Hand-edited `variants/p1.json` or `.vscode/cmake-variants.json` | drift check fails | K§6 |
| NEG-09 | Two complementary `if` blocks true at once (overlapping conditions) | duplicate-ID build error | M§5.1, M§8.5 |
| NEG-13 | No complementary `if` block true for one product (gap in conditions) | alternatives check fails (shared ID missing) | M§8.5 |
| NEG-10 | Mount docname collides with host doc | `docname conflict` → CI fails | M§7 |
| NEG-11 | `variant_data_file` points at missing file | sanity check fails (no silent empty values) | K§9 8.1 |
| NEG-12 | Bare boolean `var.feature.x` in a `variant_sources` rule | rejected by sphinx-mounts → CI fails | K§4.2 |

## 9. L5 — IDE tests (VS Code + CMake Tools + ubCode)

Manual checklist; run on each supported OS when tool versions change.

| ID | Steps | Expected | Ref |
|---|---|---|---|
| IDE-01 | Fresh clone, open folder | CMake Tools configures default product; `build/active/variants.json` exists; ubCode hover on D1 shows default value; landing page marker shows product | K§8.2, 8.3 |
| IDE-02 | Status bar: switch variant p1 → p2 | reconfigure runs; within a few seconds ubCode shows p2 values (D1 `high`, `REQ_X` resolvable) | K§8.3 (SP-06/07) |
| IDE-03 | Switch build type Debug → Release (same product) | variant data unchanged; ubCode view unchanged | K§0 P3 |
| IDE-04 | Switch kit prod → test | same as IDE-03 | K§0 P3 |
| IDE-05 | C/C++: switch p1 → p2 | IntelliSense greys/ungreys `#ifdef CONFIG_FEATURE__X` blocks | K§8.2 |
| IDE-06 | Task "Configure features" | `guiconfig`/`menuconfig` opens for the picked product | K§8.4 |
| IDE-07 | Change a feature, task "Save variant" | minimal defconfig written; reconfigure; diff shows only the change | K§8.4 |
| IDE-08 | Add `p4_defconfig`, run "Regenerate variant list" | p4 appears in the CMake Tools picker and in task inputs | K§8.4 |
| IDE-09 | Break the active defconfig, reconfigure | error visible in CMake output; active copy deleted; ubCode shows missing marker, **not** old values | K§7 6.6 |
| IDE-10 | Build `docs` via CMake Tools target picker; task "Open docs" | docs of the active product open | K§8.4 |
| IDE-11 | Edit a component `Kconfig` in the editor and save | reconfigure on next build; new symbol visible in configurator | K§7 6.3 |

## 10. Composition tests

| ID | Test | Expected | Ref |
|---|---|---|---|
| CMP-01 | Component built standalone with its own defconfigs | builds and docs pass | K§10 |
| CMP-02 | Host defconfig sets component options | component subtree `var.comp.*` in host JSON equals what the component expects | K§10 |
| CMP-03 | Host derives a component option via `select`/`default` | derived value in JSON; dependency violation → error | K§10 |
| CMP-04 | Component docs read a host key (namespace violation) | registry check fails | K§10 |
| CMP-05 | Component Kconfig revision ≠ mounted docs revision | CI pin check fails | K§10 |

## 11. L6 — Platform tests

Run L1–L3 on Linux, macOS and Windows:

| ID | Focus | Expected |
|---|---|---|
| PLT-01 | Path resolution (relative `-c`, `rsource`, `mount_at`) | identical outputs on all OSes |
| PLT-02 | Line endings / encoding of generated files | byte-identical generated JSON |
| PLT-03 | Build dir names with `/` in product names (if allowed) | works or rejected consistently |

## 12. Non-functional

| ID | Test | Target (to be agreed) |
|---|---|---|
| NF-01 | Generator runtime per product | < 2 s |
| NF-02 | Variant switch in IDE until ubCode shows new values | < 10 s |
| NF-03 | CI docs matrix duration per product | tracked, no regression > 20 % |

## 13. Regression gate for migration

| ID | Test | Expected | Ref |
|---|---|---|---|
| REG-01 | Existing hand-written variant JSON vs generated JSON from converted Kconfig | equal (after agreed key renames) | K§13 step 2 |
| REG-02 | Existing `needs.json` per variant before vs after migration | equal | K§13 |

## 14. Traceability: plan sections → tests

| Plan section | Tests |
|---|---|
| K§0 P3 build config not in variant model | GEN-20, CMK-07, CMK-08, NEG-06, IDE-03, IDE-04 |
| K§4 conventions | GEN-01 … GEN-11, NEG-07, NEG-12 |
| K§5 defconfigs | GEN-15, IDE-07 |
| K§6 generator | GEN-12 … GEN-23 |
| K§7 CMake | CMK-01 … CMK-11 |
| K§8 VS Code / CMake Tools | IDE-01 … IDE-11, SP-06, SP-07 |
| K§9 CLI wiring | NEG-11, DOC-10 |
| K§10 composition | CMP-01 … CMP-05 |
| K§11 CI checks | NEG-03 … NEG-08 |
| M§3 fields | DOC-01 … DOC-03 |
| M§4 links | SP-01, DOC-04, NEG-01 |
| M§5 blocks | DOC-05, DOC-06a, DOC-06b, DOC-06c, NEG-09, NEG-13 |
| M§6 file variants | DOC-07, NEG-02 |
| M§7 mounts | DOC-08, NEG-10 |
| M§8 consistency | NEG-01, NEG-03, NEG-09 |
| M§1.4 / M§11 open points | SP-02, SP-03, SP-05, SP-08 |

## 15. Entry and exit criteria

**Entry (start of L1–L4):** spikes SP-01 … SP-05 and SP-09 decided; fixture and
oracle reviewed.

**Release-gated tests** (DOC-06b, DOC-06c) are skipped, not failed, while the
pinned sphinx-needs has no `choose`; they become mandatory as soon as the pin is
raised.

**Exit (plan accepted as implemented):**
- L1–L4 green on all three products, in ubc and sphinx-build, on Linux.
- Every NEG test fails as expected (a check that never fails is not a check).
- L5 checklist passed on at least one OS; SP-06 / SP-07 outcomes documented.
- L6 green on Linux, macOS, Windows (nightly).
- Traceability table: every plan section has ≥ 1 passing test.

## 16. Execution order

1. Spikes (L0) → update both plans with decisions
2. Fixture + oracle + golden files
3. L1 generator tests (test-first, together with the generator)
4. L2 CMake tests
5. L3 docs tests + L4 negative tests
6. L5 IDE checklist
7. L6 platform matrix, non-functional, regression gate
