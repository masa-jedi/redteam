# Hypotheses — pre-registration

Written after static reading of the specimen, before any execution against the lab.
The upstream writeup is sealed and was not read.

- Upstream: https://github.com/KillaBoi/StealMyBitcoin-PoC
- Pinned commit: `bd137b9881734ed3ee922d853c606ccf0e515db7`
- Specimen sha256: `eed0a0d670f9d85539ec7f272a0a42e8bde7080f50c6918efcf14caca9ce82f0`
- Sealed README sha256: `a2897d3be8ec407fb473e4f466b8b365f7a3ae62f175239c39fc163e9745286d`
- Seal rule: the README is not opened before Phase 5. Unseal consists of re-fetching the
  pinned commit, checking the hash above, and only then reading.
- Static triage preceded this file. No request has been sent to any target.

## Predictions

| id | claim | falsifier | confidence |
|---|---|---|---|
| H1 | The vulnerability is in PHP 8.4.26's multipart/session-upload-progress parsing, not in the application code. The app only needs to expose a version page and start a session. | A minimal app with the right php.ini fails at preflight or produces no OOM. | high |
| H2 | The lab must be Apache + mod_php, not FPM. The final command writes to the accepted socket FD; an FPM worker does not own the client socket. | The same chain succeeds under FPM/nginx, or the final proof fails under Apache for a reason unrelated to the FD. | high |
| H3 | The producer OOM leaves stale session state in a reused worker; one of eight pipelined consumers returns a 256-byte `PHPSESSID` containing at least four pointers agreeing on a 2 MiB-aligned Zend chunk base. | All consumers return 32-byte cookies, or the candidate count is not exactly one, on a correctly configured lab. | medium |
| H4 | The code leak returns a 16-byte cookie whose second qword is `zval_ptr_dtor` with low 21 bits `0x112930`, matching the official Alpine PHP 8.4.26 build. | A different low-21 value on the same PHP version, or no 16-byte cookie. | medium |
| H5 | The final forged HashTable calls `zif_system`, and the proof command's output (nonce, `uid=`, `sha256sum print-flag`, flag) appears in the HTTP response body. | The response lacks any of the three markers, or the worker crashes before writing. | medium |
| H6 | PHP returns HTTP 200 for the memory-limit fatal error in this configuration, not 500. | Producer status is 500 or the body lacks `Allowed memory size ... exhausted`. | medium |
| H7 | The benign baseline (GET version page, one ordinary multipart upload, one normal session) never OOMs, never returns a non-32-byte cookie, and never spawns `sh` from the web worker. | Any baseline request produces an OOM, an anomalous cookie, or a shell child. | high |
| H8 | The Debian-based `php:8.4.26-apache` binary has different symbol offsets from the Alpine build the PoC was calibrated on, so either the code leak or the final callback fails until the offsets are recalibrated. | The Debian image matches `DTOR_LOW21 = 0x112930` and `ZIF_SYSTEM_FROM_DTOR = -0x204BC0`. | medium |

## Predicted loss mechanism

Remote code execution as the web user, then `print-flag` reads the synthetic flag. The
"loss" is disclosure of the flag and execution proof, not a financial transfer. The
chain oracle is replaced by a flag oracle: the flag value must be compared outside the
exploit's own output path.

## Predicted detection signal

A burst of nine keep-alive multipart requests, a 128 MiB memory-limit fatal error, and a
`Set-Cookie: PHPSESSID=` whose value is not 32 bytes, followed by a `sh -c` child of the
Apache worker. The strongest single signal is the anomalous cookie length plus the OOM.

## Scoring

Every row above is scored hit / miss / partial in `RETRO.md` after the run and after
unsealing. A miss is recorded with the observation that falsified it, not edited away.
