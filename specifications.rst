.. _full-specs:

Specifications
==============

.. spec:: Password hashing
   :id: SPEC_HASH
   :implements: REQ_AUTH

   Passwords shall be stored using a salted, memory-hard hash.

.. spec:: Structured audit records
   :id: SPEC_AUDIT
   :implements: REQ_LOG

   Each audit record shall be a structured, append-only entry.
