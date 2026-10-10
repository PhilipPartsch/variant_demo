Test strategy
=============

Everything is tested **per product** and with **both toolchains** (ubc and
Sphinx). One command runs the automated levels — the same command CI calls::

   tools/test_all.sh        # tools/build_all.sh + pytest tools/tests

Levels
------

=====  ======================  ==============================================================
Level  Name                    What is checked
=====  ======================  ==============================================================
L1     Tooling                 generator, check scripts and importers (unit tests)
L2     Build integration       CMake configure per product, active copies, BMS and component
                               selection, fixed build type, entry points
L3     Docs per product        needs present / absent, values, link variants, alternatives,
                               file variants, BMS import, code needs, ubc ↔ Sphinx parity,
                               golden files
L4     Content                 coverage of types / links / fields, warning-free traceability,
                               no dangling links, allocations, review verdicts, brevity
L5     Negative / mutation     every check fails on the defect it exists for (one defect per
                               test, in a copy of the repository, with a clean control)
L6     C code                  CTest per product, feature tests, imported results,
                               every software requirement verified by a passing test
L7     Mechanism regression    generic elements per variant mechanism on a side branch
L8     IDE                     CMake Tools and ubCode behaviour (manual checklist)
L9     Platform                macOS locally, Linux in CI
=====  ======================  ==============================================================

Oracles
-------

- **Expectation tables** per product (which need exists where, values,
  alternatives) — ``tools/tests/oracle.py``.
- **Golden files** — the authored needs of each product,
  ``tools/tests/golden/``; they change only through a reviewed commit.
- **Known toolchain differences** that are not variant behaviour are
  normalised before comparing (``tools/tests/normalize.py``).

Test evidence in the documentation
----------------------------------

- Each C test prints ``PASS`` / ``FAIL`` with its test id; the CTest JUnit
  report of every product is imported as ``test_result`` needs with the
  ``product`` field (``tools/import_test_results.py``) and linked to the test
  (``results_for``) and the vehicle requirements it is evidence for.
- The workflow gaps of every product are imported as ``gap`` needs
  (``tools/import_gaps.py``).
- Both are shown per product: the results of other products are gated out.
