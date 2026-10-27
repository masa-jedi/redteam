# ADR 0002 — CLI server behind nginx

Status: accepted, 2026-10-26. Supersedes ADR 0001.

## Context

ADR 0001 chose Apache prefork + mod_php because the final command must write to the
accepted socket and because Apache pipelines. The Apache build matched the function
delta (`zif_system - zval_ptr_dtor = -0x204bc0`) but the worker aborted with
`zend_mm_heap corrupted` before the consumers, and the module's low21 was `0x6f430`,
not the specimen's `0x112930`.

The direct CLI server from `php:8.4.26-fpm-alpine3.23` has the exact fingerprint
(`zval_ptr_dtor` at `0x712930`) and its worker survives the OOM, but it closes the
connection after the producer, so nine pipelined requests on one connection lose the
eight consumers.

## Options

1. Apache mod_php. Rejected: OOM child abort; wrong module base.
2. PHP-FPM + nginx. The worker does not own the client socket; the proof command writes
   to the wrong socket.
3. CLI server directly. The worker survives, but the client connection closes after the
   producer.
4. **CLI server behind nginx.** nginx accepts the client connection and pipelines the
   nine requests sequentially; each upstream request is a new connection to the CLI
   server's four-worker pool. The poisoned worker is reused, and the final command
   writes to the **upstream** socket, which nginx forwards into the response.

## Decision

Option 4. The lab is `php -S 0.0.0.0:8000 -t /app` with `PHP_CLI_SERVER_WORKERS=4`
from the FPM image, behind `nginx:1.27-alpine` with
`proxy_pass http://php:8000; proxy_http_version 1.1;`.

This matches the unsealed writeup's lab and the observed fingerprint. The final
success was reached after unsealing; `RETRO.md` records that honestly.

## Evidence

- Direct CLI: producer OOM, connection reset, `RemoteDisconnected`, no consumers
  (`evidence/run-heap1`).
- Apache: producer 200 + OOM, `zend_mm_heap corrupted`, SIGABRT, reset
  (`evidence/run-apache1`, `lab/attempts/apache/`).
- CLI + nginx: heap `0x783213000000`, code `0x5b5334112930`, final verified
  (`evidence/run-nginx4`); four verified bodies total; `make verify` passes.
- Static: `readelf` on the image CLI `zval_ptr_dtor=0x712930`, low21 `0x112930`.

## Consequences

- The exploit's socket trick is on the nginx upstream connection, not the client
  connection. A direct-to-CLI deployment would behave differently.
- The CLI server closes each upstream connection; nginx reconnects. The worker pool is
  what makes the consumers race for the poisoned worker.
- The successful callback kills the CLI server parent (exit 139); the container needs a
  restart. `make verify` restarts it between attempts.
- The Apache build is kept under `lab/attempts/apache/` as evidence, not used.
