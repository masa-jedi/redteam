# ADR 0001 — Apache mod_php, not the built-in server or FPM

Status: superseded by ADR 0002, 2026-10-26. Kept as the failed-path record.

## Context

The specimen pipelines one OOM producer and eight consumers on a single connection, then
expects the worker's heap to survive and serve the consumers. It also runs a final
command that writes to the accepted socket FD, which requires the PHP process to own that
socket.

## Options

1. `php -S` with `PHP_CLI_SERVER_WORKERS=4` from the FPM image. Its CLI binary has the
   exact calibration (`zval_ptr_dtor` at `0x712930`, low21 `0x112930`).
2. PHP-FPM behind nginx. The FPM worker does not own the client socket, so the proof
   command cannot write to the response.
3. Apache prefork with mod_php. The child owns the accepted socket and survives a PHP
   fatal error, so the next pipelined request reuses its heap.

## Evidence

- Option 1: the server accepted the producer connection and closed it before logging any
  request; the client received `RemoteDisconnected`. The remaining pipelined requests
  were lost. The log shows `Accepted` then `Closing` with no request line, then a later
  `Invalid request (Malformed HTTP request)`. This is a server-class failure, not a
  payload failure.
- Option 3: a nine-request pipelined GET test against `php:8.4.26-apache` returned nine
  `HTTP/1.1 200` responses on one connection.
- Option 2 is rejected by the socket-ownership argument.

## Decision

Build PHP 8.4.26 on Alpine with Apache (`--with-apxs2`) using the official FPM image's
configure flags plus the Apache SAPI. Verify the built `libphp.so` against the specimen's
calibration before running the chain. If the offsets differ, record partial fidelity
rather than editing the specimen to fit.

## Consequences

The lab needs a compiled `libphp.so`, not an off-the-shelf image. The build script is a
first-class artifact, and `make php-build` is a prerequisite for a clean checkout. The
Debian `php:8.4.26-apache` image is not usable: its `zval_ptr_dtor` low21 is `0x5db60`,
not `0x112930`.
