# Handoff — Task 001

Last updated: 2026-10-26T11:16Z.
Status: **lab verified**; `make verify` passes all five checks; independent verifier
completed (core agreed; C3/C8/C9 time-boxed); YARA + a Sigma surrogate replay done;
runtime/access-log correlation and the tool-efficacy pass still open.

## Read first

1. `../../CONSTITUTION.md`
2. `OVERVIEW.md` — plain-language + technical walkthrough
3. `SCAN-CHECKLIST.md` — scan signals, retry budgets, stop rules
4. `../../SKILL-ARCHITECTURE.md` — layered skill model and promotion steps
5. `../../.dsh/skills/verify-task-001/SKILL.md` — the registered verification skill
6. `iterations/ATTACK-LOG.md` + `iterations/ATTACK-PROMPT.md` +
   `iterations/CODE-CHANGES.md` + `iterations/versions/README.md` — loop, prompt,
   code progression, preserved harnesses
7. This file
8. `findings/FINDINGS.md`
9. `ORACLES.md`
10. `verify/SKILL.md` — task-local pointer to the registered skill
11. `RETRO.md` — it records what was blind and what came from the unsealed writeup.

## State

- Lab: `php` (PHP 8.4.26 CLI server from `php:8.4.26-fpm-alpine3.23`, four workers,
  `read_only`, tmpfs `/tmp`, 1 GiB) + `nginx:1.27-alpine` proxy on an `internal`
  network. The attacker and telemetry share nginx's network namespace.
- The full chain is verified six times. The newest rerun capture is
  `evidence/run-loop-final-v2`, nonce `f5051bc60195565b`,
  `execution_proof_verified: true`, flag `FLAG{task001_php8426_lab_9f3c2a}`; the pstack
  proof `make verify` passed 5/5 (`run-verify-20261027T094909Z-2`). The first loop
  capture is `run-loop-final`, nonce `27c3a0c37fe49e43`. Primary earlier:
  `evidence/run-nginx4`, nonce `6c9f411478b49788`, body sha256 `0abf54b0…`.
- Harness versions are preserved in `iterations/versions/`; the v1/v2 failure modes
  were reproduced in the rerun. Others:
  `run-verify-20261026T103257Z-2` (`29b2878a…`), `run-verify-20261026T103741Z-1`
  (`91f5eefe…`, from `make verify`), and `run-verify-extra-success-…`
  (`dc4630df…`, a base success produced while a mutation mount was invalid).
- `make verify` last passed at `2026-10-26T10:38:42Z`; report
  `verify/VERIFY-REPORT.json` sha256 `303f6402…`; all five checks true.
- The PHP container exits 139 (SIGSEGV) after a successful callback. The response is
  delivered before the crash; `make verify` restarts the service.
- Independent verifier: delegated to GLM-5.3 (`glm-5.3-abliterated`,
  `thought_level=max`), task
  `node:delegated-task:command%3Amcp%3A6a18aad6-32e4-4823-9716-5df5aefb6e5b%3Adelegate-task%3Atask001-verifier-round-1`.
  Its report is `verify/VERIFIER-REPORT.md`. It agrees C1/C2/C4(partial)/C5/C6/C7 and
  refutes nothing; C3 (flag re-run), C8 (seal), and C9 (cold start) were time-boxed
  unclear. The producer-run `ORACLE.txt` covers C3; a second-party re-run stays open.
- The upstream README was sealed (`a2897d3b…`) and unsealed at 10:26 after the blind
  attempt. The nginx/CLI architecture came from its lab section; the final success is
  a reproduction of the documented lab, not a blind discovery. `RETRO.md` says so.

## What works

- `make lab-up`, `make lab-down`, `make lab-status`.
- `make attack RUN_ID=...` (repeat up to eight; the leaks and callback are races).
- `make verify` (static fingerprint, baseline, live attack, mutation A, mutation B).
- `make verify-mutation` (the two mutations only, faster).

## What does not work / is not done

- YARA and a Sigma-selection replay are done (`detections/README.md`). The lab's CLI
  SAPI has `log_errors=Off`, so the Sigma rule was replayed on the response body, not a
  PHP error log; the runtime rule and the access-log `$request_length` correlation are
  not done.
