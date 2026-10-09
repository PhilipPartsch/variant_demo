/* Vehicle Control Unit (VCU): public interface. */
#ifndef VCU_VCU_H
#define VCU_VCU_H

#include "autoconf.h"

/** Initialise the Vehicle Control Unit. Returns 0 on success. */
int vcu_init(void);

#if CONFIG_POWERTRAIN__TYPE__BEV
/** Remaining energy in percent (rounded) from the BMS state of charge in
    permille; -1 while the BMS flags the state of charge as unreliable. */
int vcu_energy_percent(int soc_permille, int soc_invalid);
#else
/** Remaining energy in percent (rounded) from the fuel level and the tank
    capacity, both in decilitres. */
int vcu_energy_percent(int fuel_dl, int tank_dl);
#endif

/** Torque limit in Nm for the active power limit (kW) at the motor speed
    (rpm); battery-electric products also respect the BMS discharge power. */
int vcu_torque_limit_nm(int vehicle_limit_kw, int bms_limit_kw, int motor_rpm);

#if CONFIG_POWERTRAIN__TYPE__BEV
/** 1 when the contactor-open request has to be sent to the BMS. */
int vcu_contactor_open_request(int isolation_fault);
#endif

#if CONFIG_VEHICLE__TYPE__BUS
/** Torque request after the door interlock. */
int vcu_door_interlock_torque(int torque_request_nm, int all_doors_closed_locked);
#endif

#endif /* VCU_VCU_H */
