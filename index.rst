.. _full-example:

ubCode Full Example
===================

A feature tour for ubCode:

- requirements in **reStructuredText** and tests in **Markdown (MyST)**,
  indexed together by file routing;
- multiple need types (``req``, ``spec``, ``test``) and traceability links
  (``implements``, ``tests``);
- typed fields and build variants (the "150%" model).

Build it with the ``ubc`` CLI -- see ``README.md``.

.. toctree::
   :hidden:

   specifications
   tests

.. req:: User authentication
   :id: REQ_AUTH
   :status: <<[var.platform == "windows"]: win_auth, default_auth>>
   :platform_note: Built for <{ var.platform }>

   The system shall authenticate users before granting access.
   ``status`` resolves per build variant; ``platform_note`` embeds variant data.

.. req:: Audit logging
   :id: REQ_LOG

   The system shall record an audit trail of authentication events.
