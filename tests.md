# Verification

Tests authored in Markdown (MyST) and routed to the Markdown parser, while the
requirements they cover live in reStructuredText — all indexed together.

```{test} Authentication test
:id: TEST_AUTH
:tests: REQ_AUTH, SPEC_HASH

Verifies authentication succeeds for valid credentials.
```

```{test} Audit logging test
:id: TEST_AUDIT
:tests: REQ_LOG, SPEC_AUDIT

Verifies an audit record is written for each login attempt.
```
