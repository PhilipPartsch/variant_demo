# Plan: Using sphinx-needs and sphinx-mounts variant mechanisms

Product-independent plan. The variant dimensions shown (`edition`, `platform`,
`features`) are placeholders for your own.

Sources:
- sphinx-needs: <https://sphinx-needs.readthedocs.io/en/stable/> (`if`, `parse_variants`, `variant_data`); `choose` is documented only under <https://sphinx-needs.readthedocs.io/en/latest/directives/choose.html> and is **not released yet** (stable is 8.5.0, without `choose`)
- sphinx-mounts: <https://sphinx-mounts.useblocks.com/en/latest/> (`[[source.mounts]]`, `[[source.variant_sources]]`)

Points that could not be confirmed in the docs are marked **Verify**.

## 0. Principles

1. **One 150% source.** All variants live in one document set. Each build sees
   one configuration, so it renders a "100%" product.
2. **One variant model.** Every mechanism reads the same `var.*` data. Nobody
   adds a second switch like Sphinx `tags` or `only::`.
3. **Use the narrowest mechanism that works.** Go up the list only when the
   smaller one can't express the variation:
   field → link → block (`if`/`choose`) → file (`variant_sources`) → bundle (`source.mounts` + `if`).
4. **Every branch gets built.** Each condition must be true in at least one CI
   configuration and false in at least one other.

## 1. Phase 1: Define the variant model

| Step | Action |
|---|---|
| 1.1 | List the variation dimensions (e.g. `edition`, `platform`, `features[]`, `safety_level`). Give each a type and its allowed values. |
| 1.2 | Write the base data to `variants.json`: nested dicts, leaves are str/bool/int/float or uniform lists. |
| 1.3 | Write one file per shipped configuration, e.g. `variants/<config>.json`, layered on the base. |
| 1.4 | Use **`[needs] variant_data_file`**: it is the only location sphinx-needs 8.5.0, ubc 0.35.0 and sphinx-mounts 0.2.0 all read; `[variants] data_file` is read by none of them (evaluated in [01-evaluation-result.md](01-evaluation-result.md), A1). |
| 1.5 | Write the condition rules: always use the `var.` prefix, no bare booleans (`var.debug == True`), and match types strictly (`var.debug == 0` is *false* for a bool). Use only grammar that both parsers accept: `== != < > in not in and or not`, `.startswith/.endswith`, `is None`. |
| 1.6 | Optionally define named variants (`needs_variants = {"pro": "var.edition == 'pro'"}`) so frequently used conditions have one name and one definition. |

**Exit criterion:** the variant model is documented and reviewed, and each
config file passes a schema check.

## 2. Choosing a mechanism

| What varies per variant | Mechanism |
|---|---|
| One field value of a need (status, ASIL, parameter, text snippet) | **Field variant** |
| Which needs a need traces to | **Link variant** |
| Whether a need, paragraph, table or section exists, or which of N alternatives appears | **Block variant** (`if` / `choose`) |
| A whole document, or a directory in this repo | **File variant** (`[[source.variant_sources]]`) |
| A whole external doc bundle (other repo, generated docs, supplier docs) | **Mount variant** (`[[source.mounts]]` with `if`) |

## 3. Phase 2: Field variants

- **Config:** set `parse_variants = true` on each `[needs.fields.<name>]` that
  may vary, and only on those. Give every one a `default`.
- **Authoring:**
  - Inline condition: `:status: <<[var.platform == "windows"]: win_auth, default_auth>>`
  - Named variant: `<<pro: value, fallback>>`
  - Data reference: `:note: Built for <{ var.platform }>`
- **Rules:**
  - Always write a fallback value.
  - Put values with real logic behind named variants.
  - Use `<{ }>` to show data. Use `<< >>` to choose between values.
  - Use `predicates` in the field config when a value depends on variant data
    and the rule is the same for every need.
- **Verification:** export `needs.json` per configuration and assert the
  expected values for a few sample needs.

## 4. Phase 3: Link variants

- **Config:** set `parse_variants = true` on each `[needs.links.<type>]` that
  may vary.
