/* Door and drive interlock (bus only). */
#include "autoconf.h"
#include "vcu/vcu.h"

#if CONFIG_VEHICLE__TYPE__BUS
// @need: Zero torque with open door, IMPL_VCU_DOOR_INTERLOCK, [SWREQ_VCU_DOOR_INTERLOCK]
int vcu_door_interlock_torque(int torque_request_nm, int all_doors_closed_locked)
{
    return all_doors_closed_locked ? torque_request_nm : 0;
}
#endif
