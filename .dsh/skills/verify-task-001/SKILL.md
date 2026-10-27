---
name: verify-task-001
description: Verify the Task 001 PHP 8.4.26 lab by driving the real attack path through nginx with a fail-fast loop, then prove the result with evidence and mutations. Use after changing the lab, the app, the PHP/nginx config, the specimen, or when a new agent must reproduce the RCE cold.
---

# verify-task-001

This is the project-local control skill for the Task 001 lab. It follows the pstack
`create-verification-skill` shape: launch, doctor, drive, evidence, cleanup, helpers,
plus a feature map. The drive is the attack loop: each attempt is one bounded
hypothesis, failures are recorded, and the loop stops at the first flag.

## Launch

```sh
make lab-up
```

This builds `task001-php:local`, `task001-nginx:local`, and `task001-telemetry:local`,
then starts `php`, `nginx`, and `telemetry` on the internal `task001_lab` network.
Readiness is the compose healthcheck: `php` and `nginx` must both be `healthy`, and
`http://127.0.0.1:8080/php-version.php` must return `PHP 8.4.26`. The first build needs
network access to pull the base images; after that the lab is offline.

Every direct `docker`/`docker compose` call in the loop must use
`DOCKER_CONFIG=$PWD/.docker`; `make` exports it. The PHP service runs the CLI server,
not FPM: `php -S 0.0.0.0:8000 -t /app` with `PHP_CLI_SERVER_WORKERS=4`. The nginx proxy listens on `8080` and forwards to
`php:8000` with `proxy_http_version 1.1`. The attacker shares nginx's network
namespace, so `127.0.0.1:8080` is the only lab endpoint it can reach.

## Doctor

One read-only pass before driving:

```sh
make lab-status
docker inspect --format '{{.State.Health.Status}}' task001-php-1 task001-nginx-1
docker run --rm --entrypoint cat task001-php:local /usr/local/bin/php > /tmp/task001-php-cli
readelf -sW /tmp/task001-php-cli | grep ' zval_ptr_dtor$'
docker compose -f tasks/0001-stealmybitcoin/lab/compose.yaml exec -T php \
  php -i | grep -E 'session.upload_progress.enabled|memory_limit'
```

`zval_ptr_dtor` must have low 21 bits `0x112930`; the image must be the Alpine PHP
8.4.26 CLI. `memory_limit` must be `128M` and `session.upload_progress.enabled` must be
`On`. The scope is lab-only: the specimen's `parse_target` accepts only
`stealmybitcoin.com`, `localhost`, and `127.0.0.1`; do not point it at a real host.

## Drive

The loop harness is `tasks/0001-stealmybitcoin/iterations/run_attempt.sh`. It runs one
bounded PoC attempt in a container sharing the target container's network namespace,
writes raw HTTP under `evidence/run-loop-<attempt>/`, and tees the log. Attempt IDs
are append-only: if the evidence directory exists, the harness refuses to overwrite it;
use a new ID.

The fail-fast sequence (one attempt per hypothesis; stop at the first flag):

1. **Direct CLI** — base lab, bypass nginx:
   `iterations/run_attempt.sh direct task001-php-1 http://127.0.0.1:8000/php-version.php`
   Expected: the CLI server closes the connection; no heap leak. Lesson: the proxy is
   part of the exploit, not just deployment.
2. **One worker** — restart with `iterations/one-worker.yaml`:
   `docker compose -f tasks/0001-stealmybitcoin/lab/compose.yaml -f tasks/0001-stealmybitcoin/iterations/one-worker.yaml up -d --build php nginx`
   `iterations/run_attempt.sh one-worker-1 task001-nginx-1 http://127.0.0.1:8080/php-version.php`
   Expected: the producer OOM kills the only worker; no consumer answers. Lesson: four
   workers are required for reuse.
3. **Upload progress off** — restart with `verify/mutation-off.yaml`:
   `docker compose -f tasks/0001-stealmybitcoin/lab/compose.yaml -f tasks/0001-stealmybitcoin/verify/mutation-off.yaml up -d --build php nginx`
   `iterations/run_attempt.sh upload-off task001-nginx-1 http://127.0.0.1:8080/php-version.php`
   Expected: no producer OOM; the heap stage has no candidate. Lesson:
   `session.upload_progress` is the trigger.
4. **Wrong heap carrier** — base lab, the research copy with
   `HEAP_CARRIER_DELTA=0x0`:
   `iterations/run_attempt.sh wrong-delta task001-nginx-1 http://127.0.0.1:8080/php-version.php /iterations/specimen-wrong-delta.py`
   Expected: the leaks work, the forged table is not at the carrier; the callback
   misses. Lesson: the heap base alone is not the target; the calibrated delta and
   offset are required.
