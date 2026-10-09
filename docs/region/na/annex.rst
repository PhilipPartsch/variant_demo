Market annex: North America
===========================

Regulations and charging standards for the North American market
(``MARKET__REGION__NA``). The file exists only in NA products; the charging
requirement inside it only in battery-electric ones (combined gating).

.. if:: var.powertrain.type == 'bev'

   .. req:: North American charging standard
      :id: REQ_NA_CHARGING_STANDARD
      :status: draft
      :traces_to: US_MARKET_CHARGING

      The vehicle shall charge through a CCS1 (Combined Charging System, type 1)
      inlet.
