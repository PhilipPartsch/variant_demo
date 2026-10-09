Software requirements
=====================

Software requirements (``swreq``) of the Charging Controller (CHG), each
refining an architecture element. Workflow stage ``swreqs``, stream ``chg``.
The whole folder exists only in battery-electric products.

.. swreq:: Start session only with locked inlet
   :id: SWREQ_CHG_SESSION_START
   :status: draft
   :refines: ARCH_CHG_SESSION_CONTROL

   The CHG software shall start a charging session only while the CCS inlet is
   reported as locked.

.. swreq:: Limit charging current
   :id: SWREQ_CHG_CURRENT_LIMIT
   :status: draft
   :refines: ARCH_CHG_SESSION_CONTROL

   The CHG software shall request a charging current of at most the maximum
   charging power divided by the nominal pack voltage of the product.

.. swreq:: Derate on hot charging contacts
   :id: SWREQ_CHG_INTERFACE_DERATING
   :status: draft
   :refines: ARCH_CHG_INLET

   The CHG software shall halve the requested charging current while the
   contact temperature of the charging interface exceeds 90 °C.

.. if:: var.charging.mcs == True

   .. swreq:: MCS session setup
      :id: SWREQ_CHG_MCS_HANDSHAKE
      :status: draft
      :refines: ARCH_CHG_INLET

      The CHG software shall close the charging contactors only after the MCS
      session setup over ISO 15118-20 has completed.

.. if:: var.charging.pantograph == True and not (var.charging.mcs == True)

   .. swreq:: Raise pantograph at standstill only
      :id: SWREQ_CHG_PANTOGRAPH_SEQUENCE
      :status: draft
      :refines: ARCH_CHG_INLET

      The CHG software shall raise the pantograph only while the vehicle is at
      standstill with the parking brake applied.
