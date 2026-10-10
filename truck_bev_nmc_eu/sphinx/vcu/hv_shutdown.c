/* High-voltage shutdown on isolation fault (battery-electric only). */
#include "autoconf.h"
#include "vcu/vcu.h"

#if CONFIG_POWERTRAIN__TYPE__BEV
// @need: Request contactor opening on isolation fault, IMPL_VCU_HV_SHUTDOWN, [SWREQ_VCU_HV_SHUTDOWN]
int vcu_contactor_open_request(int isolation_fault)
{
    return isolation_fault ? 1 : 0;
}
#endif
