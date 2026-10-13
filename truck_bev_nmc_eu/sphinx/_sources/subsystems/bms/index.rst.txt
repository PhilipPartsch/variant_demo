Battery Management System (BMS)
===============================

Battery-electric products only. The BMS is a separate product; its needs are
imported for the product's cell chemistry (:variant:`bms.chemistry`) with the
prefix ``BMS_``. The subsystem need :need:`SUB_BMS` names the vehicle
requirements it covers and its black boxes.

.. needtable::
   :filter: id == "SUB_BMS"
   :columns: id, title, covers, has_part
   :style: table

.. toctree::
   :maxdepth: 1

   architecture
   integration
