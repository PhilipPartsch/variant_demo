"""Expected content per product (T§2 oracle), from the C§ tables as built
(see 04-content-result.md §1). D / N / B / A = diesel EU / BEV NMC MCS EU /
bus BEV LFP pantograph EU / BEV LFP NA."""
from conftest import A, B, BEV, D, N, PRODUCTS

ALL = set(PRODUCTS)
BEVS = set(BEV)

PRESENT = {
    # user stories
    "US_RANGE_AWARENESS": ALL, "US_PREDICTABLE_POWER": ALL, "US_FAST_DEPOT_CHARGING": BEVS,
    "US_HV_SAFETY": BEVS, "US_MARKET_CHARGING": BEVS, "US_OPPORTUNITY_CHARGING": {B},
    "US_PASSENGER_DOOR_SAFETY": {B},
    # vehicle requirements
    "REQ_ENERGY_SOURCE": ALL, "REQ_RANGE_ESTIMATE": ALL, "REQ_TRACTION_POWER_LIMIT": ALL,
    "REQ_MAX_CHARGE_POWER": BEVS, "REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT": BEVS, "REQ_MCS_CHARGING": {N},
    "REQ_PANTOGRAPH_CHARGING": {B}, "REQ_DOOR_DRIVE_INTERLOCK": {B},
    "REQ_EU_CHARGING_STANDARD": {N, B}, "REQ_NA_CHARGING_STANDARD": {A},
    # architecture and black boxes
    "ARCH_VCU_ENERGY_DISPLAY": ALL, "ARCH_VCU_POWER_MGMT": ALL, "ARCH_VCU_HV_SHUTDOWN": BEVS,
    "ARCH_VCU_DOOR_INTERLOCK": {B}, "ARCH_CHG_INLET": BEVS, "ARCH_CHG_SESSION_CONTROL": BEVS,
    "ARCH_ENG_FUEL_LEVEL": {D}, "ARCH_ENG_TORQUE_INTERFACE": {D},
    "BB_ENERGY_STATE": BEVS, "BB_POWER_LIMITS": BEVS, "BB_HV_PROTECTION": BEVS, "BB_CHARGE_LIMITS": BEVS,
    # risks and decisions
    "RISK_HV_EXPOSURE": BEVS, "RISK_DOOR_TRAP": {B},
    "DEC_BMS_AS_EXTERNAL_PRODUCT": BEVS, "DEC_CHARGING_INLET_PRIORITY": BEVS,
}
# software requirements, each with IMPL_ and TEST_ of the same suffix (one impl, one test)
SW = {
    "VCU_ENERGY_DISPLAY": ALL, "VCU_POWER_LIMIT_APPLY": ALL, "VCU_HV_SHUTDOWN": BEVS,
    "VCU_DOOR_INTERLOCK": {B}, "CHG_SESSION_START": BEVS, "CHG_CURRENT_LIMIT": BEVS,
    "CHG_INTERFACE_DERATING": BEVS, "CHG_MCS_HANDSHAKE": {N}, "CHG_PANTOGRAPH_SEQUENCE": {B},
    "ENG_FUEL_LEVEL_REPORT": {D}, "ENG_TORQUE_LIMIT": {D},
}
for suffix, where in SW.items():
    for prefix in ("SWREQ_", "IMPL_", "TEST_"):
        PRESENT[prefix + suffix] = where

VALUE = {
    "REQ_TRACTION_POWER_LIMIT": {D: "450 kW", N: "450 kW", B: "250 kW", A: "450 kW"},
    "REQ_MAX_CHARGE_POWER": {N: "1000 kW", B: "350 kW", A: "350 kW"},
}
POWER_DERATING = ["BMS_REQ_POWER_DERATING"]
ALLOCATES = {"ARCH_VCU_POWER_MGMT": {D: [], N: POWER_DERATING, B: POWER_DERATING, A: POWER_DERATING}}
# alternatives with one id: a phrase only the active branch contains
ALTERNATIVE = {
    "REQ_ENERGY_SOURCE": {D: "fuel tank level", N: "state of charge", B: "state of charge", A: "state of charge"},
    "ARCH_CHG_INLET": {N: "MCS vehicle inlet", B: "roof pantograph", A: "no additional high-power interface"},
    "ARCH_CHG_SESSION_CONTROL": {N: "CCS2", B: "CCS2", A: "CCS1"},
}
ENERGY_IMPL_TITLE = {D: "Show remaining energy (fuel level)", N: "Show remaining energy (state of charge)",
                     B: "Show remaining energy (state of charge)", A: "Show remaining energy (state of charge)"}
# file variants: html pages present per product (both toolchains)
PAGES = {
    "subsystems/chg/architecture.html": BEVS, "subsystems/bms/integration.html": BEVS,
    "subsystems/eng/architecture.html": {D}, "region/eu/annex.html": {D, N, B}, "region/na/annex.html": {A},
    "subsystems/vcu/architecture.html": ALL,
}
BMS_CHEMISTRY = {N: "NMC", B: "LFP", A: "LFP"}