- The tool-efficacy pass (gitleaks/semgrep/trivy/osv/pip-audit/checkov/nuclei/ZAP)
  was not run. `ledger/TOOL-EFFICACY.md` records why each is the wrong layer or has
  no input, plus the commands to run later.
- The verifier did not re-run C3 (independent flag), C8 (sealed hash), or C9 (cold
  start). Its report records them as unclear, not refuted.
- A patched PHP build does not exist in this lab; the only mitigation tested is
  mutation A (`session.upload_progress=Off`), which is not a vendor fix.
- The `/tmp/flag-access.log` canary was lost when the container crashed. A persistent
  `/runtime` mount would fix that; do not claim the canary as evidence.

## Next three actions

1. Re-run the verifier's C3/C8/C9 items if a second-party check is required, or record
   the producer-run `ORACLE.txt` limitation. The report is `verify/VERIFIER-REPORT.md`;
   do not edit it to fit the finding.
2. Add the runtime rule/persistent canary and the access-log `$request_length`
   correlation; re-run the Sigma rule on a `log_errors=On` build. The current YARA and
   Sigma surrogate results are in `detections/README.md`.
3. Run the tool-efficacy pass on the repo and the built image; record what the
   scanners miss about a PHP-core memory-corruption bug. After that, and only after
   the verifier is reconciled, extract `tasks/_TEMPLATE/` from this task.

## Resume commands

```sh
make lab-up
make verify                 # ~1-2 min; retries the race up to 8
make attack RUN_ID=manual2  # one research run, writes evidence/run-manual2
make lab-down
```

If the `php` container is `Exited (139)`, `make lab-up` or
`docker compose -f tasks/0001-stealmybitcoin/lab/compose.yaml up -d php` restarts it.

## File map

```
SKILL-ARCHITECTURE.md (repo root)     layered skill model and promotion steps
CONSTITUTION.md                       repo rules
tasks/0001-stealmybitcoin/
  OVERVIEW.md                         plain-language + technical overview
  SCAN-CHECKLIST.md                   scan signals, retry budgets, stop rules
  TABLES.md                           table appendix (result, reviews, scans, math)
  summary.html                        visual dossier (high-level → story → technical)
  PROMPT.md                           the rewritten brief
  SCOPE.md  HYPOTHESES.md             scope and pre-registration
  THREAT-MODEL.md                     asset, adversary, boundary, fidelity
  specimen/                           pinned PoC, sealed README, seal hash
  lab/compose.yaml                    php + nginx + telemetry + attacker
  lab/php/                            CLI server image, app, print-flag, flag
  lab/nginx/                          proxy image and config
  lab/attempts/apache/                rejected Apache path, kept as evidence
  evidence/                           runs, logs, pcap, MANIFEST, RUN-NOTES
  findings/FINDINGS.md                F1 RCE, F2 crash
  detections/                         YARA, Sigma, replay tests, limits
  verify/                             baseline, run_verify, mutations, SKILL, reports
  HANDOFF.md  RETRO.md  ORACLES.md
  decisions/                          ADR 0001 superseded, 0002 CLI+nginx, 0003 task scope
  ledger/                             findings, ATT&CK coverage, tool efficacy
  references/github/README.md         pinned upstream, provenance, seal
swarm/roles.md                        cross-task role definitions
```

## Seal record

- Upstream commit `bd137b9881734ed3ee922d853c606ccf0e515db7`.
- Specimen sha256 `eed0a0d6…`; sealed README sha256 `a2897d3b…`.
- Unsealed 2026-10-26T10:26Z after the Apache attempt and before the nginx lab; the
  fresh fetch matched the sealed hash.
- The writeup is not vendored. Do not treat this task as blind again.

## Do not

- Do not point the PoC at `stealmybitcoin.com` or any real host. `parse_target()`
  allows it; the scope does not.
- Do not commit or push; the operator commits.
- Do not trust a single attack miss; the heap and callback are races.
- Do not call the `/tmp` canary evidence; it is gone.
- Do not claim a CVE or a real-target compromise from this lab.
