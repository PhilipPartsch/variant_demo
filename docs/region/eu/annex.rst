Market annex: Europe
====================

Regulations and charging standards for the European market
(``MARKET__REGION__EU``). The file exists only in EU products; the charging
requirement inside it only in battery-electric ones (combined gating).

.. if:: var.powertrain.type == 'bev'

   .. req:: European charging standard
      :id: REQ_EU_CHARGING_STANDARD
      :status: draft
      :traces_to: US_MARKET_CHARGING

      The vehicle shall provide a CCS2 (Combined Charging System, type 2)
      charging inlet according to IEC 62196-3.
