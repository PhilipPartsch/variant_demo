"""L5 — negative / mutation tests (T§7): each check must fail on the defect
it exists for. Every test injects one defect into a copy of the repository."""
import pytest

from conftest import B, D, N, UBC, load_needs, run
from system_model import covers_mismatch, system_tree

BEV_ONLY_REQ = "REQ_MAX_CHARGE_POWER"


def fails_with(p, *needles):
    assert p.returncode != 0, p.out[-2000:]
    for n in needles:
        assert n in p.out, f"{n!r} not in output:\n{p.out[-2000:]}"


def test_neg01_ungated_link_to_bev_only_need(repo):
    repo.edit("docs/subsystems/vcu/architecture.rst",
              "   :satisfies: REQ_TRACTION_POWER_LIMIT\n", f"   :satisfies: REQ_TRACTION_POWER_LIMIT, {BEV_ONLY_REQ}\n")
    repo.configure(D)
    fails_with(repo.sphinx(), BEV_ONLY_REQ)
    fails_with(repo.ubc_check(), f"unknown link target '{BEV_ONLY_REQ}'")


def test_neg02_variant_sources_unknown_key(repo):
    repo.append("ubproject.toml", '\n[[source.variant_sources]]\nif = "var.foo.bar == 1"\nfiles = ["reports/**"]\n')
    repo.configure(D)
    fails_with(repo.sphinx(), "foo")
    fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"), "unknown key var.foo.bar")


def test_neg03_condition_key_not_in_variant_data(repo):
    repo.edit("docs/vehicle/requirements.rst", ".. if:: var.charging.mcs == True", ".. if:: var.charging.mcs_fast == True")
    fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"), "unknown key var.charging.mcs_fast")


def test_neg04_dead_kconfig_symbol(repo):
    repo.append("src/vcu/Kconfig", 'config VCU__UNUSED\n    bool "unused"\n    help\n      Never used.\n')
    fails_with(repo.tool("tools/check_kconfig.py"), "VCU__UNUSED: used nowhere")


def test_neg05_condition_true_in_every_product(repo):
    repo.edit("docs/vehicle/requirements.rst", ".. if:: var.vehicle.type == 'bus'", ".. if:: var.meta.product != ''")
    fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"), "no branch coverage")


@pytest.mark.parametrize("defect, needle", [
    ('config BUILD__DEBUG\n    bool "debug"\n    help\n      Debug build.\n', "BUILD__DEBUG: build settings"),
    (None, "build settings are not variant data: var.build.type"),
])
def test_neg06_build_configuration_in_variant_model(repo, defect, needle):
    if defect:
        repo.append("src/vcu/Kconfig", defect)
        fails_with(repo.tool("tools/check_kconfig.py"), needle)
    else:
        repo.edit("docs/vehicle/requirements.rst", ".. if:: var.vehicle.type == 'bus'", ".. if:: var.build.type == 'debug'")
        fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"), needle)


@pytest.mark.parametrize("defect, tool, needle", [
    ('config VCU__NO_HELP\n    bool "no help"\n', "tools/check_kconfig.py", "VCU__NO_HELP: no help text"),
    ('config VCU__TRI\n    tristate "tri"\n    help\n      t\n', "tools/check_kconfig.py", "VCU__TRI: tristate"),
    ('config NOPREFIX\n    bool "x"\n    help\n      x\n', "tools/check_kconfig.py", "NOPREFIX: no namespace"),
])
def test_neg07_kconfig_hygiene(repo, defect, tool, needle):
    repo.append("src/vcu/Kconfig", defect)
    fails_with(repo.tool(tool), needle)


def test_neg08_hand_edited_generated_file(repo):
    repo.edit(".vscode/cmake-variants.json", '"default": "truck_bev_nmc_eu"', '"default": "truck_diesel_eu"')
    fails_with(repo.tool("tools/kconfig2variants.py", "--all", "--vscode", "--check"), ".vscode/cmake-variants.json")


