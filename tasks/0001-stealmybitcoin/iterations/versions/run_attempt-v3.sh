#!/usr/bin/env bash
# One bounded Task 001 attack attempt. Fail fast; keep the log.
#
# usage: run_attempt.sh <attempt-id> <network-container> <target-url> [specimen-path]
#
#   network-container: task001-php-1 (direct CLI) or task001-nginx-1 (proxy)
#   target-url:        http://127.0.0.1:8000/php-version.php or ...:8080/...
#   specimen-path:     /specimen/stealmybitcoin_poc.py (default) or
#                      /iterations/specimen-wrong-delta.py
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
if [ -e "$OUT" ]; then
  echo "[abort] evidence dir exists: $OUT; use a new attempt id" >&2
  exit 2
fi
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
