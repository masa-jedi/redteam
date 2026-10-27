# Skill architecture — pentest verification, layered like pstack

Status: proposal + current state, 2026-10-26. Cross-task. Read this before creating a
new agent skill or promoting a task's `verify/` directory.

Paths are repo-root-relative unless noted. Paths written as `verify/`, `evidence/`,
`findings/`, or `detections/` refer to `tasks/0001-stealmybitcoin/`.

## Decision

Neither a single general “pentesting” mega-skill nor a single attack-vector skill.
Use **three layers plus a vector middle layer**:

1. **Method / guardrails** — general, small, stable. Scope, authorization, lab-first,
   threat model, pre-registration, evidence standard, negative controls, independent
   verifier, retro, maintenance.
2. **Task skill** — specific, executable, evidence-producing. The exact lab/target,
   fingerprint, requests, success/failure modes, detection, patch, limits, and a
   `features/` map.
3. **Meta loop** — the generator that writes the task skill, the maintainer that keeps
   it honest, and `reflect`/`correct` that turn misses into rules.

The **vector skill** is a middle layer: a reusable pattern (`php-multipart-session-rce`),
not a target’s evidence. The task skill is the instance.

This is pstack’s design. `create-verification-skill` is the general generator;
`.dsh/skills/verify-<app>/` is the specific artifact; `maintain-verification-skill` is
the general loop; the `principle-*` skills are the general principles. The generator is
reusable; the artifact is executed.

## What pstack teaches

- **Interview the repo, not the user.** The specific skill is grounded in the actual
  lab; no placeholders.
- **The generated skill is for the next agent, read cold.** It is the handoff, not a
  chat summary.
- **The feature map is the coverage contract.** A proof that drives one convenient
  entry point is incomplete when the map lists others.
- **Prove the generated skill end-to-end.** Launch, doctor, drive one feature, capture
  evidence, clean up, confirm the evidence still exists. A skill that never ran is a
  draft.
- **Stand-in gaps must be listed.** If the proof ran in a container, list every setup
  step the container did that the real target will not.
- **Never weaken the journey to pass.** A race that misses is a race that misses.
- **Offer the maintenance loop.** The map drifts; the maintainer keeps it honest.

## The layers

| Layer | Contents | Where | Test |
|---|---|---|---|
| **Method / guardrails** | Scope, authorization, lab-first, threat model, pre-registration, evidence, negative controls, independent verifier, retro, maintenance | `CONSTITUTION.md`, `SCOPE.md`, `SCAN-CHECKLIST.md`, `OVERVIEW.md`; optionally a one-page `PENTEST-METHOD.md` | A cold agent can state the scope, the evidence standard, and the stop conditions |
| **Task skill** | Exact launch, doctor, drive, evidence, cleanup, helpers; the fingerprint; the race; the mutations; the limits; `features/` | `.dsh/skills/verify-task-001/` (registered) + `tasks/0001/verify/` (task source) | A cold agent runs it and gets the flag/nonce/hash; the mutations fail correctly |
| **Vector skill** | The pattern: primitive, preconditions, deployment shape, detection idea; no target evidence | `.dsh/skills/php-multipart-session-rce/` — later | It helps a new lab start; it does not claim the old evidence |
| **Generator** | Interview the lab; generate the task skill + features; prove it | `.dsh/skills/create-pentest-skill/` | It produces a new task skill without copying Task 001’s flag/fingerprint |
| **Maintainer** | Re-run after a version/lab change; update the fingerprint/features; check the evidence | `.dsh/skills/maintain-pentest-skill/` | After a version bump, it changes the fingerprint and re-proves |
| **Learning** | `reflect`/`correct`; the task `RETRO`/`HANDOFF`/ledger | Existing pstack skills + the repo | A repeated mistake becomes a check, lint, or feature-map gotcha |

## What goes where

| Content | Layer |
|---|---|
| “No scope, no packet”; lab-first; evidence standard; producer/verifier split | Method |
| The exact `make lab-up`; the 0x112930 fingerprint; the 9-request chain; the flag; the nonce; the pcap | Task skill |
| The PHP multipart/session primitive; the 4-worker/nginx precondition; the detection idea | Vector skill (later) |
| The interview questions and the generated-skill sections | Generator |
| The drift check after a PHP image/lab change | Maintainer |
| The finding, evidence hashes, retro, handoff | Task docs (`findings/`, `evidence/`, `RETRO.md`, `HANDOFF.md`) |

## The vector layer

