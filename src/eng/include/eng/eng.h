/* Engine Interface (ENG): public interface. Built for diesel products only. */
#ifndef ENG_ENG_H
#define ENG_ENG_H

/** Initialise the Engine Interface. Returns 0 on success. */
int eng_init(void);

/** Fuel level in percent (rounded) as the average of n raw tank sensor
    samples (10 s at 100 ms), relative to the raw value of a full tank. */
int eng_fuel_level_percent(const int *samples, int n, int raw_full);

/** Torque limit in Nm for the traction power limit (kW) at the engine speed. */
int eng_torque_limit_nm(int power_limit_kw, int engine_rpm);

#endif /* ENG_ENG_H */