- **Authoring:** write the variant **per list item**:
  `:allocates: <<bev: BMS_REQ_A>>, <<bev: BMS_REQ_B>>` (named variant) or
  `<<[cond]: ID>>`; an item whose condition is false and that has no default is
  dropped. Inside `<< >>` the comma separates alternatives, so a whole-list
  switch is not possible (evaluated, B1).
- **Don't confuse this with conditional links** (`ID[status=="open"]`). Those
  *check* a link against the target's attributes; they don't select the link
  by variant. They can be combined: the variant selects the link, the
  condition checks it.
- **Rule:** a link that is active in a configuration must point at a need that
  exists in that configuration. This is the most common failure when combined
  with block or file variants.
- **Verification:** run each configuration with `-W` so dangling links fail.
  Keep one traceability matrix (needtable/needflow) per configuration.

## 5. Phase 4: Block variants (`if` / `choose`)

- **`if`:** `.. if:: var.edition == "pro"` for content that is present or absent.
- **`choose`:** `when`/`otherwise` for N alternatives. The first true branch wins.
  **Not released yet** — use the interim pattern below until the pinned
  sphinx-needs version contains it.
- **Rules:**
  - Conditions see **only `var.*`**, not need fields or IDs, because they are
    evaluated at parse time.
  - Content in a branch that isn't selected is never parsed. Its needs don't
    exist, and links to them dangle (see the link rule).
  - Alternative branches in a `choose` may reuse the same need ID: one ID,
    variant-specific content.
  - `choose` may contain only `when`, `otherwise` and comments, and branches
    can't come from `include`.
  - Once released, prefer `choose` with `otherwise` over several `if` blocks
    whose conditions are meant to exclude each other.
  - Known issue: sphinx-design `tab-item` inside `if` raises a warning.
- **When not to use it:** if only a single field differs, use a field variant
  so the need stays one object across configurations.

### 5.1 Interim pattern until `choose` is released: complementary `if` blocks

Write the alternatives as **complementary plain `if` blocks** — only the
released `if` directive, no additional directives, markers or comment
conventions (they would not be understood by ubCode). The blocks of one
alternative set are identified by the **need ID they share**:

```rst
.. if:: var.powertrain.type == "bev"

   .. req:: Energy source state
      :id: REQ_ENERGY_SOURCE

      ... battery variant ...

.. if:: not (var.powertrain.type == "bev")

   .. req:: Energy source state
      :id: REQ_ENERGY_SOURCE

      ... fuel variant ...
```

Rules:

- Each later block repeats the **negation of all earlier conditions**
  (that is what `choose` does implicitly: first true branch wins). The last
  block is the `otherwise` and is the negation of all others.
- Every alternative block defines the **same need ID** (as with `choose`).
  That ID is what ties the blocks together; no extra marker is needed.
- Exactly one block is true in every configuration:
  - two true at once → the build fails with a duplicate ID (desired signal);
  - none true → the ID is missing. A CI check catches this per product: every
    need ID defined inside `if` blocks with alternatives must exist in the
    `needs.json` of every configuration where its parent exists (§8, rule 5).
- Alternatives that contain no need (plain text only) cannot be checked this
  way — give them a need, or prefer a field variant (M§3).

### 5.2 Migration to `choose` once released

1. Pin the first sphinx-needs release containing `choose` (and confirm ubc
   supports it).
2. Convert each set of complementary `if` blocks (same need ID) mechanically:
   first block → `when` with its own condition, middle blocks → `when` with
   only their **own** condition (drop the repeated negations), last block →
   `otherwise`.
3. Keep the "alternative ID present in every configuration" check — it is
   useful for `choose` without `otherwise` too.
4. Per-product `needs.json` before and after must be identical (regression gate).

## 6. Phase 5: File variants (in-repo, `[[source.variant_sources]]`)

- **Config:**

  ```toml
  [[source.variant_sources]]
  if = "var.edition == 'pro'"
  files = ["reference/pro/**", "chapters/advanced.rst"]
  ```

- **Semantics:**
  - Rules only exclude. A file is built unless some matching rule is false.
  - Rule order doesn't matter.
  - A rule that references an unknown `var.*` key counts as false and emits
    `mounts.variant_rule_unevaluable`.
