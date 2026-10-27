#!/usr/bin/env bash
# v2 harness: workspace DOCKER_CONFIG, but still pre-creates the PoC output dir.
# Used to reproduce the FileExistsError before the append-only guard.
set -uo pipefail

ATTEMPT="${1:?attempt id}"
NET="${2:?network container}"
TARGET="${3:?target url}"
SPECIMEN="${4:-/specimen/stealmybitcoin_poc.py}"

REPO="/home/jedi/abliterated/redteam"
export DOCKER_CONFIG="$REPO/.docker"
mkdir -p "$DOCKER_CONFIG"
TASK="$REPO/tasks/0001-stealmybitcoin"
EVID="$TASK/evidence"
OUT="$EVID/run-loop-$ATTEMPT"
mkdir -p "$OUT"
LOG="$OUT/attempt.log"

set +e
timeout 180 docker run --rm --network "container:$NET" \
  -u "$(id -u):$(id -g)" \
  -v "$TASK/specimen:/specimen:ro" \
  -v "$TASK/iterations:/iterations:ro" \
  -v "$EVID:/out" \
  python:3.12-alpine \
  python "$SPECIMEN" --url "$TARGET" --output-dir "/out/run-loop-$ATTEMPT" 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
echo "exit=$rc" | tee -a "$LOG"
exit "$rc"
