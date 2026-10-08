CV platform
===========

Commercial vehicle platform — truck or bus, diesel or battery-electric. The
battery-electric products use the BMS product, whose needs are imported per
cell chemistry.

This build: **product** :variant:`meta.product` · vehicle :variant:`vehicle.type`
· powertrain :variant:`powertrain.type` · BMS chemistry :variant:`bms.chemistry`
· market :variant:`market.region`

.. toctree::
   :maxdepth: 2
   :caption: Vehicle

   vehicle/user_stories
   vehicle/requirements
   system/overview

.. toctree::
   :maxdepth: 2
   :caption: Subsystems

   subsystems/vcu/index
   subsystems/chg/index
   subsystems/eng/index
   subsystems/bms/index

.. toctree::
   :maxdepth: 1
   :caption: Market

   region/eu/annex
   region/na/annex

.. toctree::
   :maxdepth: 1
   :caption: Project

   _global/risks
   _global/decisions
   _global/test_results
   _global/gaps
   reports/index
