# Attempt: Apache mod_php (rejected)

Kept as history, not used by the lab.

## Why it was tried

The exploit pipelines one OOM producer and eight consumers and needs the worker to
survive and own the accepted socket. Apache prefork with mod_php was the first server
class tried because it supports HTTP pipelining and keeps the child alive across a PHP
fatal error.

## What happened

- PHP 8.4.26 was built on Alpine 3.23 with `--enable-fpm --with-apxs2`. The code layout
  matched the specimen's function delta exactly (`zif_system - zval_ptr_dtor =
  -0x204bc0`), but the module base put `zval_ptr_dtor` low21 at `0x6f430`, not `0x112930`.
- The OOM producer returned HTTP 200 with the memory-limit fatal, then the child aborted:
  `zend_mm_heap corrupted`, `exit signal Abort (6)`. Apache reset the connection before
  any consumer response, so the leak stage could not start.
- Apache did pipeline nine requests correctly on a benign test, so the failure was the
  OOM/allocator lifecycle, not HTTP handling.

## What the unsealed writeup showed

The intended lab is the **CLI server** from `php:8.4.26-fpm-alpine3.23` with
`PHP_CLI_SERVER_WORKERS=4`, behind nginx. That build's CLI binary has `zval_ptr_dtor`
low21 exactly `0x112930`, and the CLI server's worker survives the OOM while nginx
reconnects for each consumer. The Apache build was rejected for the right reason but
was the wrong server class.