Defer it until **two or three tasks** use the same primitive. With one task, a vector
skill generalizes from a single case and becomes a writeup. When it is time, the vector
skill contains:

- the primitive and the preconditions (not the flag);
- the deployment shapes that make it reachable;
- the detection idea and the false-positive modes;
- the lab pattern (what the stand-in must reproduce);
- the evidence standard for the class.

The task skill still owns the exact build, fingerprint, flag, and run.

## Current state

- `make verify` passes **5/5**; `verify/VERIFY-REPORT.json` sha256 `303f6402…`.
- `evidence/MANIFEST.sha256` verifies **131/131**, sha256 `8278a7f8…`.
- Primary evidence: `evidence/run-nginx4/final.response.body` sha256 `0abf54b0…`.
- The task-local skill is `tasks/0001-stealmybitcoin/verify/SKILL.md`; it has frontmatter
  `name: verify-task-001`, the five checks, the mutation pitfalls, the last run, the
  limits, and the maintenance note.
- **Built in the loop:** `.dsh/skills/verify-task-001/SKILL.md` and `features/` now
  exist and register; the task-local `verify/SKILL.md` points to the registered source.
  The loop log and refined prompt are `iterations/ATTACK-LOG.md` and
  `iterations/ATTACK-PROMPT.md`.
- **Final capture:** `evidence/run-loop-final`, nonce `27c3a0c37fe49e43`,
  `execution_proof_verified: true`, flag `FLAG{task001_php8426_lab_9f3c2a}`.
- **Proof:** `make verify` 5/5; live pass on attempt 3 of
  `run-verify-20261027T091403Z-2`; the report is `verify/VERIFY-REPORT.json`.
- **Still open:** the generator, the maintainer, the vector skill (after 2–3 tasks), and
  the independent C3/C8/C9 re-run.
- The independent verifier is **partial**: GLM-5.3 agreed on the core, refuted nothing,
  and time-boxed C3 (flag oracle), C8 (sealed hash), and C9 (cold start). The detection is partial (Sigma is a response-body
  surrogate because `log_errors=Off`). The tool-efficacy pass was not run. No CVE is
  asserted.
- The task is **lab-only**. No real host, wallet, or key was touched.

## Target layout

```
.dsh/skills/
  verify-task-001/
    SKILL.md
    features/
      README.md
      exploit-chain.md
      benign-baseline.md
      fingerprint.md
      detection.md
      patch-crash.md
  create-pentest-skill/
    SKILL.md
  maintain-pentest-skill/
    SKILL.md
```

The task-local `tasks/0001-stealmybitcoin/verify/SKILL.md` stays as the source until
the registered copy exists; then it becomes a pointer to the registered skill (avoid
two drifting sources).

## The specific skill: `verify-task-001`

The pstack six sections, grounded in this lab:

- **Launch** — `make lab-up`; the php/nginx healthchecks; the evidence directory; the
  first pull needs network, then offline.
- **Doctor** — `make lab-status` plus the static `readelf` fingerprint
  (`zval_ptr_dtor` low21 `0x112930`); the scope check.
- **Drive** — `make verify` (five checks); `make attack RUN_ID=…` (one research run);
  `verify/baseline.py` (benign control). The real HTTP path through nginx, not a mock.
- **Evidence** — `verify/VERIFY-REPORT.json`; `evidence/MANIFEST.sha256`;
  `evidence/run-nginx4/ORACLE.txt`; the body with the nonce, `uid=0`, hash, flag; the
  pcap and logs. Proof survives cleanup.
- **Cleanup** — `make lab-down`; the evidence is a bind mount and survives; do not
  delete it. One lab per repo; do not double-drive the same project name.
- **Helpers** — `verify/run_verify.py`, `verify/baseline.py`, `lab/probe.py`; show the
  invocations and the expected outputs.
- **Limits / stand-in** — the race (~4/10 here, 7/10 upstream); the lab is a stand-in
  for a real target; the real build/worker/proxy are unknown; the `parse_target`
  allowlist includes the real domain but the scope forbids it; C3/C8/C9 (flag oracle, sealed hash, cold start); the detection
  surrogate; no CVE.
- **Maintenance** — after a PHP/lab change, update the fingerprint and re-run; the
  maintainer.

### Feature map

Each file uses the four H2s: `Sub-features`, `How to get to it (user POV)`,
`Driving it with <harness>`, `Gotchas`.

