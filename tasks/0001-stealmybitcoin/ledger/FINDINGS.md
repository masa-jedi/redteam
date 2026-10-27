# Findings ledger

| id | task | title | severity | status | evidence | independent |
|---|---|---|---|---|---|---|
| F1 | 0001 | Unauthenticated RCE through PHP 8.4.26 multipart/session parsing | Critical (lab) | verified, 4 successes | `tasks/0001-stealmybitcoin/findings/FINDINGS.md`; `evidence/run-nginx4`; `evidence/run-verify-20261026T103741Z-1` | partial — GLM agrees core; C3/C8/C9 time-boxed |
| F2 | 0001 | Successful callback crashes the CLI server parent (exit 139) | Medium | observed | `evidence/php-exit.txt`; `evidence/php-run-nginx4.log` | partial — GLM agrees core; C3/C8/C9 time-boxed |

## Severity rationale

- F1: network, no credentials, no user interaction, code execution as the worker
  (uid 0 in this lab), flag disclosure. CVSS 3.1 input `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H`
  = 8.1; AC:H because the chain is build- and race-specific. Business impact is scoped
  to the lab until a real deployment is in scope.
- F2: availability after RCE. The response is delivered before the crash; the parent is
  PID 1, so the container stops. No restart policy.

## Open

- Independent verification: GLM report at
  `tasks/0001-stealmybitcoin/verify/VERIFIER-REPORT.md`; core agreed, no refutations,
  C3/C8/C9 time-boxed. Do not label it fully independent until those are re-run.
- Patched PHP build: no vendor fix in the lab; mutation A is a mitigation, not a fix.
- Detection correlation: the OOM rule exists; the access-log `$request_length`
  correlation and the runtime rule are not implemented.
- Real-target exposure: out of scope. No CVE asserted.
