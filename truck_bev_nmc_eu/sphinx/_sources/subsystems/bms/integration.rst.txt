BMS integration
===============

This product uses BMS release 0.1.0 with the cell chemistry
:variant:`bms.chemistry` (``third_party/bms/0.1.0/``). Chemistry-specific
values come from the imported needs and change with the product, without any
change to the CV content.

Allocated interface needs
-------------------------

.. needtable::
   :filter: type == "bms_block"
   :columns: id, title, satisfies, allocates
   :style: table

All BMS interface needs
-----------------------

.. needtable::
   :filter: id.startswith("BMS_") and "interface" in tags
   :columns: id, title, chemistry, allocated_from
   :style: table
