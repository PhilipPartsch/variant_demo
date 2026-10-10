/* Traction power limit as a torque limit. */
#include "autoconf.h"
#include "vcu/vcu.h"

#define VCU_MAX_TORQUE_NM 3000

// @need: Apply traction power limit, IMPL_VCU_POWER_LIMIT_APPLY, [SWREQ_VCU_POWER_LIMIT_APPLY]
int vcu_torque_limit_nm(int vehicle_limit_kw, int bms_limit_kw, int motor_rpm)
{
    int limit_kw = vehicle_limit_kw;
#if CONFIG_POWERTRAIN__TYPE__BEV
    if (bms_limit_kw < limit_kw) {
        limit_kw = bms_limit_kw;
    }
#else
    (void)bms_limit_kw;
#endif
    if (motor_rpm <= 0) {
        return VCU_MAX_TORQUE_NM;
    }
    int torque = limit_kw * 9549 / motor_rpm; /* P[kW] * 9549 / n[rpm] = M[Nm] */
    return torque < VCU_MAX_TORQUE_NM ? torque : VCU_MAX_TORQUE_NM;
}