- **Layout convention:** group variant-specific docs in directories, e.g.
  `variants/<dimension>/<value>/...`, so the globs stay simple.
- **Glob rules:**
  - No `{a,b}` alternation, `..`, or absolute paths.
  - A rule must never be able to exclude `root_doc`.
- **Toctrees:** list variant files normally. When a rule explains why an entry
  is excluded, the warning drops to INFO (`mounts.variant_excluded_reference`),
  so `-W` still passes.

## 7. Phase 6: Mount variants (external bundles, `[[source.mounts]]`)

- **Config:**

  ```toml
  [[source.mounts]]
  dir = "../<bundle>"
  mount_at = "_mounted/<bundle>"
  attach_to = "index"
  if = "'<feature>' in var.features"
  ```

- **Use it for** sub-component docs, supplier documentation, generated API
  docs, or platform packages kept outside the host repo.
- **Rules:**
  - Always set `mount_at` to avoid docname collisions, and enable
    `strict_mount_at` in CI.
  - Use `attach_to` instead of hand-written toctree entries.
  - Set `path_check = "error"` in CI.
  - `variant_sources` rules gate whole `dir` mounts but don't narrow `files`
    mounts. Put file-list conditions on the mount's own `if`.
- **Needs inside bundles** follow the same link rule: a need in a gated bundle
  must not be a target of an unconditional link from the host.

## 8. Phase 7: Cross-cutting consistency

1. **Dependency rule:** if a need is gated (block, file or mount), every
   incoming link must be gated by the same or a stronger condition. Use named
   variants so both sides share one definition.
2. **ID policy:** IDs are unique per configuration. A shared ID is allowed only
   for alternatives that exclude each other (`choose` branches, complementary
   `if` blocks, or mounts whose
   `if` conditions exclude each other).
3. **Condition registry:** keep a list of all conditions, generated by grepping
   `<<[`, `.. if::`, `when::` and `if =`. Each `var.*` key used must exist in
   the model.
4. **Reporting:** for each configuration, produce `needs.json`, a
   coverage/traceability table and a list of excluded files. Diffs between
   configurations show variant drift.
5. **Alternatives complete** (interim, §5.1): a need ID defined in
   complementary `if` blocks exists exactly once in every configuration
   (zero → missing content; two → duplicate-ID build error). Derived from the
   sources and the per-configuration `needs.json` — no markers.

## 9. Phase 8: CI and tooling

- **Build matrix:** one job per `variants/<config>.json`, run with both
  `ubc build` and `sphinx-build -W -E -D needs_variant_data=...`, so the two
  tools agree.
- **Branch coverage check:** every condition is true in at least one
  configuration and false in at least one.
- **Alternatives check:** every need ID defined in complementary `if`
  blocks is present in every configuration (§8, rule 5).
- **Fail on:**
  - dangling links
  - `variant_rule_unevaluable`
  - `docname conflict`
  - `variant_data_location`
- **Unsuppress `needs.dynamic_function`:** `conf.py` currently suppresses it
  because `var.*` support isn't released yet. Re-enable the warning once the
  sphinx-needs release that supports `var.*` is pinned.

## 10. Rollout order

1. Variant model and CI matrix (Phase 1 and §9 skeleton)
2. Field variants
3. Link variants
4. Block variants
5. File variants
6. Mount variants
7. Consistency checks and reports (Phase 7)

Each step ships with at least one example and its CI check before the next
step starts.

## 11. Open points and risks

- **Link syntax:** confirm the exact variant syntax for multi-ID link fields (§4).
- **Shared config location:** answered — `[needs] variant_data_file` (§1.4).
- **Version requirements:** `var.*` needs an unreleased sphinx-needs build or
  ubc (see `conf.py`), and `if`/`choose`/`variant_sources` have minimum
  versions. Pin the versions.
- **`choose` not released:** stable sphinx-needs (8.5.0) has `if` but not
  `choose`/`when`/`otherwise`. Use complementary `if` blocks (§5.1) until the release, then
  migrate (§5.2). Confirm the release version and ubc support before the
  first demo.
- **Limits of parse-time conditions:** `if`, `choose` and file rules can't
  depend on need data. Anything that must react to needs belongs in filters or
  predicates.
