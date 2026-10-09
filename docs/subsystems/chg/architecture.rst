Architecture
============

Architecture elements (``arch``) of the Charging Controller (CHG), each
satisfying vehicle requirements. Workflow stage ``archs``, stream ``chg``.
The whole folder exists only in battery-electric products.

.. Showcase B: three alternatives with one id; the first true branch wins
   (MCS before pantograph, see DEC_CHARGING_INLET_PRIORITY). With the
   sphinx-needs `choose` directive this becomes when / when / otherwise.

.. if:: var.charging.mcs == True

   .. arch:: Charging inlet
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER, REQ_MCS_CHARGING

      The charging inlet is a Megawatt Charging System inlet for up to 1000 kW
      at 800 V, with connector lock and temperature monitoring.

.. if:: var.charging.pantograph == True and not (var.charging.mcs == True)

   .. arch:: Charging inlet
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER, REQ_PANTOGRAPH_CHARGING

      The charging inlet is a roof pantograph contact rail for opportunity
      charging plus a plug-in inlet for depot charging.

.. if:: not (var.charging.mcs == True) and not (var.charging.pantograph == True)

   .. arch:: Charging inlet
      :id: ARCH_CHG_INLET
      :status: draft
      :satisfies: REQ_MAX_CHARGE_POWER

      The charging inlet is a single plug-in inlet with connector lock and
      temperature monitoring.

.. Alternatives per market: the session control follows the charging standard
   of the market.

.. if:: var.market.region == 'eu'

   .. arch:: Charging session control
      :id: ARCH_CHG_SESSION_CONTROL
      :status: draft
      :satisfies: REQ_EU_CHARGING_STANDARD

      The charging session control runs the CCS2 charging session with the
      charger (ISO 15118 communication) and sets the charging current limit.

.. if:: var.market.region == 'na'

   .. arch:: Charging session control
      :id: ARCH_CHG_SESSION_CONTROL
      :status: draft
      :satisfies: REQ_NA_CHARGING_STANDARD

      The charging session control runs the CCS1 charging session with the
      charger (ISO 15118 communication) and sets the charging current limit.
