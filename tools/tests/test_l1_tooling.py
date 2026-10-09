"""L1 — tooling unit tests (T§3): generator, check scripts, importers."""
import json
import shutil
import textwrap
from pathlib import Path

import pytest

from conftest import BEV, D, PRODUCTS, PYTHON, ROOT, SITE, run

GEN = str(ROOT / "tools/kconfig2variants.py")


def gen(tmp_path: Path, kconfig: str, defconfig: str, name: str = "probe"):
    (tmp_path / "Kconfig").write_text(textwrap.dedent(kconfig))
    dc = tmp_path / f"{name}_defconfig"
    dc.write_text(textwrap.dedent(defconfig))
    out = tmp_path / "out"
    p = run([PYTHON, GEN, str(tmp_path / "Kconfig"), str(dc), str(out)])
    data = json.loads((out / "variants.json").read_text()) if p.returncode == 0 else None
    return p, data, out


CHOICE = """
choice VEHICLE__TYPE
    prompt "Vehicle"
    default VEHICLE__TYPE__TRUCK
    help
      Vehicle type.
config VEHICLE__TYPE__TRUCK
    bool "Truck"
config VEHICLE__TYPE__BUS
    bool "Bus"
endchoice
"""


def test_gen01_nesting(tmp_path):
    p, data, _ = gen(tmp_path, 'config A__B__C\n    bool "x"\n    default y\n    help\n      x\n', "")
    assert p.returncode == 0, p.out
    assert data["a"]["b"]["c"] is True


def test_gen02_symbol_without_namespace(tmp_path):
    p, _, _ = gen(tmp_path, 'config PLAIN\n    bool "x"\n    help\n      x\n', "")
    assert p.returncode != 0 and "without namespace" in p.out


def test_gen03_types(tmp_path):
    p, data, _ = gen(tmp_path, """
        config X__FLAG
            bool "f"
            help
              f
        config X__COUNT
            int "c"
            default 3
            help
              c
        config X__MASK
            hex "m"
            default 0x10
            help
              m
        config X__LABEL
            string "l"
            default "2.50"
            help
              l
        """, "CONFIG_X__FLAG=y\n")
    assert p.returncode == 0, p.out
    assert data["x"] == {"flag": True, "count": 3, "mask": 16, "label": "2.50"}


def test_gen04_tristate_rejected(tmp_path):
    p, _, _ = gen(tmp_path, 'config X__T\n    tristate "t"\n    help\n      t\n', "")
    assert p.returncode != 0 and "tristate" in p.out


def test_gen05_named_choice(tmp_path):
    p, data, out = gen(tmp_path, CHOICE, "CONFIG_VEHICLE__TYPE__BUS=y\n")
    assert p.returncode == 0, p.out
    assert data["vehicle"] == {"type": "bus"}
    assert "CONFIG_VEHICLE__TYPE__BUS 1" in (out / "autoconf.h").read_text()


def test_gen06_disabled_symbols_typed_off():
    d = json.loads((ROOT / "variants" / f"{D}.json").read_text())
    assert d["bms"] == {"enabled": False, "chemistry": ""}
    assert d["hv"]["voltage"] == "" and d["charging"]["mcs"] is False


@pytest.mark.parametrize("defconfig, message", [
    ("CONFIG_UNKNOWN__SYMBOL=y\n", "undefined"),
    ("CONFIG_X__N=9\n", "X__N"),
])
def test_gen07_invalid_defconfig(tmp_path, defconfig, message):
    p, _, _ = gen(tmp_path, 'config X__N\n    int "n"\n    range 1 5\n    default 1\n    help\n      n\n', defconfig)
    assert p.returncode != 0 and message in p.out, p.out


def test_gen07_unmet_dependency():
    p = run([PYTHON, GEN, "--all"], cwd=ROOT)  # sanity: the real model is valid
    assert p.returncode == 0, p.out


def test_gen07_dependency_violation(tmp_path):
    kconfig = CHOICE + 'config CHARGING__PANTOGRAPH\n    bool "p"\n    depends on VEHICLE__TYPE__BUS\n    help\n      p\n'
    p, _, _ = gen(tmp_path, kconfig, "CONFIG_VEHICLE__TYPE__TRUCK=y\nCONFIG_CHARGING__PANTOGRAPH=y\n")
    assert p.returncode != 0 and "unmet dependency" in p.out


def test_gen08_idempotent(tmp_path):
    p, _, out = gen(tmp_path, CHOICE, "CONFIG_VEHICLE__TYPE__BUS=y\n")
    first = {f: (f.read_bytes(), f.stat().st_mtime_ns) for f in out.iterdir() if f.name != ".config"}
    run([PYTHON, GEN, str(tmp_path / "Kconfig"), str(tmp_path / "probe_defconfig"), str(out)], check=True)
    for f, (content, mtime) in first.items():
        assert f.read_bytes() == content, f
        assert f.stat().st_mtime_ns == mtime, f"{f.name} rewritten although unchanged"
    data = (out / "variants.json").read_text()
    assert data == json.dumps(json.loads(data), indent=2, sort_keys=True) + "\n"


def test_gen09_meta_product():
    for p in PRODUCTS:
        assert json.loads((ROOT / "variants" / f"{p}.json").read_text())["meta"]["product"] == p


def test_gen10_no_kit_or_build_type_input():
    help_text = run([PYTHON, GEN, "--help"], check=True).out.lower()
    assert "build type" not in help_text and "kit" not in help_text and "debug" not in help_text


