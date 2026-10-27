# Preserved harness versions — rerun

The first loop's v1/v2 harness files were overwritten. This directory preserves the
three versions for the rerun so the progression is executable, not reconstructed.

| Version | File | Behavior | Reproduces |
|---|---|---|---|
| v1 | `run_attempt-v1.sh` | No `DOCKER_CONFIG`; no pre-created output dir; temp log | Direct CLI works; direct `docker compose` fails on `/home/jedi/.docker` |
| v2 | `run_attempt-v2.sh` | `DOCKER_CONFIG`; pre-creates `$OUT`; logs into it | `FileExistsError` before the PoC starts |
| v3 | `run_attempt-v3.sh` | Temp log; no pre-create; post-run copy; append-only guard | The final harness; drives the v3 loop |

Also preserved:

- `one-worker.yaml` — the one-worker deployment experiment.
- `specimen-wrong-delta.py` — the `HEAP_CARRIER_DELTA=0x0` experiment.

The first-loop files were overwritten; these files are the preserved rereun versions.
The behavioral differences match the original failures. The v3 file is the source of
truth; `iterations/run_attempt.sh` is the same code.

The rerun results are appended to `ATTACK-LOG.md` and `CODE-CHANGES.md`.

## Rerun results

| Version | Result | Evidence |
|---|---|---|
| v1 direct | `[health]`; `[abort] RemoteDisconnected`; exit 1 | `run-loop-direct-v1` |
| v1 compose | `mkdir /home/jedi/.docker: permission denied`; exit 1 | `run-loop-v1-compose.log` |
| v2 | `FileExistsError: /out/run-loop-one-worker-v2`; exit 1 | `run-loop-one-worker-v2` |
| v3 one-worker | `heap: expected one strict address, found 0`; exit 1 | `run-loop-one-worker-v3` |
| v3 upload-off | `producer did not return PHP 8.4.26 HTTP 200 OOM`; exit 1 | `run-loop-upload-off-v3` |
| v3 wrong-delta | heap `0x7cbcc9e00000`; code `0x5a3f58912930`; nonce `34f96e892217ecbd`; `execution_proof_verified: false` | `run-loop-wrong-delta-v4` |
| v3 final-v2 | heap `0x79e74b800000`; code `0x5f579df12930`; nonce `f5051bc60195565b`; `execution_proof_verified: true`; flag | `run-loop-final-v2` |
| v3 proof | 5/5; live attempt 3 `run-verify-20261027T094909Z-2` | `VERIFY-REPORT.json` |

## Hashes

| File | sha256 |
|---|---|
| `run_attempt-v1.sh` | `61c072d4f0682d241fac2cc00332792d81444cba9d011eb7b477a345ee9cfe3e` |
| `run_attempt-v2.sh` | `613974ef1a9d555dbe04a05dca64456419657ff51e00a8c53c943fb35fc7f8f3` |
| `run_attempt-v3.sh` | `8803702197bc235d7ea62079b05f10e500618f5752c5e7dc5801a0f2c08f6560` |
| `one-worker.yaml` | `a40df2d01f79e7861a6b7058db833cec35657564c1d2667e697aa0414720a6b7` |
| `specimen-wrong-delta.py` | `3e6a88463937444e63b97afbdd9d17736d5485f5a49b153e0f1e773f93117b2d` |
