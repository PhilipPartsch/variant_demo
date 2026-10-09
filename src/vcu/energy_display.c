/* Remaining energy for the instrument cluster. One need id, two
   implementations: the active product's compile database decides which marker
   becomes IMPL_VCU_ENERGY_DISPLAY. */
#include "autoconf.h"
#include "vcu/vcu.h"

#if CONFIG_POWERTRAIN__TYPE__BEV
// @need: Show remaining energy (state of charge), IMPL_VCU_ENERGY_DISPLAY, [SWREQ_VCU_ENERGY_DISPLAY]
int vcu_energy_percent(int soc_permille, int soc_invalid)
{
    if (soc_invalid) {
        return -1;
    }
    return (soc_permille + 5) / 10;
}
#else
// @need: Show remaining energy (fuel level), IMPL_VCU_ENERGY_DISPLAY, [SWREQ_VCU_ENERGY_DISPLAY]
int vcu_energy_percent(int fuel_dl, int tank_dl)
{
    if (tank_dl <= 0) {
        return 0;
    }
    return (fuel_dl * 100 + tank_dl / 2) / tank_dl;
}
#endif
