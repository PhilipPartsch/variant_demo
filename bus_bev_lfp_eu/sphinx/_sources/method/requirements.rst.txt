Requirements engineering
========================

Requirements are written in the **150 % source** and resolved per product.
They are authored stage by stage in the AI workflow (``ubc agent``) and
reviewed against criteria files in ``metamodel/quality/``.

Levels
------

=================  ============================================  ==============================
Level              Rule                                          Traces to
=================  ============================================  ==============================
User story         "As a <role>, I …" — one capability a user     — (root of the V)
                   can observe; no implementation terms
Vehicle req        one *shall*, verifiable (unit, tolerance,      exactly one user story
                   condition); product values in ``value``
Software req       one *shall* for one subsystem's software      exactly one architecture element
=================  ============================================  ==============================

Writing rules
-------------

- **One statement per need**; one or two sentences.
- **Product-specific values** are not written into the text but into the
  ``value`` field with a variant function, so the requirement stays one need:
  ``:value: <<mcs: 1000 kW, 350 kW>>``.
- **Variant-specific requirements** are gated with an ``if`` block on the
  variant data (e.g. ``.. if:: var.vehicle.type == 'bus'``) or live in a
  variant folder (``region/eu``, ``region/na``).
- **Alternatives** (same requirement, different content per product) share one
  id in complementary ``if`` blocks — e.g. ``REQ_ENERGY_SOURCE``: state of charge
  for battery-electric products, fuel level for diesel.
- **Imported BMS requirements** are context, never edited or restated; CV needs
  reference them and link only to BMS interface needs.

Workflow and review
-------------------

The stages are configured in ``[workflow]`` of ``ubproject.toml``:
``user_stories`` → ``reqs`` → ``archs`` / ``bms_allocation`` → ``swreqs`` →
``code`` → ``tests``, plus ``risks`` and ``decisions``.

- ``ubc agent next`` names the next stage; ``ubc agent gaps`` lists what is
  missing per product.
- An independent review (separate context) scores every need against the
  criteria of its type (e.g. *atomicity*, *verifiability*, *parent fit*,
  *variant consistency*) and stores a verdict in ``.pharaoh/verdicts/``.
- A need is gated as strongly as its parent (*variant consistency*); no
  build-type or kit conditions.
