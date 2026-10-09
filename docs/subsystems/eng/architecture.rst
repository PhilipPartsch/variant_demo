Architecture
============

Architecture elements (``arch``) of the Engine Interface (ENG), each
satisfying vehicle requirements. Workflow stage ``archs``, stream ``eng``.
The whole folder exists only in diesel products.

.. arch:: Fuel level provider
   :id: ARCH_ENG_FUEL_LEVEL
   :status: draft
   :satisfies: REQ_ENERGY_SOURCE

   The engine interface fuel level provider reads the tank level sensor and
   provides the fuel level in percent of the tank capacity to the VCU.

.. arch:: Engine torque interface
   :id: ARCH_ENG_TORQUE_INTERFACE
   :status: draft
   :satisfies: REQ_TRACTION_POWER_LIMIT

   The engine torque interface forwards the VCU torque request to the engine
   control unit and limits it to the engine torque curve.
