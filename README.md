# Red-team log

Historical log of authorized security research. Two work classes, never mixed:

- `lab`: reproducible, offline, synthetic target. No real host, key, or third party.
- `engagement`: a real target under a signed scope. Not present in this repo yet.

Read `CONSTITUTION.md` before adding a task. Read `tasks/<id>/HANDOFF.md` before
continuing one. The upstream solution for a task stays sealed until its predictions are
written and hashed.

## Tasks

| id | name | class | status | oracle |
|---|---|---|---|---|
| 0001 | Steal My Bitcoin (PHP 8.4.26 RCE) | lab | verified in the lab; `make verify` passes | independent flag read + nonce/hash + mutation |

**Task 0001 is not a bitcoin stealer.** The upstream name is the CTF's theme. The
specimen is a memory-corruption chain in PHP 8.4.26's multipart/session upload-progress
parsing, ending in `zif_system`. The lab asset is a synthetic flag. See
`tasks/0001-stealmybitcoin/THREAT-MODEL.md`. A plain-language + technical walkthrough
is in `tasks/0001-stealmybitcoin/OVERVIEW.md`.

## Quick start

```sh
make lab-up
make attack RUN_ID=manual1   # repeat up to ~8; the leaks and callback are races
make verify                  # static fingerprint + baseline + live attack + 2 mutations
make lab-down
```

`make attack` runs the specimen in the attacker container, which shares nginx's network
namespace. There is no published port and the lab network is `internal: true`.

`make verify` is the gate: it extracts the CLI binary and checks the `0x112930`
fingerprint, runs a benign baseline, retries the live attack, and proves the check has
teeth with two mutations. Last report: `tasks/0001-stealmybitcoin/verify/VERIFY-REPORT.json`
(sha256 `303f6402…`), all five checks true.

## Verified evidence

- Primary: `tasks/0001-stealmybitcoin/evidence/run-nginx4` — nonce `6c9f411478b49788`,
  `uid=0`, `print-flag` sha256 `47593914…`, flag `FLAG{task001_php8426_lab_9f3c2a}`.
- Four verified bodies from separate runs; `evidence/MANIFEST.sha256` (131 files, sha256
  `8278a7f8…`) verifies with `sha256sum -c`.
- The independent review is `tasks/0001-stealmybitcoin/verify/VERIFIER-REPORT.md`:
  it agrees on the core and refutes nothing, but time-boxed the flag re-run, seal
  re-check, and cold start. The finding is not labeled fully independently verified.

## Layout

```
CONSTITUTION.md          rules that govern every task
SKILL-ARCHITECTURE.md    layered skill model (method → task skill → generator/maintainer)
.dsh/skills/verify-task-001/   registered pstack-style verification skill
  SKILL.md
  features/
tasks/0001-stealmybitcoin/
  iterations/            fail-fast attack log, refined prompt, code history, harness,
    versions/            preserved v1/v2/v3 harnesses and experiments
  OVERVIEW.md            plain-language + technical walkthrough
  SCAN-CHECKLIST.md      scan signals, retry budgets, stop rules
  TABLES.md              the table appendix (result, reviews, scans, math)
  summary.html           the visual dossier (high-level → story → technical)
  PROMPT.md              the rewritten brief
  SCOPE.md               lab scope and explicit non-targets
  HYPOTHESES.md          pre-registration and the sealed hash
  THREAT-MODEL.md        asset, adversary, boundary, fidelity criteria
  specimen/              pinned PoC by hash, sealed upstream README
  lab/                   php + nginx compose, images, probe, rejected Apache attempt
  evidence/              raw HTTP, pcap, logs, manifest, run notes
  findings/              F1 RCE and F2 crash with artifact hashes
  detections/            YARA, Sigma, replay tests, and the log-source gap
  verify/                baseline, run_verify, mutations, SKILL, last report
  HANDOFF.md             state for the next agent
  RETRO.md               hypothesis scoring and the blind/unsealed split
  ORACLES.md             what can say the result is right
  SWARM.md               task composition
  decisions/             ADRs (0001 superseded, 0002 CLI+nginx, 0003 task scope)
  ledger/                findings, ATT&CK coverage, tool efficacy
  references/github/     pinned upstream and provenance
swarm/roles.md           cross-task role definitions
```

## Evidence rule

Every claim in a finding cites a path and a sha256. Run `sha256sum -c` on the manifest
before trusting a result. A result that cannot be reproduced from the repo is a draft.

## Tooling

The task used Docker Compose, `readelf`, YARA, and a Python Sigma-selection replay.
The starter scanner stack (gitleaks, semgrep, CodeQL, osv, pip-audit, trivy, checkov,
nuclei, ZAP, Burp) is deliberately not claimed: this finding is in the PHP runtime, not
the app or dependencies. `tasks/0001-stealmybitcoin/ledger/TOOL-EFFICACY.md` records each skipped tool and why,
plus the fixture plan for a measured pass.

## Commits

The operator commits. Agents do not run `git init`, commit, push, or add submodules.
