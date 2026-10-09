Architecture
============

Architecture elements (``arch``) of the Vehicle Control Unit (VCU), each
satisfying vehicle requirements. Workflow stage ``archs``, stream ``vcu``.

.. arch:: Energy display manager
   :id: ARCH_VCU_ENERGY_DISPLAY
   :status: draft
   :satisfies: REQ_ENERGY_SOURCE, REQ_RANGE_ESTIMATE

   The VCU energy display manager reads the remaining energy from the energy
   source of the product (battery state of charge or fuel tank level), derives
   the remaining range and sends both to the instrument cluster.

.. arch:: Traction power manager
   :id: ARCH_VCU_POWER_MGMT
   :status: draft
   :satisfies: REQ_TRACTION_POWER_LIMIT
   :allocates: <<bev: BMS_REQ_POWER_DERATING>>

   The VCU traction power manager caps the torque request so that the
   delivered traction power stays within the vehicle limit; in battery-electric
   products it also applies the power derating reported by the BMS.

.. if:: var.powertrain.type == 'bev'

   .. arch:: High-voltage shutdown coordinator
      :id: ARCH_VCU_HV_SHUTDOWN
      :status: draft
      :satisfies: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT

      The VCU high-voltage shutdown coordinator receives the isolation fault
      from the BMS and commands the main contactors open.

.. if:: var.vehicle.type == 'bus'

   .. arch:: Door and drive interlock
      :id: ARCH_VCU_DOOR_INTERLOCK
      :status: draft
      :satisfies: REQ_DOOR_DRIVE_INTERLOCK

      The VCU door interlock reads the closed-and-locked signals of all
      passenger doors and sets the traction torque request to zero while any
      door is not closed and locked.
