/* Charging Controller (CHG): public interface. Built for battery-electric
   products only. */
#ifndef CHG_CHG_H
#define CHG_CHG_H

#include "autoconf.h"

/** Initialise the Charging Controller. Returns 0 on success. */
int chg_init(void);

/** 1 when a charging session may start. */
int chg_session_may_start(int inlet_locked);

/** Maximum charging current in A for the maximum charging power in kW at the
    nominal pack voltage of the product. */
int chg_current_limit_a(int max_power_kw);

/** Requested charging current after derating on hot contacts. */
int chg_derated_current_a(int current_a, int contact_temp_c);

#if CONFIG_CHARGING__MCS
/** 1 when the charging contactors may close. */
int chg_mcs_contactors_may_close(int session_setup_complete);
#endif

#if CONFIG_CHARGING__PANTOGRAPH && !CONFIG_CHARGING__MCS
/** 1 when the pantograph may be raised. */
int chg_pantograph_may_raise(int standstill, int parking_brake_applied);
#endif

#endif /* CHG_CHG_H */