5. **Correct** — base lab, the pinned specimen:
   `iterations/run_attempt.sh final task001-nginx-1 http://127.0.0.1:8080/php-version.php /specimen/stealmybitcoin_poc.py`
   Stop at the first body with the nonce, `uid=0`, the `print-flag` hash, and the flag.
   Do not continue attacking after the flag.

The final proof is `make verify`: fingerprint, benign baseline, live attack with bounded
retries, mutation A (upload progress off), mutation B (broken page). `make verify` starts
and stops its own lab.

## Evidence

- `evidence/run-loop-<attempt>/attempt.log` — the command and observed output.
- `evidence/run-loop-<attempt>/run.json` — stage results and errors.
- `evidence/run-loop-final/final.response.body` — first flag capture: nonce
  `27c3a0c37fe49e43`, `uid=0`, `475939… /usr/local/bin/print-flag`, and
  `FLAG{task001_php8426_lab_9f3c2a}`.
- `evidence/run-loop-final-v2/final.response.body` — rerun capture: nonce
  `f5051bc60195565b`, same flag, `execution_proof_verified: true`.
- `evidence/run-loop-final/final.json` — nonce, hashes, and
  `execution_proof_verified: true`.
- `evidence/run-loop-direct`, `run-loop-one-worker-c`, `run-loop-upload-off`,
  `run-loop-wrong-delta-3` — the failed hypotheses.
- `tasks/0001-stealmybitcoin/iterations/ATTACK-LOG.md` — every attempt, prompt, failure,
  and lesson.
- `tasks/0001-stealmybitcoin/iterations/ATTACK-PROMPT.md` — the refined attack prompt.
- `verify/VERIFY-REPORT.json` — the five-check proof; live pass on attempt 3 of
  `run-verify-20261027T091403Z-2`.
- `evidence/run-loop-upload-off`, `run-loop-wrong-delta-3` — the negative and carrier
  failures that shaped the final prompt.
- `evidence/MANIFEST.sha256` — integrity of the evidence set.
- `evidence/run-nginx4/ORACLE.txt` — the independent image read.

The proof standard: the real HTTP path (nginx -> CLI), the real worker pool, the real
cleanup callback. No internal setters, no test-only endpoint, no mock of the vulnerable
parser. The flag, nonce, `uid`, and binary hash must all be in the same response.

## Cleanup

```sh
make lab-down
```

This removes the project's containers and volumes. The `evidence/` directory is a bind
mount and survives. Never delete evidence during cleanup. One lab per repo; do not
double-drive the `task001` project name.

## Helpers

- `tasks/0001-stealmybitcoin/iterations/run_attempt.sh` — one bounded attempt.
- `tasks/0001-stealmybitcoin/verify/run_verify.py` — the five checks.
- `tasks/0001-stealmybitcoin/verify/baseline.py` — the benign baseline.
- `tasks/0001-stealmybitcoin/lab/probe.py` — the health/upload probe.
- `tasks/0001-stealmybitcoin/iterations/CODE-CHANGES.md` — the code progression.
- `tasks/0001-stealmybitcoin/iterations/versions/` — preserved v1/v2/v3 harnesses.

## Feature map

`features/README.md` indexes: `exploit-chain`, `benign-baseline`, `fingerprint`,
`detection`, `patch-crash`. Each file has the four H2s: `Sub-features`,
`How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`.

## Limits

- The exploit is a race: roughly 4/10 base attempts here; the upstream writeup reports
  7/10. A single miss is not a regression.
- A wrong `HEAP_CARRIER_DELTA` can still pass both leaks and return a 200 with
  `execution_proof_verified: false`; both leaks succeeding is not proof. The calibrated
  carrier delta/offset is required.
- The lab is a stand-in for the real challenge: the exact build, four workers, nginx,
  128 MiB, and heap layout are known here; on a real target they are not. The
  `parse_target` allowlist keeps the specimen on the lab.
- `make verify` passes 5/5, but the independent verifier is partial: C3 (flag oracle),
  C8 (sealed hash), and C9 (cold start) were time-boxed.
- The detection is partial: Sigma is a response-body surrogate because `log_errors=Off`.
  The tool-efficacy pass was not run. No CVE is asserted.
- The successful callback kills the CLI server parent (`Exited 139`); that is an
  availability side effect, not a second exploit.
- The final captured flag is `FLAG{task001_php8426_lab_9f3c2a}` (nonce
  `27c3a0c37fe49e43`); it is synthetic and lab-only.

## Maintenance

After a PHP image, worker count, memory limit, nginx config, or specimen change:
re-run the Doctor, re-run the loop once, update the feature map's `Gotchas`, refresh the
evidence manifest, and record the change in the task's `HANDOFF.md`. Use
`maintain-verification-skill` for the periodic audit. The task-local
`tasks/0001-stealmybitcoin/verify/SKILL.md` points here once this skill is the registered
source.
