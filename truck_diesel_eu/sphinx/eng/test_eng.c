/* Unit tests of the Engine Interface (ENG). Each case prints
   "PASS <TEST id>" or "FAIL <TEST id>" (read by tools/import_test_results.py). */
#include <stdio.h>
#include "eng/eng.h"

static int failures;

static void report(const char *test_id, int ok)
{
    printf("%s %s\n", ok ? "PASS" : "FAIL", test_id);
    failures += !ok;
}

// @need: Fuel level is the averaged sensor value, TEST_ENG_FUEL_LEVEL_REPORT, [SWREQ_ENG_FUEL_LEVEL_REPORT]
static void test_fuel_level(void)
{
    const int samples[4] = {500, 520, 480, 500}; /* slosh around 500 of 1000 */
    report("TEST_ENG_FUEL_LEVEL_REPORT", eng_fuel_level_percent(samples, 4, 1000) == 50);
}

// @need: Engine torque limit follows the power limit, TEST_ENG_TORQUE_LIMIT, [SWREQ_ENG_TORQUE_LIMIT]
static void test_torque_limit(void)
{
    report("TEST_ENG_TORQUE_LIMIT", eng_torque_limit_nm(450, 1800) == 2387 && eng_torque_limit_nm(450, 1000) == 2600);
}

int main(void)
{
    test_fuel_level();
    test_torque_limit();
    return failures ? 1 : 0;
}