def test_neg09_overlapping_alternative_conditions(repo):
    # with choose, overlapping conditions are allowed: the first true branch wins, no duplicate id
    repo.edit("docs/vehicle/requirements.rst", "   .. otherwise::", "   .. when:: var.vehicle.type == 'truck'")
    repo.configure(N)  # truck and battery-electric: both conditions true
    assert repo.ubc_check().returncode == 0
    assert repo.sphinx().returncode == 0
    content = ubc_needs(repo)["REQ_ENERGY_SOURCE"]["content"]
    assert "state of charge" in content and "fuel tank" not in content


def test_neg10_gap_in_alternative_conditions(repo):
    repo.edit("docs/vehicle/requirements.rst", "   .. otherwise::", "   .. when:: var.powertrain.type == 'hydrogen'")
    fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"),
               "branch when \"var.powertrain.type == 'hydrogen'\" is the first true branch in no product")
    repo.configure(D)  # no branch is taken: the id is missing
    fails_with(repo.ubc_check(), "REQ_ENERGY_SOURCE")


def test_neg11_allocation_to_non_interface_need(repo):
    repo.edit("docs/subsystems/bms/architecture.rst", ":allocates: BMS_REQ_POWER_DERATING, BMS_REQ_PACK_OVERCURRENT",
              ":allocates: BMS_REQ_POWER_DERATING, BMS_REQ_CELL_OVERTEMPERATURE")
    repo.configure(N)
    fails_with(repo.ubc_check(), "alloc-target-interface")
    fails_with(repo.sphinx(), "alloc-target-interface")


def test_neg12_bms_pin_without_allocated_id(repo):
    import json
    f = repo.file("third_party/bms/0.1.0/nmc.needs.json")
    d = json.loads(f.read_text())
    d["versions"]["0.1.0"]["needs"].pop("REQ_POWER_DERATING")
    f.write_text(json.dumps(d))
    repo.configure(N)
    fails_with(repo.ubc_check(), "BMS_REQ_POWER_DERATING")
    fails_with(repo.tool("tools/pin_bms.py", "--check"), "REQ_POWER_DERATING")


def test_neg13_missing_variant_data(repo):
    repo.edit("ubproject.toml", 'variant_data_file = "build/active/variants.json"\n', "")
    repo.configure(N)
    fails_with(repo.ubc_check(), "no variant data")


def test_neg14_bare_boolean_condition(repo):
    repo.edit("ubproject.toml", "if = \"var.market.region == 'na'\"", 'if = "var.charging.mcs"')
    fails_with(repo.tool("tools/check_variants.py", "--needs-dir", "/nonexistent"), "bare boolean var.charging.mcs")
    repo.configure(D)
    assert repo.sphinx().returncode != 0  # sphinx-mounts aborts (plan 99 SM-01)


def test_neg15_marker_gated_weaker_than_its_requirement(repo):
    # the MCS marker outside its #if: the code need exists where its swreq does not
    repo.edit("src/chg/mcs.c", "#if CONFIG_CHARGING__MCS\n// @need", "// @need")
    repo.edit("src/chg/mcs.c", "    return session_setup_complete ? 1 : 0;\n}\n#endif", "    return session_setup_complete ? 1 : 0;\n}\n#if 0\n#endif")
    repo.edit("src/chg/include/chg/chg.h", "#if CONFIG_CHARGING__MCS\n/** 1 when the charging", "#if 1\n/** 1 when the charging")
    repo.configure(B)
    fails_with(repo.ubc_check(), "SWREQ_CHG_MCS_HANDSHAKE")


