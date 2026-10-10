CV platform
===========

A commercial vehicle (CV) platform — truck or bus, diesel or battery-electric —
documented once as a **150 % model** and built per **product**. The project
shows variant management across requirements, architecture, code and tests
with Kconfig, CMake, sphinx-needs, sphinx-mounts, sphinx-codelinks and ubCode.

This build: **product** :variant:`meta.product` · vehicle :variant:`vehicle.type`
· powertrain :variant:`powertrain.type` · BMS chemistry :variant:`bms.chemistry`
· market :variant:`market.region`

Products
--------

==================  =======  ==========  =========  =======  ==========  ======
Product             Vehicle  Powertrain  Chemistry  HV       Charging    Market
==================  =======  ==========  =========  =======  ==========  ======
truck_diesel_eu     truck    diesel      —          —        —           EU
truck_bev_nmc_eu    truck    BEV         NMC        800 V    MCS         EU
bus_bev_lfp_eu      bus      BEV         LFP        400 V    pantograph  EU
truck_bev_lfp_na    truck    BEV         LFP        800 V    CCS only    NA
==================  =======  ==========  =========  =======  ==========  ======

How a product is built
----------------------

1. **Kconfig** holds the feature model; one ``configs/<product>_defconfig`` per
   product selects the features.
2. Selecting the product in **CMake** (VS Code CMake Tools or
   ``tools/build_product.sh``) generates the variant data ``var.*``, selects the
   imported BMS needs of the product's chemistry and the compile database of
   its code.
3. The documentation reads the variant data: needs, fields, links, whole files
   and code markers appear only where their condition holds.
4. Every product is built with **ubc** (ubCode) and **Sphinx**; both results
   must agree.

The battery management system (BMS) is a **separate product**: its released
needs are imported per cell chemistry with the prefix ``BMS_``, and the CV
platform links only to its interface needs.

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

.. toctree::
   :maxdepth: 1
   :caption: Method

   method/metamodel
   method/requirements
   method/architecture
   method/testing
