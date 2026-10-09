Software requirements
=====================

Software requirements (``swreq``) of the Engine Interface (ENG), each refining
an architecture element. Workflow stage ``swreqs``, stream ``eng``. The whole
folder exists only in diesel products.

.. swreq:: Report filtered fuel level
   :id: SWREQ_ENG_FUEL_LEVEL_REPORT
   :status: draft
   :refines: ARCH_ENG_FUEL_LEVEL

   The ENG software shall report the fuel level as the 10 s average of the tank
   level sensor in percent of the tank capacity, rounded to 1 %.

.. swreq:: Send engine torque limit
   :id: SWREQ_ENG_TORQUE_LIMIT
   :status: draft
   :refines: ARCH_ENG_TORQUE_INTERFACE

   The ENG software shall send the torque limit, calculated as the traction
   power limit divided by the current engine speed, in a TSC1 message every
   10 ms.
