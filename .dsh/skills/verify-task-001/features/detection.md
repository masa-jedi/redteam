# detection

## Sub-features

- YARA matches the known PoC shape on the request/body artifacts.
- The Sigma rule describes the 200-with-fatal / OOM pattern.
- The benign baseline does not match.

## How to get to it (user POV)

A defender watches the proxy and the PHP error stream. The attack's producer returns a
200 carrying the memory-limit fatal; the callback returns the nonce/flag body. The
detection feature proves the attack is observable, not that the detection is complete.

## Driving it with the harness

```sh
make verify
```

The verification replays the detection artifacts in `detections/TEST.txt` and
`detections/REPLAY.txt`. The YARA rule is `detections/yara/stealmybitcoin_poc.yar`; the
Sigma rule is `detections/sigma/php_multipart_oom.yml`.

## Gotchas

- `log_errors=Off` in the lab means the Sigma rule is a **response-body surrogate**, not
  a real PHP error-log rule. Do not claim a runtime detection that was not observed.
- The YARA true-positive/true-negative test is on the recorded artifacts, not on live
  traffic.
- The detection is not the exploit; a match does not prove the callback fired.
