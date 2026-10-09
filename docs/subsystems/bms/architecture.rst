BMS black box
=============

Black-box elements of the BMS as seen by the CV platform (``bms_block``,
prefix ``BB_``). Each satisfies a vehicle requirement and allocates BMS
interface needs (``BMS_REQ_*``). Workflow stage ``bms_allocation``. The whole
folder exists only in battery-electric products; BMS values are referenced
through the allocated needs, never copied.

.. bms_block:: Battery energy state
   :id: BB_ENERGY_STATE
   :status: draft
   :satisfies: REQ_ENERGY_SOURCE
   :allocates: BMS_REQ_SOC_ACCURACY, BMS_REQ_SOC_INVALID_FLAG

   The BMS provides the state of charge shown to the driver, with its accuracy
   and a flag when the value is unreliable.

.. bms_block:: Battery power limits
   :id: BB_POWER_LIMITS
   :status: draft
   :satisfies: REQ_TRACTION_POWER_LIMIT
   :allocates: BMS_REQ_POWER_DERATING, BMS_REQ_PACK_OVERCURRENT

   The BMS publishes the permitted discharge power that the VCU applies as a
   traction power limit, and protects the pack against overcurrent as the last
   line of defence.

.. bms_block:: Battery isolation protection
   :id: BB_HV_PROTECTION
   :status: draft
   :satisfies: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT
   :allocates: BMS_REQ_ISOLATION_FAULT, BMS_REQ_FAULT_REACTION_TIME

   The BMS detects the isolation fault that triggers the high-voltage shutdown
   and opens the main contactors on request of the VCU. Open point for the BMS
   team: no BMS requirement bounds the isolation-fault reaction time yet.

.. bms_block:: Battery charging limits
   :id: BB_CHARGE_LIMITS
   :status: draft
   :satisfies: REQ_MAX_CHARGE_POWER
   :allocates: BMS_REQ_CELL_VOLTAGE_LIMITS, BMS_REQ_HEATING_REQUEST, BMS_REQ_COOLING_REQUEST

   The BMS keeps every cell inside the voltage window of its chemistry and
   requests heating or cooling, so that charging power is accepted only within
   safe cell limits. Open point for the BMS team: no BMS interface requirement
   publishes a permitted charging power yet.
