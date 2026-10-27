#!/usr/bin/env bash
# v1 harness: no DOCKER_CONFIG; no pre-created output dir; no append-only guard.
# Used to reproduce the first-loop harness failures.
set -uo pipefail

ATTEMPT="${1:?attempt id}"
NET="${2:?network container}"
TARGET="${3:?target url}"
SPECIMEN="${4:-/specimen/stealmybitcoin_poc.py}"

REPO="/home/jedi/abliterated/redteam"
TASK="$REPO/tasks/0001-stealmybitcoin"
EVID="$TASK/evidence"
OUT="$EVID/run-loop-$ATTEMPT"
LOG_TMP="$(mktemp)"
trap 'rm -f "$LOG_TMP"' EXIT

set +e
timeout 180 docker run --rm --network "container:$NET" \
  -u "$(id -u):$(id -g)" \
  -v "$TASK/specimen:/specimen:ro" \
  -v "$TASK/iterations:/iterations:ro" \
  -v "$EVID:/out" \
  python:3.12-alpine \
  python "$SPECIMEN" --url "$TARGET" --output-dir "/out/run-loop-$ATTEMPT" 2>&1 | tee "$LOG_TMP"
rc=${PIPESTATUS[0]}

mkdir -p "$OUT"
cp "$LOG_TMP" "$OUT/attempt.log"
echo "exit=$rc" | tee -a "$OUT/attempt.log"
exit "$rc"
