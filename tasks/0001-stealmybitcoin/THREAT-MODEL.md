# Threat model — Task 001

## Correction to the premise

The upstream repository is not a bitcoin stealer. It is a proof of concept for a
memory-corruption chain in PHP 8.4.26's multipart and session-upload-progress parsing.
The "Steal My Bitcoin" name is the CTF's theme, not the asset. The protected asset in
this lab is a synthetic flag. Any claim about funds, wallets, or a chain is out of scope
and would be a category error.

## Protected asset

- `/flag` in the victim container, readable by the web user, printed by
  `/usr/local/bin/print-flag`.
- Execution proof in the HTTP response: a fresh nonce, `uid=`, and the sha256 of
  `print-flag`. The nonce is generated microseconds before the request, so a replay
  cannot produce it.

## Adversary

- Unauthenticated remote HTTP client. No credentials, no prior access.
- Can send arbitrary HTTP/1.1: multipart bodies, keep-alive, pipelined requests.
- Knows the PHP version from `X-Powered-By`.
- Cannot read the flag or the filesystem before exploitation.
- Does not use phishing, host access, or a real user. There is no social engineering
  step in this chain.

## Trust boundary

The boundary is the HTTP request parser inside a reusable PHP worker. The worker's heap
survives across requests, and the flag sits on the far side of the parser, reachable
only after `zif_system` is called. The vulnerability is in the runtime, not in the
application: `php-version.php` only prints the version.

## Failure to reproduce

1. A 249 KiB multipart body with deeply nested field names amplifies into the 128 MiB
   memory limit during request parsing. The OOM leaves half-built session state in the
   worker.
2. Eight pipelined consumers race for that worker. One returns a 256-byte `PHPSESSID`
   containing heap pointers; at least four must agree on a 2 MiB-aligned Zend chunk base.
3. A second producer/consumer pair discloses `zval_ptr_dtor` in a 16-byte cookie, which
   locates the PHP code image.
4. A final multipart body plants a forged HashTable whose `pDestructor` is `zif_system`;
   PHP's cleanup path calls it with the command in the same buffer. The command writes
   to the upstream socket to nginx, because `zif_system`'s stdout does not reach the
   response; nginx forwards the injected bytes.

## Fidelity criteria

- PHP 8.4.26 from the Alpine build the PoC was calibrated on: `zval_ptr_dtor` low 21 bits
  `0x112930`, and `zif_system = zval_ptr_dtor - 0x204bc0`.
- `memory_limit=128M`, single multipart body under 1 MiB, four reusable workers.
- The FPM image's CLI server (`php -S`) with four workers, behind nginx: the worker
  must own the upstream socket and survive the OOM so a later consumer reuses its heap.
  Apache mod_php was rejected: the OOM child aborted with `zend_mm_heap corrupted`, and
  the module base did not match `0x112930`.
- If the build's symbol offsets differ, the final callback is not the original chain.
  Record the result as partial fidelity, not a success.

## Out of scope

`stealmybitcoin.com`, any real host, wallet, key, or third party. Other PHP versions,
persistence, lateral movement, and denial of service beyond the single calibrated burst
are also out of scope.
