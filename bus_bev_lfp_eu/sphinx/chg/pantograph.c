/* Roof pantograph sequence (pantograph products without MCS). */
#include "autoconf.h"
#include "chg/chg.h"

#if CONFIG_CHARGING__PANTOGRAPH && !CONFIG_CHARGING__MCS
// @need: Raise pantograph at standstill only, IMPL_CHG_PANTOGRAPH_SEQUENCE, [SWREQ_CHG_PANTOGRAPH_SEQUENCE]
int chg_pantograph_may_raise(int standstill, int parking_brake_applied)
{
    return standstill && parking_brake_applied;
}
#endif
