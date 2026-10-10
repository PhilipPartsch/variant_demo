Architecture modelling
======================

The architecture describes **what each element is and owns**, in present
tense, and satisfies the vehicle requirements. One element per distinct
responsibility; every vehicle requirement is satisfied by at least one CV
architecture element.

Elements
--------

- **CV subsystems** (``arch``, ``docs/subsystems/<x>/architecture.rst``):

  ======  ==========================  ================  ======================
  Name    Subsystem                   Products          Code
  ======  ==========================  ================  ======================
  VCU     Vehicle Control Unit        all               ``src/vcu``
  CHG     Charging Controller         battery-electric  ``src/chg``
  ENG     Engine Interface            diesel            ``src/eng``
  ======  ==========================  ================  ======================

  A subsystem that a product does not contain is excluded as a whole: its
  documentation folder by a file variant, its code by CMake.

- **BMS black boxes** (``bms_block``, ``docs/subsystems/bms/architecture.rst``):
  the BMS is an external product. Each black box satisfies a vehicle
  requirement and *allocates* the BMS interface requirements that realise it.
  BMS values are referenced through the allocated needs, never copied.
  A black box is not refined by CV software requirements.

- **Software requirements** refine one architecture element each; code and
  tests implement and verify them with one-line markers.

Variants in the architecture
----------------------------

- **Variant-specific elements** sit in the folder of their subsystem or in an
  ``if`` block (e.g. the door interlock for buses).
- **Alternatives** — the same element with a different design per product —
  share one id, e.g. ``ARCH_CHG_INLET``: MCS inlet, roof pantograph or no
  additional interface. The order of the alternatives is a recorded decision.
- **Link variants**: a link that exists only in some products is written with
  a variant function, e.g. ``:allocates: <<bev: BMS_REQ_POWER_DERATING>>``.
- In code, alternatives are ``#if`` / ``#else`` with the same need id; the
  product's compile database decides which marker becomes the need.

Decisions and risks
-------------------

- **Decisions** (``decision``) record context, alternatives, consequences and
  rationale, and *affect* the architecture elements they constrain.
- **Risks** (``risk``) are vehicle-level and *mitigated* by a requirement.
