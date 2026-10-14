Metamodel
=========

The metamodel is defined in ``ubproject.toml`` (need types, links, fields) and
``metamodel/schemas.json`` (rules). It follows the metamodel of the BMS, so
that both products read the same; the CV platform adds three types
(``bms_block``, ``system``, ``subsystem``), three links (``allocates``,
``part_of``, ``covers``) and two fields (``value``, ``product``).

V-model chain
-------------

::

   user_story ◄─traces_to── req ◄─satisfies── arch ◄─refines── swreq ◄─implements── impl
                             ▲                 ▲                  ▲
                             │ satisfies       │ affects          └─verifies── test ◄─results_for── test_result
                         bms_block           decision
                             │ allocates
                             ▼
                   BMS_REQ_* (imported, interface needs)

   risk ──mitigates──► req          gap ──gap_for──► any need

   System level: the vehicle is the system; the vehicle-level user stories and
   requirements belong to it by their level.

   req ◄─covers── subsystem ──part_of──► system (SYS_VEHICLE)
                      ▲
                      └──part_of── arch / bms_block

Need types
----------

===========  ==========  =========================================  =================================
Type         Prefix      Purpose                                    Where
===========  ==========  =========================================  =================================
system       ``SYS_``    the vehicle; exactly one per product       ``docs/system/overview.rst``
subsystem    ``SUB_``    subsystem of the vehicle (VCU, CHG, ENG,   ``docs/system/overview.rst``
                         BMS); covers the reqs allocated to it
user_story   ``US_``     one user-observable capability             ``docs/vehicle/user_stories.rst``
req          ``REQ_``    vehicle requirement, one shall             ``docs/vehicle``, ``docs/region``
arch         ``ARCH_``   architecture element of a CV subsystem     ``docs/subsystems/{vcu,chg,eng}``
bms_block    ``BB_``     black-box view of the BMS                  ``docs/subsystems/bms``
swreq        ``SWREQ_``  software requirement of a CV subsystem     ``docs/subsystems/{vcu,chg,eng}``
impl         ``IMPL_``   implementation, one-line marker in C code  ``src/<subsystem>``
test         ``TEST_``   test, one-line marker in C test code       ``tests/<subsystem>``
test_result  ``TRES_``   imported test result of one product        ``docs/_global/test_results.rst``
risk         ``RISK_``   vehicle-level risk                         ``docs/_global/risks.rst``
decision     ``DEC_``    design decision                            ``docs/_global/decisions.rst``
gap          ``GAP_``    imported workflow gap of one product       ``docs/_global/gaps.rst``
===========  ==========  =========================================  =================================

Links and fields
----------------

- Links: ``traces_to``, ``satisfies``, ``refines``, ``implements``,
  ``verifies``, ``results_for``, ``mitigates``, ``affects``, ``gap_for``
  (``motivates`` is declared but unused), ``allocates`` (``arch`` /
  ``bms_block`` → BMS interface requirement, with variant functions),
  ``part_of`` (``arch`` / ``bms_block`` → subsystem, subsystem → system) and
  ``covers`` (subsystem → req, with variant functions).
- ``status``: ``draft`` → ``review`` → ``approved``; ``imported`` for every
  BMS need.
- ``value``: the product-specific value of a vehicle requirement, written with
  a variant function, e.g. ``<<bus: 250 kW, 450 kW>>``.
- ``product``: the product a test result or gap belongs to.
- The BMS fields (``chemistry``, test-result and gap fields) are declared so
  that imported needs keep them.

Rules
-----

- **Schema rules** (``metamodel/schemas.json``) check id prefixes, the upward
  traces and required fields as *violations*; reverse coverage ("every req is
  satisfied") is a *warning*, because it is owed by a later stage. They apply
  to local needs only; imported BMS needs are validated by the BMS.
- **System level:** exactly one system; every subsystem is ``part_of`` it and
  covers ≥ 1 req; every ``arch`` / ``bms_block`` is ``part_of`` exactly one
  subsystem; every req is covered by a subsystem. A subsystem covers exactly
  the reqs its parts satisfy (checked per product by the tests).
- **BMS links:** ``allocates`` may target only BMS requirements tagged
  ``interface``; every ``bms_block`` allocates at least one.
- **Variants:** a need is gated by the same or a stronger condition than its
  parent, so that no link dangles in any product. Conditions use the variant
  data ``var.*`` and are spelled out in ``if`` blocks; alternatives share one
  id in the ``when`` / ``otherwise`` branches of a ``choose`` (code: ``#if`` /
  ``#else``).
- **Warning-free:** ``ubc check`` passes without warnings for every product.
