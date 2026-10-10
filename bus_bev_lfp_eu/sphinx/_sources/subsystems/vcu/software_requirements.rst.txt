Software requirements
=====================

Software requirements (``swreq``) of the Vehicle Control Unit (VCU), each
refining an architecture element. Workflow stage ``swreqs``, stream ``vcu``.

.. swreq:: Send remaining energy
   :id: SWREQ_VCU_ENERGY_DISPLAY
   :status: draft
   :refines: ARCH_VCU_ENERGY_DISPLAY

   The VCU software shall send the remaining energy of the energy source to the
   instrument cluster in percent, rounded to 1 %, once per second.

.. swreq:: Apply traction power limit
   :id: SWREQ_VCU_POWER_LIMIT_APPLY
   :status: draft
   :refines: ARCH_VCU_POWER_MGMT

   The VCU software shall limit the torque request to the active power limit
   divided by the current motor speed.

.. if:: var.powertrain.type == 'bev'

   .. swreq:: Request contactor opening on isolation fault
      :id: SWREQ_VCU_HV_SHUTDOWN
      :status: draft
      :refines: ARCH_VCU_HV_SHUTDOWN

      The VCU software shall send the contactor-open request to the BMS within
      10 ms after receiving the isolation fault.

.. if:: var.vehicle.type == 'bus'

   .. swreq:: Zero torque with open door
      :id: SWREQ_VCU_DOOR_INTERLOCK
      :status: draft
      :refines: ARCH_VCU_DOOR_INTERLOCK

      The VCU software shall set the torque request to zero while any passenger
      door is not reported as closed and locked.
