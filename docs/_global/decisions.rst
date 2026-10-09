Decisions
=========

Design decisions (``decision``): context, alternatives, consequences and
rationale.

.. if:: var.powertrain.type == 'bev'

   .. decision:: Use the BMS as an external product
      :id: DEC_BMS_AS_EXTERNAL_PRODUCT
      :status: draft
      :affects: ARCH_VCU_POWER_MGMT

      **Context:** The battery-electric products need the battery management
      system (BMS), which is developed as a separate product with its own
      requirements, variants (cell chemistry) and releases.

      **Alternatives:** (1) Import the released BMS needs per chemistry as
      external needs. (2) Mount the BMS documentation sources into the CV build.
      (3) Copy the relevant BMS requirements into the CV documentation.

      **Consequences:** The CV platform links to BMS interface needs only,
      pins a BMS release and selects the chemistry per product; the traction
      power manager allocates the BMS power derating. BMS pages are not part of
      the CV documentation.

      **Rationale:** Alternative 1 keeps the BMS independent and needs no BMS
      configuration in the CV project; mounting would require the BMS
      metamodel and variant data, copying would drift from the BMS.

   .. decision:: MCS takes priority over the pantograph
      :id: DEC_CHARGING_INLET_PRIORITY
      :status: draft
      :affects: ARCH_CHG_INLET

      **Context:** The Kconfig model allows a product with both megawatt
      charging (MCS) and a roof pantograph, but the vehicle has room for one
      high-power charging interface.

      **Alternatives:** (1) MCS first. (2) Pantograph first. (3) Forbid the
      combination in Kconfig.

      **Consequences:** The high-power charging interface is selected in the
      order MCS, pantograph, none; a product with both features gets the MCS
      interface and no pantograph requirement is satisfied.

      **Rationale:** MCS serves long-haul trucks, the main BEV use case; the
      order keeps the Kconfig model open for a future pantograph truck.
