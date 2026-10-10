/* Torque limit for the engine control unit (sent as SAE J1939 TSC1). */
#include "eng/eng.h"

#define ENG_MAX_TORQUE_NM 2600

// @need: Torque limit from the traction power limit, IMPL_ENG_TORQUE_LIMIT, [SWREQ_ENG_TORQUE_LIMIT]
int eng_torque_limit_nm(int power_limit_kw, int engine_rpm)
{
    if (engine_rpm <= 0) {
        return ENG_MAX_TORQUE_NM;
    }
    int torque = power_limit_kw * 9549 / engine_rpm;
    return torque < ENG_MAX_TORQUE_NM ? torque : ENG_MAX_TORQUE_NM;
}
