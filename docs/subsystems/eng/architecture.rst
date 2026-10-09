Architecture
============

Architecture elements (``arch``) of the Engine Interface (ENG), each
satisfying vehicle requirements. Workflow stage ``archs``, stream ``eng``.
The whole folder exists only in diesel products.

.. arch:: Fuel level provider
   :id: ARCH_ENG_FUEL_LEVEL
   :status: draft
   :satisfies: REQ_ENERGY_SOURCE

   The engine interface fuel level provider reads the analogue tank level
   sensor every 100 ms, averages it over 10 s against fuel slosh and provides
   the fuel level in percent of the tank capacity (1 % resolution) to the VCU.

.. arch:: Engine torque interface
   :id: ARCH_ENG_TORQUE_INTERFACE
   :status: draft
   :satisfies: REQ_TRACTION_POWER_LIMIT

   The engine torque interface converts the VCU traction power limit into a
   torque limit at the current engine speed and sends it to the engine control
   unit as an SAE J1939 torque/speed control (TSC1) message.
