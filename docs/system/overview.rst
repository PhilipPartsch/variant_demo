System overview
===============

The system architecture of the CV platform: the vehicle as **system**
(``system``) and its **subsystems** (``subsystem``). The vehicle level is the
system level: the user stories and vehicle requirements are the stakeholder and
system requirements of the vehicle. Each subsystem covers the vehicle
requirements allocated to it; its architecture elements are ``part_of`` it.
Workflow stage ``subsystems``.

.. system:: Commercial vehicle
   :id: SYS_VEHICLE
   :status: draft

   The commercial vehicle of this product (:variant:`meta.product`): vehicle
   :variant:`vehicle.type`, powertrain :variant:`powertrain.type`, market
   :variant:`market.region`. Which subsystems it contains depends on its
   powertrain.

Subsystems of this product
--------------------------

.. needtable::
   :filter: type == "subsystem"
   :columns: id, title, covers, has_part
   :style: table

.. subsystem:: Vehicle Control Unit (VCU)
   :id: SUB_VCU
   :status: draft
   :part_of: SYS_VEHICLE
   :covers: REQ_ENERGY_SOURCE, REQ_RANGE_ESTIMATE, REQ_TRACTION_POWER_LIMIT, <<bev: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT>>, <<bus: REQ_DOOR_DRIVE_INTERLOCK>>

   The VCU shows the remaining energy and range and limits the traction power
   in every product, coordinates the high-voltage shutdown in battery-electric
   products and the door interlock in buses. Own documentation and C code
   (``src/vcu``).

.. if:: var.powertrain.type == 'bev'

   .. subsystem:: Charging Controller (CHG)
      :id: SUB_CHG
      :status: draft
      :part_of: SYS_VEHICLE
      :covers: REQ_MAX_CHARGE_POWER, <<mcs: REQ_MCS_CHARGING>>, <<pantograph: REQ_PANTOGRAPH_CHARGING>>, <<eu: REQ_EU_CHARGING_STANDARD>>, <<na: REQ_NA_CHARGING_STANDARD>>

      The CHG charges the battery at the rated charging power through the CCS
      inlet of the market (ISO 15118 session) and the high-power interface of
      the product (MCS inlet, roof pantograph or none). Battery-electric
      products only; own documentation and C code (``src/chg``).

   .. subsystem:: Battery Management System (BMS)
      :id: SUB_BMS
      :status: draft
      :part_of: SYS_VEHICLE
      :covers: REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT, REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT, REQ_MAX_CHARGE_POWER

      The BMS provides the state of charge, the permitted discharge power, the
      isolation fault with the main contactors and the cell limits for
      charging. Battery-electric products only; a separate product whose
      released needs are imported for the cell chemistry of the product (BMS
      release 0.1.0).

.. if:: var.powertrain.type == 'diesel'

   .. subsystem:: Engine Interface (ENG)
      :id: SUB_ENG
      :status: draft
      :part_of: SYS_VEHICLE
      :covers: REQ_ENERGY_SOURCE, REQ_TRACTION_POWER_LIMIT

      The ENG provides the fuel level from the tank sensor and passes the
      traction power limit to the engine control unit as an SAE J1939 torque
      limit. Diesel products only; own documentation and C code (``src/eng``).

Requirements of the system
--------------------------

The vehicle-level needs of this product, with the subsystems that cover them.

.. needtable::
   :filter: type in ["user_story", "req"] and is_external == False
   :columns: id, title, type, covered_by
   :style: table
