# Retro — Task 001

## Hypothesis scorecard

| id | prediction | result | evidence |
|---|---|---|---|
| H1 | The bug is in PHP 8.4.26 multipart/session parsing, not the app. The app only prints the version. | **hit** | `lab/php/php-version.php` is six lines; the OOM/leak happens during request parsing; mutation A (`upload_progress=Off`) removes the producer OOM. |
| H2 | The lab must be Apache + mod_php, not FPM, because the final command needs the accepted socket. | **miss** | Apache did pipeline nine requests (`lab/attempts/apache/README.md`), but the OOM child aborted with `zend_mm_heap corrupted` and reset the connection (`run-apache1`). The intended lab is the CLI server behind nginx: the CLI worker owns the **upstream** connection and nginx forwards its bytes. |
| H3 | The producer OOM leaves stale session state; one of eight consumers returns a 256-byte cookie with ≥4 pointers agreeing on a 2 MiB chunk. | **hit** | `run-nginx4/heap.json`: heap `0x783213000000`, consumer 0 cookie `256`. |
| H4 | The code leak returns a 16-byte cookie with `zval_ptr_dtor` low21 `0x112930`. | **hit** | `run-nginx4/code.json`: `0x5b5334112930`; independent `readelf` on the CLI binary: `0x712930`. |
| H5 | The forged HashTable calls `zif_system`; the nonce, `uid`, binary hash, and flag appear in the response. | **hit** | `run-nginx4/final.response.body`; second success `run-verify-…-2`. |
| H6 | The producer returns HTTP 200 for the memory-limit fatal, not 500. | **hit** | `probe-oom.log`, `run-nginx4/heap.json` producer status 200. |
| H7 | The benign baseline never OOMs, never returns a non-32 cookie, never spawns a shell. | **hit** | `verify/baseline.py` pass; mutation B proves the baseline fails on a broken page. |
| H8 | The Debian `php:8.4.26-apache` offsets differ from the Alpine calibration. | **hit** | Debian `zval_ptr_dtor` low21 `0x5db60`; Alpine Apache module `0x6f430`; Alpine CLI `0x112930`. |

H2 is the one that cost the most time. Its falsifier was "the final proof fails under
Apache for a reason unrelated to the FD", and that is exactly what happened: the OOM
shutdown aborted the child. The Apache build matched the function **delta**
(`zif_system - zval_ptr_dtor = -0x204bc0`) but not the module base low21 or the worker
lifecycle. The delta is necessary, not sufficient.

## The blind phase, honestly

- The upstream README was fetched at 10:03, hashed (`a2897d3b…`) and sealed. It was not
  read until 10:26, after the built-in-server and Apache attempts. The seal hash was
  re-checked against a fresh fetch at unseal.
- The blind phase achieved: preflight against the CLI binary, the producer OOM, the
  `zend_mm_heap corrupted` abort, and the rejection of the direct built-in server and
  Apache. It did **not** achieve a heap leak or the callback.
- The nginx + CLI-server architecture came from the writeup's lab section after
  unsealing. The full RCE at 10:29 is a **reproduction of the documented lab**, not a
  blind discovery. The exploitation chain itself was always in the specimen; the
  missing piece was the deployment shape.
- The writeup also supplied the 7/10 success rate and the "callback miss / heap miss"
  failure modes, which shaped the retries. The finding says so; the result is not
  presented as independent of the writeup.

That is the learning loop the repo is for: the blind attempt produced a real negative
result and a precise question ("who owns the accepted socket, and what survives the
OOM?"), and the unsealed material answered the deployment question.

## What the writeup knew that the artifact did not

- The lab is the FPM image's **CLI** server (`php -S`, four workers) behind nginx, not
  FPM and not Apache. The CLI server closes each upstream connection after a response;
  nginx reconnects, which is what lets eight consumers reach the poisoned worker.
- The success rate is about 7/10, with two distinct miss modes: no heap candidate, or
  both leaks and a final callback miss. Neither is a partial success.
- Both leaks are stable per container (same addresses across runs) because the workers
  persist and ASLR is per process; the variable is which worker answers.
- The final command writes to the socket because `zif_system`'s stdout does not reach
  the HTTP response; nginx forwards the injected bytes.
- The live run recovered a WIF that did **not** derive the advertised prize address;
  the author calls that the creator's mistake. We did not use or need a real WIF.

## What we got wrong

1. **Apache by inference.** The socket-ownership requirement is satisfied by Apache
   too, and Apache pipelines. The missing inference was that a proxy in front of the
   CLI server also satisfies it: the CLI worker owns the nginx upstream socket. We
   tested the CLI server directly, saw the connection close, and changed server class
   instead of adding the proxy.
2. **Mutation mount as a directory.** The first mutation A used `./mutation-off.ini`
   in an override file; Compose resolved it against the base file's directory, created
   a directory at the target, and the ini silently did not load. The "mutation
   success" was a base success. Fixed with `../verify/…` and mode 644 (root with
   `cap_drop: ALL` cannot override DAC).
3. **`USE_ZEND_ALLOC=0`.** It disables the Zend allocator and therefore the memory
   limit, so the probe returned the version page with no OOM. Useful as a control,
   not as a workaround.
4. **`max_input_vars` changes.** Raising it to 10000 changed the OOM/abort behaviour;
   the intended lab keeps the default 1000 and the startup warning is part of the
   observed path.

## What the verification skill now protects

`make verify` encodes the lessons:

- the static binary fingerprint (`0x112930`) so a wrong image fails before any attack;
- the benign baseline so a broken page cannot be mistaken for a secured one;
- the live attack with bounded retries and integrity checks on nonce, hashes, heap
  alignment, code low21, and the independently read flag;
- mutation A, which removes the upload-progress path and must stop the attack at the
  producer;
- mutation B, which breaks the version page and must fail the baseline.

The first `make verify` run caught the bad mutation mount and the flaky heap/final
stages; that is the skill doing its job.

## Independent review

The GLM-5.3 verifier agreed on C1, C2, C4 (source hash), C5, C6, and C7, and refuted
nothing. It time-boxed C3 (flag re-run), C8 (seal re-check), and C9 (cold start) as
unclear. That is not a rubber stamp: the report is `verify/VERIFIER-REPORT.md`, and the
open items are in `HANDOFF.md`. Re-run them before calling the task fully independently
verified.

## Next task hygiene

- Start each new task with a new artifact and a new seal. Do not reuse this unsealed
  writeup as a blind target.
- Ask the deployment question first: which process owns the client socket, which owns
  the upstream socket, what survives the failure, and which workers are reused.
- Keep the producer/verifier split. The verifier must see only artifacts, not this
  retro or the producer's reasoning.
- Extract `tasks/_TEMPLATE/` only after this task's evidence and verify skill are
  stable; not before.
