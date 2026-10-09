"""L2 — build integration (T§4): CMake configure, active copies, BMS and
component selection, build type, entry points. Runs in a copy of the repo."""
import json
import shutil

import pytest

from conftest import BEV, D, N, PRODUCTS, SITE, UBC, ROOT, run

ACTIVE = ("variants.json", "autoconf.h", "bms.needs.json", "VARIANT")
BMS_FILE = {D: "third_party/bms/empty.needs.json", N: "third_party/bms/0.1.0/nmc.needs.json",
            "bus_bev_lfp_eu": "third_party/bms/0.1.0/lfp.needs.json", "truck_bev_lfp_na": "third_party/bms/0.1.0/lfp.needs.json"}


def configure(repo, product, *extra, env=None):
    return run(["cmake", "-S", ".", "-B", f"build/cmake/{product or 'none'}", "-G", "Ninja",
                *( [f"-DVARIANT={product}"] if product is not None else [] ), *extra], cwd=repo.path, env=env)


@pytest.mark.parametrize("variant, message", [(None, "VARIANT not set"), ("nope", "Unknown VARIANT 'nope'")])
def test_cmk01_missing_or_unknown_variant(repo, variant, message):
    p = configure(repo, variant)
    assert p.returncode != 0 and message in p.out


def test_cmk02_cmk04_active_copies_per_product(repo):
    for p in PRODUCTS:
        assert configure(repo, p).returncode == 0
        active = repo.path / "build/active"
        assert (active / "VARIANT").read_text().strip() == p
        assert json.loads((active / "variants.json").read_text()) == json.loads((repo.path / f"variants/{p}.json").read_text())
        assert (active / "bms.needs.json").read_bytes() == (repo.path / BMS_FILE[p]).read_bytes(), f"BMS selection for {p}"
        header = (active / "autoconf.h").read_text()
        assert ("CONFIG_POWERTRAIN__TYPE__BEV 1" in header) == (p in BEV)


def test_cmk03_broken_defconfig_removes_active_copies(repo):
    assert configure(repo, "bus_bev_lfp_eu").returncode == 0
    repo.append("configs/bus_bev_lfp_eu_defconfig", "CONFIG_CHARGING__MCS=y\n")
    p = configure(repo, "bus_bev_lfp_eu")
    assert p.returncode != 0 and "unmet dependency" in p.out
    assert not any((repo.path / "build/active" / f).exists() for f in ACTIVE)


def test_cmk05_component_selection(repo):
    for p in PRODUCTS:
        assert configure(repo, p).returncode == 0
        files = {e["file"] for e in json.loads((repo.path / f"build/cmake/{p}/compile_commands.json").read_text())}
        has = lambda comp: any(f"/src/{comp}/" in f for f in files)
        assert has("vcu")
        assert has("chg") == (p in BEV), p
        assert has("eng") == (p == D), p
        assert any(f"/tests/{('eng' if p == D else 'chg')}/" in f for f in files), "tests are built (B§6.2.6)"


def test_cmk06_build_type_fixed_and_kit_independent(repo):
    assert configure(repo, N).returncode == 0
    cache = (repo.path / f"build/cmake/{N}/CMakeCache.txt").read_text()
    assert "CMAKE_BUILD_TYPE:STRING=Debug" in cache
    gcc = sorted(p for p in __import__("glob").glob("/opt/homebrew/bin/gcc-[0-9]*")) or [shutil.which("gcc")]
    if not gcc or not gcc[-1]:
        pytest.skip("no second compiler")
    other = run(["cmake", "-S", ".", "-B", "build/cmake/gcc", "-G", "Ninja", f"-DVARIANT={N}"], cwd=repo.path,
                env={"CC": gcc[-1]})
    assert other.returncode == 0, other.out
    assert (repo.path / "build/cmake/gcc/kconfig/variants.json").read_bytes() == \
           (repo.path / f"build/cmake/{N}/kconfig/variants.json").read_bytes()
    exports = {}
    for build in (N, "gcc"):
        run(["cmake", "--build", f"build/cmake/{build}"], cwd=repo.path, check=True)
        shutil.copy(repo.path / f"build/cmake/{build}/compile_commands.json", repo.path / "build/compile_commands.json")
        run([UBC, "build", "needs", "-o", f"build/{build}.json"], cwd=repo.path, check=True)
        d = json.loads((repo.path / f"build/{build}.json").read_text())
        needs = d["versions"][d.get("current_version") or next(iter(d["versions"]))]["needs"]
        exports[build] = {i: {k: v for k, v in n.items() if k not in ("local-url",)} for i, n in needs.items()}
    assert exports[N] == exports["gcc"]


def test_cmk07_defconfig_change_reconfigures(repo):
    assert configure(repo, D).returncode == 0
    run(["cmake", "--build", f"build/cmake/{D}"], cwd=repo.path, check=True)
    repo.edit(f"configs/{D}_defconfig", "CONFIG_MARKET__REGION__EU=y", "CONFIG_MARKET__REGION__NA=y")
    run(["cmake", "--build", f"build/cmake/{D}"], cwd=repo.path, check=True)
    assert json.loads((repo.path / "build/active/variants.json").read_text())["market"]["region"] == "na"


def test_ent01_build_product(repo):
    p = run(["tools/build_product.sh", D], cwd=repo.path)
    assert p.returncode == 0, p.out
    site = repo.path / "build/site" / D
    for f in ("sphinx/index.html", "ubcode/index.html", "ubc.needs.json", "sphinx.needs.json", "junit.xml", "gaps.json"):
        assert (site / f).exists(), f
    assert "parity" in p.out


def test_ent02_build_all_outputs(site):
    for p in PRODUCTS:
        for f in ("sphinx/index.html", "ubcode/index.html", "ubc.needs.json", "sphinx.needs.json", "junit.xml"):
            assert (SITE / p / f).exists(), f"{p}/{f}"
