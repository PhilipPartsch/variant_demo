Reports
=======

Traceability, coverage and BMS usage of this build's product
(:variant:`meta.product`). Every table is evaluated per product: switching the
product changes the rows without changing the sources.

Product and BMS version
-----------------------

- Product: :variant:`meta.product` (vehicle :variant:`vehicle.type`,
  powertrain :variant:`powertrain.type`, market :variant:`market.region`)
- BMS release 0.1.0 (``third_party/bms/0.1.0/``), cell chemistry
  :variant:`bms.chemistry` (empty for diesel products: no BMS)

Vehicle requirements → architecture
-----------------------------------

Every vehicle requirement and the CV architecture elements (``arch``) and BMS
black boxes (``bms_block``) that satisfy it.

.. needtable::
   :filter: type in ["arch", "bms_block"] and is_external == False
   :columns: id, title, type, satisfies
   :style: table

Software requirements → code and tests
--------------------------------------

.. needtable::
   :filter: type in ["impl", "test"] and is_external == False
   :columns: id, title, type, implements, verifies
   :style: table

BMS usage
---------

BMS interface needs this product allocates, with the chemistry they are
resolved for.

.. needtable::
   :filter: type == "bms_block"
   :columns: id, title, allocates
   :style: table

Needflow: user story to BMS
---------------------------

.. needflow::
   :filter: (type in ["user_story", "req", "arch", "bms_block"] and is_external == False) or (id.startswith("BMS_REQ_") and "interface" in tags)
   :show_link_names:

Variant comparison
------------------

The comparison of the products (``needs.json`` per product, side by side) is
part of the published site (plan 6), not of a single product build.