def test_gen11_vscode_lists_products():
    variants = json.loads((ROOT / ".vscode/cmake-variants.json").read_text())
    assert set(variants["variant"]["choices"]) == set(PRODUCTS)
    assert "buildType" not in variants
    tasks = json.loads((ROOT / ".vscode/tasks.json").read_text())
    options = next(i["options"] for i in tasks["inputs"] if i["id"] == "product")
    assert set(options) == set(PRODUCTS)


def test_gen12_drift_check_names_file(repo):
    assert repo.tool("tools/kconfig2variants.py", "--all", "--vscode", "--check").returncode == 0
    repo.edit("variants/truck_diesel_eu.json", '"region": "eu"', '"region": "na"')
    p = repo.tool("tools/kconfig2variants.py", "--all", "--vscode", "--check")
    assert p.returncode != 0 and "variants/truck_diesel_eu.json" in p.out


def test_chk01_alternatives_missing(site, tmp_path):
    fake = tmp_path / "site"
    for p in PRODUCTS:
        (fake / p).mkdir(parents=True)
        shutil.copy(SITE / p / "ubc.needs.json", fake / p / "ubc.needs.json")
    assert run([PYTHON, "tools/check_variants.py", "--needs-dir", str(fake)]).returncode == 0
    f = fake / D / "ubc.needs.json"
    d = json.loads(f.read_text())
    d["versions"][d.get("current_version") or next(iter(d["versions"]))]["needs"].pop("REQ_ENERGY_SOURCE")
    f.write_text(json.dumps(d))
    p = run([PYTHON, "tools/check_variants.py", "--needs-dir", str(fake)])
    assert p.returncode != 0 and f"{D}: alternative REQ_ENERGY_SOURCE missing" in p.out


def test_chk02_condition_registry_unknown_key(repo):
    repo.edit("docs/vehicle/requirements.rst", ".. if:: var.vehicle.type == 'bus'", ".. if:: var.vehicle.kind == 'bus'")
    p = repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent")
    assert p.returncode != 0 and "unknown key var.vehicle.kind" in p.out


def test_chk03_bms_pin_mismatch(repo):
    assert repo.tool("tools/pin_bms.py", "--check").returncode == 0
    repo.edit("cmake/bms.cmake", 'set(CV_BMS_VERSION "0.1.0")', 'set(CV_BMS_VERSION "0.2.0")')
    p = repo.tool("tools/pin_bms.py", "--check")
    assert p.returncode != 0 and "0.2.0" in p.out


def test_chk04_skill_mirror(repo):
    assert repo.tool("tools/check_skill_mirrors.py").returncode == 0
    repo.append(".agents/skills/draft-allocation/SKILL.md", "\nlocal change\n")
    p = repo.tool("tools/check_skill_mirrors.py")
    assert p.returncode != 0 and "draft-allocation" in p.out and "differs" in p.out


JUNIT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="(empty)" tests="1" timestamp="2026-10-10T08:00:00">
  <testcase name="test_vcu" classname="test_vcu" time="0.25" status="run">
    <system-out>PASS TEST_VCU_ENERGY_DISPLAY
FAIL TEST_VCU_POWER_LIMIT_APPLY
</system-out>
  </testcase>
</testsuite>
"""


def test_imp01_test_results(site, tmp_path):
    fake = tmp_path / "site" / D
    fake.mkdir(parents=True)
    shutil.copy(SITE / D / "ubc.needs.json", fake / "ubc.needs.json")
    (fake / "junit.xml").write_text(JUNIT)
    out = tmp_path / "test_results.rst"
    p = run([PYTHON, "tools/import_test_results.py", "--site", str(tmp_path / "site"), "--output", str(out)])
    # the diesel product has 4 test needs; 2 without a result are reported
    assert p.returncode != 0 and "test needs without a result" in p.out
    (fake / "junit.xml").write_text(JUNIT.replace("FAIL TEST_VCU_POWER_LIMIT_APPLY\n",
        "FAIL TEST_VCU_POWER_LIMIT_APPLY\nPASS TEST_ENG_FUEL_LEVEL_REPORT\nPASS TEST_ENG_TORQUE_LIMIT\n"))
    p = run([PYTHON, "tools/import_test_results.py", "--site", str(tmp_path / "site"), "--output", str(out)])
    assert p.returncode == 0, p.out
    text = out.read_text()
    assert f".. if:: var.meta.product == '{D}'" in text
    assert ":id: TRES_VCU_ENERGY_DISPLAY__TRUCK_DIESEL_EU" in text and ":outcome: passed" in text
    assert ":outcome: failed" in text and f":product: {D}" in text
    assert ":chain_reqs: REQ_ENERGY_SOURCE, REQ_RANGE_ESTIMATE" in text
    assert ":test_run_label: 2026-10-10 08:00:00" in text


def test_imp02_gaps(tmp_path):
    fake = tmp_path / "site" / BEV[0]
    fake.mkdir(parents=True)
    (fake / "gaps.json").write_text(json.dumps({"gaps": [
        {"id": "REQ_X", "type": "req", "link": "satisfies", "have": 0, "need": 1, "category": "trace_backward"},
        {"id": "BMS_REQ_Y", "type": "req", "link": "review", "have": 0, "need": 1, "category": "review"},
    ]}))
    out = tmp_path / "gaps.rst"
    run([PYTHON, "tools/import_gaps.py", "--site", str(tmp_path / "site"), "--output", str(out)], check=True)
    text = out.read_text()
    assert ":id: GAP_REQ_X_SATISFIES__TRUCK_BEV_NMC_EU" in text and ":gap_for: REQ_X" in text
    assert ":gap_shortfall: 0 of 1" in text and f":product: {BEV[0]}" in text
    assert "BMS_REQ_Y" not in text
