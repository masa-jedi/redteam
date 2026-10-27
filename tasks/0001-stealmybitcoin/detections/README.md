# Detections — Task 001

What fired, on what, and what is still only content.

## YARA — specimen file

`yara/stealmybitcoin_poc.yar` matches the Python PoC on `$s3 zif_system`,
`$s4 print-flag`, and `$s5 multipart/form-data; boundary=`, with `filesize < 1MB`
and `3 of them`.

Test (output in `yara/TEST.txt`):

```sh
docker run --rm -v "$PWD":/w -w /w alpine:3.23 sh -c '
  apk add --no-cache yara
  yara -s tasks/0001-stealmybitcoin/detections/yara/stealmybitcoin_poc.yar \
    tasks/0001-stealmybitcoin/specimen/stealmybitcoin_poc.py
  yara tasks/0001-stealmybitcoin/detections/yara/stealmybitcoin_poc.yar \
    tasks/0001-stealmybitcoin/lab/php/php-version.php'
```

Result: **TP** on the specimen (script matched, strings printed); **TN** on the
six-line PHP app (no match, no output). The Alpine `yara` build in this test returned
exit 0 for both scans, so the test trusts the presence/absence of match output, not
the exit code.

Limits: the rule is a file/YARA match for the known PoC. A re-encoded or recompiled
variant with the same strings can match; a rewritten client can evade it. It does not
detect the attack on the wire.

## Sigma — PHP memory-limit fatal

`sigma/php_multipart_oom.yml` selects `Allowed memory size` + `exhausted` in a PHP
error log.

**The lab's CLI SAPI has `log_errors=Off`**, so the fatal goes to the HTTP response
body, not the server log. The rule's selection was therefore replayed on the saved
response body (`sigma/REPLAY.txt`):

| input | Sigma selection | `grep -cE 'Allowed memory size.*exhausted'` |
|---|---|---|
| `evidence/run-nginx4/final.response.body` (attack) | 1 | 1 |
| `detections/benign-body.txt` (version page) | 0 | 0 |

That is a **surrogate source**, not a deployed PHP error log. To use the rule as
written, the lab must set `log_errors=On` and `error_log=/dev/stderr` (or a file), then
replay against the real log. That change is not in the current image; do not claim a
live log detection until it is.

The rule is low-fidelity on its own: a legitimate large upload with a low limit can
fire it. Correlate with a POST burst and an anomalous `PHPSESSID` length (32 expected;
16 or 256 is the leak signature). The access log currently does not carry
`$request_length`; adding it is the next step for the correlation.

## Runtime — not tested

There is no tested runtime rule. A Falco/auditd rule for `print-flag` as a child of
`php -S`, or a canary that writes to a bind-mounted `/runtime`, would close the gap.
The `/tmp/flag-access.log` canary was lost when the container crashed; it is not
evidence. Do not claim runtime coverage for this task.

## What the detection set does not prove

- It does not prove the exploit; it is a signal.
- The Sigma replay is on a response body, not a SIEM.
- There is no correlation rule that joins the OOM to the 9-request burst and the
  anomalous cookie. That is the next iteration, and it needs a log pipeline.
