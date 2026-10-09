Risks
=====

Vehicle-level risks (``risk``), each mitigated by a requirement.

.. if:: var.powertrain.type == 'bev'

   .. risk:: Electric shock after an insulation failure
      :id: RISK_HV_EXPOSURE
      :status: draft
      :mitigates: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT

      A failed insulation of the high-voltage system can expose the driver or a
      workshop technician to a dangerous touch voltage.

.. if:: var.vehicle.type == 'bus'

   .. risk:: Passenger caught in a door while the bus moves off
      :id: RISK_DOOR_TRAP
      :status: draft
      :mitigates: REQ_DOOR_DRIVE_INTERLOCK

      A passenger who is still in the door area can be caught or fall when the
      bus moves off with an open door.
