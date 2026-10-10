/* Unit tests of the Charging Controller (CHG). Each case prints
   "PASS <TEST id>" or "FAIL <TEST id>" (read by tools/import_test_results.py). */
#include <stdio.h>
#include "autoconf.h"
#include "chg/chg.h"

static int failures;

static void report(const char *test_id, int ok)
{
    printf("%s %s\n", ok ? "PASS" : "FAIL", test_id);
    failures += !ok;
}

// @need: Session starts only with locked inlet, TEST_CHG_SESSION_START, [SWREQ_CHG_SESSION_START]
static void test_session_start(void)
{
    report("TEST_CHG_SESSION_START", chg_session_may_start(1) == 1 && chg_session_may_start(0) == 0);
}

// @need: Charging current follows the pack voltage, TEST_CHG_CURRENT_LIMIT, [SWREQ_CHG_CURRENT_LIMIT]
static void test_current_limit(void)
{
#if CONFIG_HV__VOLTAGE__V800
    report("TEST_CHG_CURRENT_LIMIT", chg_current_limit_a(1000) == 1250);
#else
    report("TEST_CHG_CURRENT_LIMIT", chg_current_limit_a(350) == 875);
#endif
}

// @need: Hot contacts halve the current, TEST_CHG_INTERFACE_DERATING, [SWREQ_CHG_INTERFACE_DERATING]
static void test_interface_derating(void)
{
    report("TEST_CHG_INTERFACE_DERATING", chg_derated_current_a(500, 91) == 250 && chg_derated_current_a(500, 90) == 500);
}

#if CONFIG_CHARGING__MCS
// @need: Contactors wait for MCS setup, TEST_CHG_MCS_HANDSHAKE, [SWREQ_CHG_MCS_HANDSHAKE]
static void test_mcs_handshake(void)
{
    report("TEST_CHG_MCS_HANDSHAKE", chg_mcs_contactors_may_close(0) == 0 && chg_mcs_contactors_may_close(1) == 1);
}
#endif

#if CONFIG_CHARGING__PANTOGRAPH && !CONFIG_CHARGING__MCS
// @need: Pantograph rises only at standstill, TEST_CHG_PANTOGRAPH_SEQUENCE, [SWREQ_CHG_PANTOGRAPH_SEQUENCE]
static void test_pantograph_sequence(void)
{
    report("TEST_CHG_PANTOGRAPH_SEQUENCE", chg_pantograph_may_raise(1, 1) == 1 && chg_pantograph_may_raise(0, 1) == 0
                                           && chg_pantograph_may_raise(1, 0) == 0);
}
#endif

int main(void)
{
    test_session_start();
    test_current_limit();
    test_interface_derating();
#if CONFIG_CHARGING__MCS
    test_mcs_handshake();
#endif
#if CONFIG_CHARGING__PANTOGRAPH && !CONFIG_CHARGING__MCS
    test_pantograph_sequence();
#endif
    return failures ? 1 : 0;
}
