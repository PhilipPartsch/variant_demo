/* Megawatt Charging System session (MCS products only). */
#include "autoconf.h"
#include "chg/chg.h"

#if CONFIG_CHARGING__MCS
// @need: Close contactors after MCS setup, IMPL_CHG_MCS_HANDSHAKE, [SWREQ_CHG_MCS_HANDSHAKE]
int chg_mcs_contactors_may_close(int session_setup_complete)
{
    return session_setup_complete ? 1 : 0;
}
#endif