| Feature | User POV | Drive | Evidence | Gotcha |
|---|---|---|---|---|
| `exploit-chain` | Attacker sends the 9-request chain through nginx | `make attack` / `make verify` | Flag, nonce, `uid=0`, binary hash | Race; four workers; nginx; exact build |
| `benign-baseline` | Normal visitor GETs the version page and uploads a small form | `verify/baseline.py` | No OOM, 32-byte cookie, no flag | Does not prove the exploit |
| `fingerprint` | The CLI binary is the right Alpine 8.4.26 build | `readelf` on the image CLI | `zval_ptr_dtor` low21 `0x112930` | Wrong image fails before the attack |
| `detection` | A rule fires on the attack and not the benign input | YARA/Sigma replay | `detections/TEST.txt`, `REPLAY.txt` | `log_errors=Off`; the Sigma source is a surrogate |
| `patch-crash` | Upload progress off blocks the attack; a broken page fails the baseline; success kills the parent | `make verify` mutations | `VERIFY-REPORT.json`; `php-exit.txt` | The mutation must fail for the right reason |

## The generator: `create-pentest-skill`

Mirror pstack’s interview, with the pentest gates added:

- **Surface** — the attack surface: endpoint, parser, chain, deployment shape.
- **Run** — `make lab-up`; the lab only; the scope gate.
- **Drive** — `make verify` / `make attack` / `baseline.py`; the real HTTP path.
- **Observe** — nonce, flag, hash, pcap, logs, exit codes.
- **Isolate** — internal network, no egress, one lab; no real target.
- **Gates** — signed `SCOPE.md` for a real target; pre-registration/seal; negative
  controls; independent verifier; no placeholders; prove before handing over.

The generator writes `.dsh/skills/verify-<task>/SKILL.md` and `features/`; it does not
write a generic “how to hack” guide.

## The maintainer

After a PHP/lab/version change:

1. Re-run the Doctor (fingerprint/health).
2. Re-run `make verify`; update the report hash and the last run.
3. Update the feature map’s `Gotchas`; add a feature if the surface changed.
4. Re-check the stand-in gaps and the scope.
5. Record the change in `ledger/` and `HANDOFF.md`.

## Next actions

1. Create `.dsh/skills/verify-task-001/SKILL.md` from the task-local skill, using the
   six pstack sections. Leave a pointer in the task-local copy.
2. Add `features/README.md` and the five feature files with the four H2s.
3. Add the one-read-only Doctor and the Cleanup/Helpers commands to the skill.
4. Prove it cold: `make lab-up`; follow the skill; `make verify`; `make lab-down`;
   confirm the evidence still exists; record the last run in the skill.
5. Write `create-pentest-skill` and `maintain-pentest-skill`.
6. Wait for 2–3 tasks before extracting `php-multipart-session-rce` as a vector skill.
7. Update `README.md`, `HANDOFF.md`, and the ledger; no commit or push. **Done in this
   loop; the generator/maintainer/vector remain future work.**

## Open decisions (operator)

- **Skill root:** `.dsh/skills/` (pstack convention) vs another project-local path. The
  task-local copy is not a registered skill today.
- **General method:** a root `PENTEST-METHOD.md` vs a `pentest-method` skill. The
  `CONSTITUTION.md`/`SCOPE.md`/`SCAN-CHECKLIST.md` already carry most of it.
- **Naming:** `verify-task-001` (pstack `verify-<app>` style) vs `pentest-0001`.
- **Source of truth:** registered skill vs task-local copy. Do not maintain two
  divergent copies; one points to the other.
- **Vector trigger:** after 2–3 tasks on the same primitive; not now.
- **Real-target scope:** lab only for now; a real target needs a signed `SCOPE.md` and
  its own verification run. Do not point the lab skill at a real host.

## Do not

- Build one mega “pentesting” skill; it becomes a checklist and cannot be proven.
- Make one attack vector the whole system; it overfits and becomes a writeup.
- Put the target’s flag/nonce/fingerprint in the vector skill.
- Point `make verify` at a real host; it is built for the lab.
- Weaken the race or the mutation to make the skill pass; report the miss.
- Use 1,000 agents for a deterministic scan; the scan is a for-loop.
- Commit, push, or `git init`.

## Cold start

1. Read `README.md`, this file, `CONSTITUTION.md`, `SCOPE.md`, and
   `tasks/0001-stealmybitcoin/HANDOFF.md`.
2. `make lab-up`; `make verify`; `make lab-down`.
3. Read the task-local `verify/SKILL.md`, then the feature map if it exists.
4. The next action is in “Next actions” above; do not invent a new general skill before
   the specific one is registered and proven.
