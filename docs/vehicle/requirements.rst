Vehicle requirements
====================

Vehicle and system requirements (``req``), each tracing to a user story.
Product-specific values are held in the ``value`` field. Workflow stage ``reqs``.

Energy and range
----------------

.. Showcase A: alternatives with one id. Exactly one block is active per
   product; with the sphinx-needs `choose` directive this becomes when/otherwise.

.. if:: var.powertrain.type == 'bev'

   .. req:: Remaining energy display
      :id: REQ_ENERGY_SOURCE
      :status: draft
      :traces_to: US_RANGE_AWARENESS

      The vehicle shall display the remaining energy as the state of charge
      reported by the battery management system, in percent with a resolution
      of 1 %.

.. if:: not (var.powertrain.type == 'bev')

   .. req:: Remaining energy display
      :id: REQ_ENERGY_SOURCE
      :status: draft
      :traces_to: US_RANGE_AWARENESS

      The vehicle shall display the remaining energy as the fuel tank level, in
      percent of the tank capacity with a resolution of 1 %.

.. req:: Range estimate
   :id: REQ_RANGE_ESTIMATE
   :status: draft
   :traces_to: US_RANGE_AWARENESS

   The vehicle shall display the estimated remaining range in kilometres,
   calculated from the remaining energy and the average consumption of the last
   50 km. Energy source of this product: :variant:`powertrain.type`.

Traction power
--------------

.. req:: Traction power limit
   :id: REQ_TRACTION_POWER_LIMIT
   :status: draft
   :traces_to: US_PREDICTABLE_POWER
   :value: <<bus: 250 kW, 450 kW>>

   The vehicle shall limit the delivered traction power to the value of this
   requirement.

Charging and high voltage
-------------------------

.. if:: var.powertrain.type == 'bev'

   .. req:: Maximum charging power
      :id: REQ_MAX_CHARGE_POWER
      :status: draft
      :traces_to: US_FAST_DEPOT_CHARGING
      :value: <<mcs: 1000 kW, 350 kW>>

      The vehicle shall accept a sustained charging power up to the value of this
      requirement between 20 % and 80 % state of charge.

   .. req:: High-voltage shutdown on isolation fault
      :id: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT
      :status: draft
      :traces_to: US_HV_SAFETY

      The vehicle shall disconnect the high-voltage battery within 100 ms after
      the battery management system reports an isolation fault.

.. if:: var.charging.mcs == True

   .. req:: Megawatt charging
      :id: REQ_MCS_CHARGING
      :status: draft
      :traces_to: US_FAST_DEPOT_CHARGING

      The vehicle shall support charging sessions with the Megawatt Charging
      System (MCS) according to IEC 63379.

.. if:: var.charging.pantograph == True

   .. req:: Pantograph charging
      :id: REQ_PANTOGRAPH_CHARGING
      :status: draft
      :traces_to: US_OPPORTUNITY_CHARGING

      The vehicle shall support opportunity charging through a roof-mounted
      pantograph according to SAE J3105.

Passenger safety
----------------

.. if:: var.vehicle.type == 'bus'

   .. req:: Door and drive interlock
      :id: REQ_DOOR_DRIVE_INTERLOCK
      :status: draft
      :traces_to: US_PASSENGER_DOOR_SAFETY

      The vehicle shall inhibit traction while a passenger door is not detected
      as closed and locked.
