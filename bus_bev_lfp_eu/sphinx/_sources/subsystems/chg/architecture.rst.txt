Architecture
============

Architecture elements (``arch``) of the Charging Controller (CHG), each
satisfying vehicle requirements. Workflow stage ``archs``, stream ``chg``.
The whole folder exists only in battery-electric products.

.. Showcase B: three alternatives with one id; the first true branch wins
   (MCS before pantograph, see DEC_CHARGING_INLET_PRIORITY). With the
   sphinx-needs `choose` directive this becomes when / when / otherwise.

.. if:: var.charging.mcs == True

   .. arch:: High-power charging interface
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER, REQ_MCS_CHARGING

      The high-power charging interface is an MCS vehicle inlet (IEC 63379)
      next to the CCS inlet, rated for the charging power of
      REQ_MAX_CHARGE_POWER, with connector lock and pin temperature monitoring.

.. if:: var.charging.pantograph == True and not (var.charging.mcs == True)

   .. arch:: High-power charging interface
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER, REQ_PANTOGRAPH_CHARGING

      The high-power charging interface is a vehicle-mounted roof pantograph
      (SAE J3105-2) that is raised at the charging stop, rated for the charging
      power of REQ_MAX_CHARGE_POWER.

.. if:: not (var.charging.mcs == True) and not (var.charging.pantograph == True)

   .. arch:: High-power charging interface
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER

      There is no additional high-power interface: the vehicle charges with
      the power of REQ_MAX_CHARGE_POWER through the CCS inlet, which is locked
      during the session.

.. Alternatives per market: the CCS inlet type follows the market.

.. if:: var.market.region == 'eu'

   .. arch:: CCS inlet and charging session
      :id: ARCH_CHG_SESSION_CONTROL
      :status: draft
      :satisfies: REQ_EU_CHARGING_STANDARD

      The CCS inlet is a CCS2 vehicle inlet (IEC 62196-3). The charging session
      control runs the session with the charger over ISO 15118-2 and sets the
      charging current limit from the BMS cell limits.

.. if:: var.market.region == 'na'

   .. arch:: CCS inlet and charging session
      :id: ARCH_CHG_SESSION_CONTROL
      :status: draft
      :satisfies: REQ_NA_CHARGING_STANDARD

      The CCS inlet is a CCS1 vehicle inlet (SAE J1772). The charging session
      control runs the session with the charger over ISO 15118-2 and sets the
      charging current limit from the BMS cell limits.
