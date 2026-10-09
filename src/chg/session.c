/* CCS charging session control. */
#include "autoconf.h"
#include "chg/chg.h"

#if CONFIG_HV__VOLTAGE__V800
#define CHG_NOMINAL_PACK_V 800
#else
#define CHG_NOMINAL_PACK_V 400
#endif

// @need: Start session only with locked inlet, IMPL_CHG_SESSION_START, [SWREQ_CHG_SESSION_START]
int chg_session_may_start(int inlet_locked)
{
    return inlet_locked ? 1 : 0;
}

// @need: Charging current from power and pack voltage, IMPL_CHG_CURRENT_LIMIT, [SWREQ_CHG_CURRENT_LIMIT]
int chg_current_limit_a(int max_power_kw)
{
    return max_power_kw * 1000 / CHG_NOMINAL_PACK_V;
}
