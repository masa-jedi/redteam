# Findings — Task 001

Target: local lab only. PHP 8.4.26 (Alpine CLI server, four workers) behind nginx
1.27. No real host, wallet, key, or third party was involved.

---

## F1 — Unauthenticated RCE through PHP 8.4.26 multipart/session parsing

**Status:** reproduced; producer-run independent flag/byte oracles pass; external model
review completed (core agreed; C3/C8/C9 time-boxed).
**Confidence:** high for this lab build; the chain is build-specific and a race.
**Severity:** Critical in the lab.

Technical: network-reachable, no credentials, no user interaction, code execution as
the worker (uid 0 in this lab because the CLI server runs as root), synthetic flag
disclosed. CVSS 3.1 as an input: `AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H` = 8.1. The
High attack complexity is real: the chain needs the Alpine 8.4.26 layout, four
reusable workers, and winning the worker/allocator race.

Business impact: full compromise of the web worker and anything readable by it. In
this lab that is the flag; in a real deployment it would be whatever the PHP process
can read. The upstream writeup reports a real challenge run that recovered a key,
with the caveat that the recovered WIF did not derive the advertised prize address.

### What happens

1. A 249 KiB multipart body with deeply nested field names is parsed into nested PHP
   arrays. With `memory_limit=128M`, parsing hits the limit and leaves stale session
   state in a reusable worker.
2. Eight pipelined consumers race for that worker. One returns a 256-byte
   `PHPSESSID` containing heap pointers; four or more agree on a 2 MiB-aligned Zend
   chunk base.
3. A second producer/consumer pair discloses `zval_ptr_dtor` in a 16-byte cookie. Its
   low 21 bits are `0x112930`, matching the Alpine 8.4.26 build.
4. A final 369 KiB multipart body plants a forged HashTable whose `pDestructor` is
   `zif_system`. PHP's cleanup path calls it; the command writes the nonce, `id`, the
   `print-flag` hash, and the flag to the accepted socket. nginx forwards the bytes.

The exact source-level root cause in the parser is the PoC author's claim. This task
reproduced the behavior and the preconditions, not an independent root cause. The
session-upload-progress path is necessary: with `session.upload_progress.enabled=Off`
the producer no longer OOMs and the chain stops at the first stage (mutation A).

### Evidence

| artifact | sha256 | shows |
|---|---|---|
| `evidence/run-nginx4/final.response.body` | `0abf54b04c5de67fe9bdb33db40cc6a5c4c062f220680e6677425ff627e2d6c5` | fatal, nonce `6c9f411478b49788`, `uid=0`, `print-flag` hash, flag |
| `evidence/run-nginx4/final.json` | `459c02bc9d3d1d9c7057cd4554e2616be3605434e8ffa2ff5d12454fe8580ecc` | all three markers true; body/raw hashes |
| `evidence/run-nginx4/heap.json` | `ff0ec07854216bd3e705794a50397c56db98aef53516d57dfe5deb74a82f3133` | heap `0x783213000000`, one 256-byte consumer cookie |
| `evidence/run-nginx4/code.json` | `f7d510e47251c0025402840ac2e4ff873896837a86a3895aafc11326fa903cee` | code `0x5b5334112930`, low21 `0x112930` |
| `evidence/run-nginx4/ORACLE.txt` | `360a3a3fc9e795b49e66353383a4620fac0e0d1d63063981a32bd786604897b6` | independent image read: flag and binary hash match the body |
| `evidence/run-verify-20261026T103257Z-2/final.response.body` | `6eebf82b2e62e253c71d30087a59b19dc5d8bce4419e31fa366d674ba3c264fa` | second verified run, nonce `29b2878a6f9356b5` |
| `evidence/php-run-nginx4.log` | `bcfbab4879615eae44aabf7e736ba282fd34fa89bff96d5fde0b437e15323cf9` | the final POST and the 139 exit |
| `evidence/nginx-run-nginx4.log` | `b2eac40172a9ce0ccba8547c1758d1b1ca8edeaa819b1a9f3d448de99fd3d971` | the client-side requests as seen by the proxy |
| `evidence/lab.pcap` | `170f8eecdc0631c89ef025e92db2379be9259c43af19a556633cffaed21a8ae6` | nginx-side capture of the runs |

The full list, including the failed attempts, is `evidence/MANIFEST.sha256`.

### Reproduction

```sh
make lab-up
make attack RUN_ID=repro1
```

A verified run prints `"execution_proof_verified": true` and the body contains the
fresh nonce, `uid=`, the `print-flag` hash, and the flag. Because both leaks are races
and the callback can miss, run it up to 8 times; `make verify` automates that bound.

Observed in this session: four verified successes in ten base-config attempts (40%),
including the `make verify` run. The upstream writeup reports 7/10. The rate
is environment- and scheduler-dependent; treat a single miss as a race, not a
regression, and use the verification skill's retries.

### Impact

- Code execution as the web worker. In this lab, root inside the container; in a
  hardened deployment, the service account.
- Disclosure of the synthetic flag and any file the worker can read.
- The successful callback also kills the CLI server parent (F2), so the exploit is
  one-shot per container in this configuration.

### Remediation and retest

- The real fix is a patched PHP build. 8.4.26 is the tested version; this lab has no
  vendor patch and asserts no CVE.
- `session.upload_progress.enabled=Off` blocks the chain at the producer while the
  benign baseline still passes (mutation A in `make verify`). That is a mitigation,
  not a fix.
- Do not expose the PHP CLI server directly; note that the nginx proxy did **not**
  prevent the bug, it only shaped the worker reuse.
- Limit request body size and multipart part counts, and alert on memory-limit
  exhaustion.
- Retest with `make verify`; when a patched PHP image exists, replace the `php` base
  and require mutation A and the live attack to fail while the baseline passes.

### Disclosure

No CVE is asserted. The upstream repository is a public CTF PoC; the operator should
coordinate with the PHP security team before making a real-target or vendor claim.
The flag in this lab is synthetic and the container is disposable.

---

## F2 — Successful callback crashes the CLI server parent

**Status:** observed; reproducible as part of F1.
**Severity:** Medium (availability, after code execution).

The response with the nonce and flag is delivered, then the PHP CLI server parent
exits with signal 11 (`Exited (139)`). Because the parent is PID 1, the container
stops and nginx returns 502 until it is restarted. The forged cleanup path runs the
command and then the process dies; the exact crash point is not instrumented.

Evidence: `evidence/php-exit.txt` (`6f4e7679...`), `evidence/php-run-nginx4.log`
(`bcfbab48...`), `evidence/run-nginx4/final.response.body` (`0abf54b0...`).

Impact: availability loss and one-shot exploitation. A real deployment needs a
supervisor/restart policy and should treat a post-request 139 as a compromise signal.
The container's default restart policy is `no`; `make verify` restarts it explicitly.
