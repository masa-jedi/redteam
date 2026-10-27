---
name: verify-task-001
description: Verify the Task 001 PHP 8.4.26 lab. Checks the CLI binary fingerprint, a benign baseline, the full RCE against the lab, and two mutations. Use after changing the lab, the app, the PHP/nginx config, or the specimen.
---

# verify-task-001

> Task-local pointer. The registered source is
> `../../../.dsh/skills/verify-task-001/SKILL.md`; the layering is in
> `../../../SKILL-ARCHITECTURE.md`. Use the registered skill for cold starts.

## When to use

- After any change to `tasks/0001-stealmybitcoin/lab/`, the app, the nginx config,
  or the PHP base image.
- After a change to the specimen or the exploit wrapper.
- Before handing the task to another agent or claiming the finding still reproduces.

## One command

```sh
make verify
```

It needs Docker and the host's `readelf`. It starts the lab itself. No external
network is used after the base images are present.

## What it drives

The real path: attacker container → nginx → PHP CLI server (four workers). It does
not call the PHP server directly, because the proxy is part of the exploit's worker
reuse.

## The five checks

1. **Static calibration.** Extract `/usr/local/bin/php` from `task001-php:local` and
   read `zval_ptr_dtor`. The low 21 bits must be `0x112930`. A wrong PHP image fails
   here before any attack, which is the lesson from the Debian and Apache attempts.
2. **Benign baseline.** `verify/baseline.py` sends a version GET, a small multipart
   upload with upload-progress fields, and a follow-up GET. It must see status 200,
   `X-Powered-By: PHP/8.4.26`, no memory-limit fatal, no non-32-byte cookie, and no
   flag. This is the negative control: a broken page must not look "secure".
3. **Live attack.** Runs the specimen up to eight times. A verified run must have all
   three markers, matching body/raw hashes, a 2 MiB-aligned heap candidate, a code
   candidate with low21 `0x112930`, and the independently read flag and `print-flag`
   hash in the body. The exploit is a race; a single miss is not a regression.
4. **Mutation A — remove the upload-progress path.** Mounts a `99-mutation.ini` with
   `session.upload_progress.enabled=Off`. The benign baseline must still pass, the
   attack must not verify, and it must stop at the producer with
   `producer did not return PHP 8.4.26 HTTP 200 OOM`.
5. **Mutation B — break the benign page.** Mounts a page that returns 500. The benign
   baseline must fail. This proves the baseline check has teeth.

The script writes `verify/VERIFY-REPORT.json` with every check and its detail.

## Mutation pitfalls (learned the hard way)

- Compose resolves a relative bind-mount path in an **override** file against the
  **first** compose file's directory, not the override's. Use `../verify/...` from
  `lab/compose.yaml`, or Docker silently creates a directory at the target and PHP
  never reads the ini.
- The PHP container runs as root with `cap_drop: ALL`. Root cannot override file
  permissions without `CAP_DAC_OVERRIDE`, so mounted ini files must be mode `0644`.
  A `0600` file is unreadable even to root.
- `USE_ZEND_ALLOC=0` disables the Zend allocator and therefore the memory limit. It
  makes the producer return the version page with no OOM; it is a control, not a fix.
- Raising `max_input_vars` changes the OOM path. The intended lab keeps the default.

## Last run

`2026-10-26T10:38:42Z`: all five checks pass. Static `0x712930` / low21 `0x112930`;
baseline pass; live attack success on attempt 2 (`run-verify-20261026T103741Z-1`,
nonce `91f5eefe641036e3`, heap `0x745eebc00000`, code `0x5a4dac912930`); mutation A
pass (`producer did not return … OOM`); mutation B pass. Report:
`verify/VERIFY-REPORT.json`, sha256 `303f6402…`.

## What it cannot tell you

- Whether PHP 8.4.26 is vulnerable outside this Alpine CLI build. The fingerprint and
  the heap calibration are build-specific.
- Whether the real-world service is exposed. The lab proves the chain against this
  deployment, not against a production host.
- The exploit's exact success probability. It is a race; the observed rate in this
  session was about 4/10, while the upstream writeup reports 7/10.
- Anything about persistence, lateral movement, or credential access. This task stops
  at the flag and the crash.
- Detection coverage. The detection rules live in `detections/`; this skill verifies
  the exploit path, not a SIEM deployment.

## Maintenance

- If the PHP base image changes, update the expected low21 in `run_verify.py` and
  `HYPOTHESES.md`, then re-run. Do not silently accept a new fingerprint.
- If the app changes, update `verify/baseline.py` only for behavior you intend; keep
  the no-OOM/no-flag asserts.
- If the mutation mount changes, re-check the effective ini inside the container with
  `php -i` before trusting a pass.
- Register the skill in `ledger/` and keep the last report hash in `HANDOFF.md`.
