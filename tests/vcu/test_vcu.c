/* Unit tests of the Vehicle Control Unit (VCU). Each case prints
   "PASS <TEST id>" or "FAIL <TEST id>" (read by tools/import_test_results.py). */
#include <stdio.h>
#include "autoconf.h"
#include "vcu/vcu.h"

static int failures;

static void report(const char *test_id, int ok)
{
    printf("%s %s\n", ok ? "PASS" : "FAIL", test_id);
    failures += !ok;
}

// @need: Remaining energy is rounded to percent, TEST_VCU_ENERGY_DISPLAY, [SWREQ_VCU_ENERGY_DISPLAY]
static void test_energy_display(void)
{
#if CONFIG_POWERTRAIN__TYPE__BEV
    report("TEST_VCU_ENERGY_DISPLAY", vcu_energy_percent(805, 0) == 81 && vcu_energy_percent(500, 1) == -1);
#else
    report("TEST_VCU_ENERGY_DISPLAY", vcu_energy_percent(1215, 4000) == 30 && vcu_energy_percent(0, 4000) == 0);
#endif
}

// @need: Torque is limited by the power limit, TEST_VCU_POWER_LIMIT_APPLY, [SWREQ_VCU_POWER_LIMIT_APPLY]
static void test_power_limit(void)
{
#if CONFIG_POWERTRAIN__TYPE__BEV
    int ok = vcu_torque_limit_nm(450, 200, 1000) == 1909; /* BMS limit is lower */
#else
    int ok = vcu_torque_limit_nm(250, 0, 1000) == 2387     /* 250 kW at 1000 rpm */
          && vcu_torque_limit_nm(450, 0, 1000) == 3000;    /* capped at the maximum torque */
#endif
    report("TEST_VCU_POWER_LIMIT_APPLY", ok);
}

#if CONFIG_POWERTRAIN__TYPE__BEV
// @need: Isolation fault requests contactor opening, TEST_VCU_HV_SHUTDOWN, [SWREQ_VCU_HV_SHUTDOWN]
static void test_hv_shutdown(void)
{
    report("TEST_VCU_HV_SHUTDOWN", vcu_contactor_open_request(1) == 1 && vcu_contactor_open_request(0) == 0);
}
#endif

#if CONFIG_VEHICLE__TYPE__BUS
// @need: Open door sets torque to zero, TEST_VCU_DOOR_INTERLOCK, [SWREQ_VCU_DOOR_INTERLOCK]
static void test_door_interlock(void)
{
    report("TEST_VCU_DOOR_INTERLOCK", vcu_door_interlock_torque(800, 0) == 0 && vcu_door_interlock_torque(800, 1) == 800);
}
#endif

int main(void)
{
    test_energy_display();
    test_power_limit();
#if CONFIG_POWERTRAIN__TYPE__BEV
    test_hv_shutdown();
#endif
#if CONFIG_VEHICLE__TYPE__BUS
    test_door_interlock();
#endif
    return failures ? 1 : 0;
}