def test_neg16_same_id_without_if_else(repo):
    repo.edit("src/vcu/energy_display.c", "#if CONFIG_POWERTRAIN__TYPE__BEV\n", "")
    repo.edit("src/vcu/energy_display.c", "#else\n", "")
    repo.edit("src/vcu/energy_display.c", "#endif\n", "")
    repo.edit("src/vcu/energy_display.c", "int vcu_energy_percent(int fuel_dl, int tank_dl)", "int vcu_energy_percent_fuel(int fuel_dl, int tank_dl)")
    repo.configure(N)
    fails_with(repo.ubc_check(), "IMPL_VCU_ENERGY_DISPLAY")
    # Sphinx-Codelinks 2.0.0 warns with the marker's file and line (aborted in 1.4.0, plan 99 CL-06)
    fails_with(repo.sphinx(), "energy_display.c", "codelinks.duplicate_need")


def ubc_needs(repo):
    run([UBC, "build", "needs", "-o", "build/n.json"], cwd=repo.path, check=True)
    return {i: n for i, n in load_needs(repo.path / "build/n.json").items() if not i.startswith("BMS_")}


def test_neg17_arch_without_subsystem(repo):
    repo.edit("docs/subsystems/vcu/architecture.rst", "   :part_of: SUB_VCU\n", "")
    repo.configure(D)
    fails_with(repo.ubc_check(), "trace-arch-part_of")
    fails_with(repo.sphinx(), "trace-arch-part_of")


def test_neg18_arch_part_of_the_system(repo):
    repo.edit("docs/subsystems/vcu/architecture.rst", "   :part_of: SUB_VCU\n", "   :part_of: SYS_VEHICLE\n")
    repo.configure(D)
    fails_with(repo.ubc_check(), "trace-arch-part_of")
    fails_with(repo.sphinx(), "trace-arch-part_of")


def test_neg19_subsystem_covers_what_no_part_satisfies(repo):
    repo.edit("docs/system/overview.rst", ":covers: REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT\n",
              ":covers: REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT, REQ_RANGE_ESTIMATE\n")
    repo.configure(D)
    assert any("SUB_ENG covers ['REQ_RANGE_ESTIMATE']" in p for p in covers_mismatch(ubc_needs(repo)))


def test_neg20_part_satisfies_what_its_subsystem_does_not_cover(repo):
    repo.edit("docs/system/overview.rst", ":covers: REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT\n",
              ":covers: REQ_ENERGY_SOURCE\n")
    repo.configure(D)
    assert any("SUB_ENG does not cover ['REQ_TRACTION_POWER_LIMIT']" in p for p in covers_mismatch(ubc_needs(repo)))


def test_neg21_second_system(repo):
    repo.append("docs/system/overview.rst", "\n.. system:: Trailer\n   :id: SYS_TRAILER\n   :status: draft\n\n   A second system.\n")
    repo.configure(D)
    assert any("exactly one system" in p for p in system_tree(ubc_needs(repo)))


def test_neg22_subsystem_gated_wrongly(repo):
    # SUB_ENG without its gate: present in BEV products, where its folder is excluded
    repo.edit("docs/system/overview.rst", ".. if:: var.powertrain.type == 'diesel'\n", ".. if:: True\n")
    repo.configure(N)
    fails_with(repo.ubc_check(), "SUB_ENG")


@pytest.mark.parametrize("product", (D, N))
def test_neg00_control_unchanged_copy_is_clean(repo, product):
    """Without a defect the copy builds cleanly — so every NEG failure above is
    caused by its defect, not by the copy."""
    repo.configure(product)
    p = repo.ubc_check()
    assert p.returncode == 0, p.out[-2000:]
    p = repo.sphinx()
    assert p.returncode == 0, p.out[-2000:]
    html = (repo.path / "build/sphinx/subsystems/vcu/code_trace.html").read_text()
    assert "IMPL_VCU_ENERGY_DISPLAY" in html and "IMPL_VCU_POWER_LIMIT_APPLY" in html
    for tool in (["tools/check_variants.py", "--needs-dir", "/nonexistent"], ["tools/check_kconfig.py"],
                 ["tools/kconfig2variants.py", "--all", "--vscode", "--check"], ["tools/pin_bms.py", "--check"]):
        assert repo.tool(*tool).returncode == 0, tool
