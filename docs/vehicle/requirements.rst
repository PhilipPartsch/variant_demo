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
      reported by the battery management system.

.. if:: not (var.powertrain.type == 'bev')

   .. req:: Remaining energy display
      :id: REQ_ENERGY_SOURCE
      :status: draft
      :traces_to: US_RANGE_AWARENESS

      The vehicle shall display the remaining energy as the fuel tank level.

.. req:: Range estimate
   :id: REQ_RANGE_ESTIMATE
   :status: draft
   :traces_to: US_RANGE_AWARENESS

   The vehicle shall display the estimated remaining range, calculated from the
   remaining energy of its energy source (:variant:`powertrain.type`).

Traction power
--------------

.. req:: Traction power limit
   :id: REQ_TRACTION_POWER_LIMIT
   :status: draft
   :traces_to: US_PREDICTABLE_POWER
   :value: <<bus: 250 kW, 450 kW>>

   The vehicle shall not deliver more traction power than the limit announced
   to the driver, at most the value of this requirement.

Charging and high voltage
-------------------------

.. if:: var.powertrain.type == 'bev'

   .. req:: Maximum charging power
      :id: REQ_MAX_CHARGE_POWER
      :status: draft
      :traces_to: US_FAST_DEPOT_CHARGING
      :value: <<mcs: 1000 kW, 350 kW>>

      The vehicle shall accept charging power up to the value of this
      requirement.

   .. req:: High-voltage shutdown on isolation fault
      :id: REQ_HV_SHUTDOWN_ON_ISOLATION_FAULT
      :status: draft
      :traces_to: US_HV_SAFETY

      The vehicle shall disconnect the high-voltage battery and warn the driver
      when an isolation fault is detected.

.. if:: var.charging.mcs == True

   .. req:: Megawatt charging
      :id: REQ_MCS_CHARGING
      :status: draft
      :traces_to: US_FAST_DEPOT_CHARGING

      The vehicle shall support charging sessions with the Megawatt Charging
      System (MCS).

.. if:: var.charging.pantograph == True

   .. req:: Pantograph charging
      :id: REQ_PANTOGRAPH_CHARGING
      :status: draft
      :traces_to: US_OPPORTUNITY_CHARGING

      The vehicle shall support opportunity charging through a roof-mounted
      pantograph at terminal stops.

Passenger safety
----------------

.. if:: var.vehicle.type == 'bus'

   .. req:: Door and drive interlock
      :id: REQ_DOOR_DRIVE_INTERLOCK
      :status: draft
      :traces_to: US_PASSENGER_DOOR_SAFETY

      The vehicle shall inhibit traction while a passenger door is open.
