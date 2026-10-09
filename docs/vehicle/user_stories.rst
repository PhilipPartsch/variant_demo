User stories
============

Vehicle-level user stories (``user_story``), one user-observable capability
each. Workflow stage ``user_stories``.

.. user_story:: Range awareness
   :id: US_RANGE_AWARENESS
   :status: draft

   As a driver, I know the remaining energy and range of my vehicle.

.. user_story:: Predictable traction power
   :id: US_PREDICTABLE_POWER
   :status: draft

   As a driver, I get predictable traction power, and limits are announced to me.

.. if:: var.powertrain.type == 'bev'

   .. user_story:: Fast depot charging
      :id: US_FAST_DEPOT_CHARGING
      :status: draft

      As a fleet operator, I recharge a vehicle within a driver break.

   .. user_story:: High-voltage safety
      :id: US_HV_SAFETY
      :status: draft

      As a driver or workshop technician, I am protected from high-voltage hazards.

   .. user_story:: Charging in the home market
      :id: US_MARKET_CHARGING
      :status: draft

      As a fleet operator, I charge the vehicle at the public charging
      infrastructure of its market.

.. if:: var.charging.pantograph == True

   .. user_story:: Opportunity charging
      :id: US_OPPORTUNITY_CHARGING
      :status: draft

      As a bus operator, I top up the battery at terminal stops.

.. if:: var.vehicle.type == 'bus'

   .. user_story:: Passenger door safety
      :id: US_PASSENGER_DOOR_SAFETY
      :status: draft

      As a bus passenger, I am safe while boarding and leaving through the doors.
