"""L3 — documentation per product (T§5), every check for ubc and Sphinx."""
import json

import pytest

from conftest import A, B, BEV, D, N, PRODUCTS, ROOT, SITE, authored, local
from normalize import normalize
from oracle import (ALLOCATES, ALTERNATIVE, BMS_CHEMISTRY, ENERGY_IMPL_TITLE, PAGES, PRESENT, VALUE)

TOOLS = ("ubc", "sphinx")
GOLDEN = ROOT / "tools/tests/golden"


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("product", PRODUCTS)
def test_doc01_presence(site, product, tool):
    needs = local(site[product][tool])
    expected = {i for i, where in PRESENT.items() if product in where}
    authored = {i for i in needs if not i.startswith(("TRES_", "GAP_"))}
    assert authored == expected, f"missing {sorted(expected - authored)}, unexpected {sorted(authored - expected)}"


@pytest.mark.parametrize("tool", TOOLS)
def test_doc02_value_fields(site, tool):
    for nid, per in VALUE.items():
        for product, value in per.items():
            assert site[product][tool][nid]["value"] == value, (nid, product)


@pytest.mark.parametrize("product", PRODUCTS)
def test_doc03_variant_data_in_text(product):
    data = json.loads((ROOT / f"variants/{product}.json").read_text())
    for tool in ("sphinx", "ubcode"):
        html = (SITE / product / tool / "index.html").read_text()
        assert product in html and data["powertrain"]["type"] in html, tool
        if data["bms"]["chemistry"]:
            assert data["bms"]["chemistry"] in html, tool


@pytest.mark.parametrize("tool", TOOLS)
def test_doc04_link_variant(site, tool):
    for nid, per in ALLOCATES.items():
        for product, targets in per.items():
            assert sorted(site[product][tool][nid].get("allocates") or []) == targets, (nid, product)


@pytest.mark.parametrize("tool", TOOLS)
def test_doc05_alternatives(site, tool):
    for nid, per in ALTERNATIVE.items():
        for product, phrase in per.items():
            assert phrase in site[product][tool][nid]["content"], (nid, product)


def test_doc06_choose():
    pytest.skip("release-gated: sphinx-needs 8.5.0 has no `choose` (migration: plan 20)")


@pytest.mark.parametrize("product", PRODUCTS)
def test_doc07_file_variants(product):
    for page, where in PAGES.items():
        for tool in ("sphinx", "ubcode"):
            assert (SITE / product / tool / page).exists() == (product in where), (tool, page)


@pytest.mark.parametrize("tool", TOOLS)
def test_doc08_bms_import(site, tool):
    for product in PRODUCTS:
        bms = {i: n for i, n in site[product][tool].items() if i.startswith("BMS_")}
        if product == D:
            assert not bms
            continue
        assert len(bms) == 205
        assert bms["BMS_REQ_CELL_VOLTAGE_LIMITS"]["chemistry"] == BMS_CHEMISTRY[product]
        assert all(n["status"] == "imported" for n in bms.values())


@pytest.mark.parametrize("tool", TOOLS)
def test_doc09_code_needs(site, tool):
    for product in PRODUCTS:
        code = {i for i, n in local(site[product][tool]).items() if n["type"] in ("impl", "test")}
        assert code == {i for i, w in PRESENT.items() if i.startswith(("IMPL_", "TEST_")) and product in w}, product


@pytest.mark.parametrize("tool", TOOLS)
def test_doc09b_same_id_two_implementations(site, tool):
    for product in PRODUCTS:
        need = site[product][tool]["IMPL_VCU_ENERGY_DISPLAY"]
        assert need["title"] == ENERGY_IMPL_TITLE[product]
        assert need["implements"] == ["SWREQ_VCU_ENERGY_DISPLAY"]


@pytest.mark.parametrize("product", PRODUCTS)
def test_doc10_parity(site, product):
    u, s = site[product]["ubc"], site[product]["sphinx"]
    assert set(u) == set(s)
    diff = []
    for nid in u:
        keys = set(u[nid]) & set(s[nid])
        if normalize(u[nid], keys) != normalize(s[nid], keys):
            a, b = normalize(u[nid], keys), normalize(s[nid], keys)
            diff.append((nid, {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}))
    assert not diff, diff[:5]


@pytest.mark.parametrize("product", PRODUCTS)
def test_doc11_golden(site, product):
    golden = GOLDEN / f"{product}.needs.json"
    if not golden.exists():
        pytest.fail(f"no golden file {golden.name}: run tools/tests/update_golden.py and review the result")
    current = {i: normalize(n) for i, n in sorted(authored(local(site[product]["ubc"])).items())}
    assert current == json.loads(golden.read_text())
    assert json.loads((GOLDEN / f"{product}.variants.json").read_text()) == \
           json.loads((ROOT / f"variants/{product}.json").read_text())
