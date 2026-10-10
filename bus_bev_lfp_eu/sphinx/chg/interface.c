/* Charging interface protection (MCS inlet, pantograph or CCS inlet). */
#include "autoconf.h"
#include "chg/chg.h"

#define CHG_CONTACT_TEMP_LIMIT_C 90

// @need: Halve current on hot contacts, IMPL_CHG_INTERFACE_DERATING, [SWREQ_CHG_INTERFACE_DERATING]
int chg_derated_current_a(int current_a, int contact_temp_c)
{
    return contact_temp_c > CHG_CONTACT_TEMP_LIMIT_C ? current_a / 2 : current_a;
}
