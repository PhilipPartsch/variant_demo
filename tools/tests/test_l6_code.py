"""L6 — C code (T§8): CTest per product, feature code, JUnit import,
verification coverage per product."""
import re
import xml.etree.ElementTree as ET

import pytest

from conftest import B, N, PRODUCTS, SITE, local

LINE = re.compile(r"^(PASS|FAIL) (TEST_[A-Z0-9_]+)$", re.M)


def results(product) -> dict:
    suite = ET.parse(SITE / product / "junit.xml").getroot()
    out = {}
    for case in suite.iter("testcase"):
        assert case.get("status") == "run" and case.find("failure") is None, case.get("name")
        out.update({t: r for r, t in LINE.findall(case.findtext("system-out") or "")})
    return out


@pytest.mark.parametrize("product", PRODUCTS)
def test_code01_ctest_passes(site, product):
    r = results(product)
    assert r and all(v == "PASS" for v in r.values()), r


def test_code02_feature_tests_per_product(site):
    ran = {p: set(results(p)) for p in PRODUCTS}
    assert {p for p in PRODUCTS if "TEST_CHG_MCS_HANDSHAKE" in ran[p]} == {N}
    assert {p for p in PRODUCTS if "TEST_CHG_PANTOGRAPH_SEQUENCE" in ran[p]} == {B}


@pytest.mark.parametrize("product", PRODUCTS)
def test_code03_junit_import(site, product):
    needs = local(site[product]["ubc"])
    tres = {n["results_for"][0]: n for n in needs.values() if n["type"] == "test_result"}
    tests = {i for i, n in needs.items() if n["type"] == "test"}
    assert set(tres) == tests, "docs/_global/test_results.rst is stale: run tools/import_test_results.py"
    assert set(tres) == set(results(product)), "imported results differ from the last CTest run"
    for t, n in tres.items():
        assert n["product"] == product and n["outcome"] == "passed", (t, n)


@pytest.mark.parametrize("product", PRODUCTS)
def test_code04_every_swreq_verified_by_a_passing_test(site, product):
    needs = local(site[product]["ubc"])
    passed = {t for t, r in results(product).items() if r == "PASS"}
    for i, n in needs.items():
        if n["type"] != "swreq":
            continue
        tests = {t for t, m in needs.items() if m["type"] == "test" and i in (m.get("verifies") or [])}
        assert tests & passed, f"{i} has no passing test in {product}"
