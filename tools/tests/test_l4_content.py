"""L4 — content (T§6): coverage matrix, traceability, gating, allocations,
review verdicts, brevity."""
import json
import re
import tomllib
import warnings

import pytest

from conftest import BEV, PRODUCTS, ROOT, SITE, UBC, local, run
from oracle import ALTERNATIVE, PAGES

CONFIG = tomllib.loads((ROOT / "ubproject.toml").read_text())
LINKS = set(CONFIG["needs"]["links"])


def union(site, tool="ubc"):
    out = {}
    for p in PRODUCTS:
        out.update(local(site[p][tool]))
    return out


def test_cnt01_coverage_matrix(site):
    needs = union(site)
    types = {n["type"] for n in needs.values()}
    assert types >= {"user_story", "req", "arch", "bms_block", "swreq", "impl", "test", "risk", "decision",
                     "test_result", "gap"}, types
    used = {l for n in needs.values() for l in LINKS if n.get(l)}
    assert used >= LINKS - {"motivates"}, f"unused links: {LINKS - used}"   # motivates: declared, unused (as in the BMS)
    assert any(n.get("value") for n in needs.values()), "value field"
    assert {n["product"] for n in needs.values() if n["type"] == "test_result"} == set(PRODUCTS), "product field"
    assert len(ALTERNATIVE) >= 2 and len(PAGES) >= 4  # alternatives and file variants covered (DOC-05, DOC-07)


@pytest.mark.parametrize("product", PRODUCTS)
def test_cnt02_traceability_warning_free(site, product):
    log = (SITE / product / "logs/ubc-check.log").read_text()
    assert "warning" not in log.split("Found")[-1] and "error" not in log.split("Found")[-1], log[-500:]


@pytest.mark.parametrize("tool", ("ubc", "sphinx"))
@pytest.mark.parametrize("product", PRODUCTS)
def test_cnt03_no_dangling_links(site, product, tool):
    needs = site[product][tool]
    dangling = [(i, l, t) for i, n in local(needs).items() for l in LINKS for t in (n.get(l) or []) if t not in needs]
    assert not dangling, dangling


@pytest.mark.parametrize("tool", ("ubc", "sphinx"))
def test_cnt04_allocations_target_interfaces(site, tool):
    for p in BEV:
        needs = site[p][tool]
        for i, n in local(needs).items():
            for t in n.get("allocates") or []:
                assert t.startswith("BMS_REQ_") and "interface" in needs[t].get("tags", []), (p, i, t)


def flipping_ids(site) -> set:
    """Alternatives with one id and the needs whose fingerprint follows them
    (plan 99 PH-01, PH-03): their verdict can be fresh in one product only."""
    alt = set(ALTERNATIVE) | {"IMPL_VCU_ENERGY_DISPLAY"}
    out = set(alt)
    for p in PRODUCTS:
        for i, n in local(site[p]["ubc"]).items():
            if any(t in alt for l in LINKS for t in (n.get(l) or [])):
                out.add(i)
    return out


@pytest.mark.parametrize("product", PRODUCTS)
def test_cnt05_review_verdicts(site, repo, product):
    repo.configure(product)
    p = run([UBC, "agent", "verdict-check", "-p", "."], cwd=repo.path)
    result = json.loads(p.out[p.out.index("{"):])
    assert not result["missing"] and not result["failing"] and not result["malformed"], result
    outdated = set(result["outdated"]) | set(result.get("unverifiable", []))
    unexpected = outdated - flipping_ids(site)
    assert not unexpected, f"outdated verdicts not explained by PH-01: {sorted(unexpected)}"
    if outdated:
        pytest.xfail(f"plan 99 PH-01 (verdict per id): {sorted(outdated)} outdated in {product}")


def test_cnt06_brevity(site):
    long = []
    for i, n in union(site).items():
        if n["type"] in ("decision", "test_result", "gap"):
            continue
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", (n.get("content") or "").strip()) if s]
        if len(sentences) > 2:
            long.append((i, len(sentences)))
    if long:
        warnings.warn(f"needs with more than two sentences (C§0): {long}")
