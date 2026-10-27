<!--
Handoff note: this file is the rewritten brief for repo initialization + Task 001.
It supersedes the original chat prompt. Read this file first, then CONSTITUTION.md
once it exists. Do not commit or push; the operator commits.
Status: executed 2026-10-26; see tasks/0001-stealmybitcoin/HANDOFF.md.
This file preserves the brief as issued.
Structure note: decisions/, ledger/, and references/ are task-scoped as of ADR 0003;
the target shape below is the original layout. See
tasks/0001-stealmybitcoin/decisions/0003-task-scoped-records.md.
-->

# PROMPT — Repo init + Task 001: "Steal My Bitcoin", blind lab

You are the lead operator for a long-running red-team / pentest research repo.
The operator is an authorized pentester. This repo is their historical log, not a
product. Two kinds of work exist here: `lab` (reproducible, offline, no real target)
and `engagement` (a real, authorized target). Task 001 is `lab` only.

Your job in this session is Phase 0 through Phase 8 for Task 001. Deep, not wide.
One task, finished to evidence, beats four tasks started.

---

## 1. Non-negotiables

1. Do not run `git init`, commit, push, or add submodules. Leave the tree for the operator.
2. Task 001 touches no real host, domain, wallet, key, or third-party API. All network
   traffic stays on a Docker `internal` network with no route out.
3. The solution is sealed. Do not read `README.md` from the source repo before Phase 5.
   Record its sha256 first, in `tasks/0001-stealmybitcoin/HYPOTHESES.md`. If you have
   already read it, say so immediately and stop; the experiment is contaminated.
4. Every claim cites an artifact path and its sha256. No artifact, no finding.
5. The agent that produces a finding never verifies it. Use a separate verifier, on a
   different model if one is available.
6. Real-target work needs a signed `SCOPE.md` (targets, window, rules of engagement,
   kill switch, data handling). That gate exists from Phase 0 but is not exercised here.
7. `make down` removes containers, networks, volumes, captured secrets, and traces.

If any instruction conflicts with these, these win. Say so instead of improvising.

---

## 2. Phase 0 — Constitution

Write `CONSTITUTION.md`, one page maximum. It encodes the seven rules above plus:

- the evidence schema (artifact, hash, timestamp, command, operator, verifier);
- the severity method (technical severity plus business impact, not CVSS alone);
- the handoff contract (a fresh agent with only the repo can continue);
- the definition of done for any task;
- the rule that empty scaffolding is forbidden.

This file governs every future task. Do not pad it. Do not restate it elsewhere.

---

## 3. Phase 1 — Minimal skeleton

Create only files Task 001 actually uses. No empty directories. No placeholder docs.
No tool you do not run. No dependency you do not pin. Target shape:

```
README.md                  index, how to use the repo, task list
CONSTITUTION.md            Phase 0 output
tasks/
  0001-stealmybitcoin/
    PROMPT.md              this brief, copied in
    SCOPE.md               lab scope and explicit non-targets
    HYPOTHESES.md          pre-registration + sealed-solution hash
    THREAT-MODEL.md        asset, adversary, trust boundary, fidelity criteria
    lab/                   compose.yaml, Dockerfiles, configs, seed data
    specimen/              the PoC file or a fetch-by-hash script + provenance
    evidence/              MANIFEST.sha256, traces, pcaps, command log
    findings/FINDINGS.md
    detections/            sigma/, yara/, runtime rules
    verify/                SKILL.md, tests, Makefile targets
    HANDOFF.md
    RETRO.md
references/
  README.md                provenance schema; no unsourced material
  github/                  index of pinned repos, added only after Phase 5
  markdowns/               sourced notes, never the solution before Phase 5
kit/                       reusable wrappers, only for tools actually used
ledger/
  FINDINGS.md
  ATTACK-COVERAGE.md
  TOOL-EFFICACY.md
swarm/roles.md
decisions/                 one short ADR per real choice
```

Rule: a directory exists because a task put a file in it, not because a diagram had a box.
After Task 001 passes, extract what was actually reused into `tasks/_TEMPLATE/` with a
README marking mandatory vs optional. Not before.

---

## 4. Phase 2 — Specimen and blind triage

Acquire the PoC into `specimen/` or fetch it by pinned hash. Record source URL, retrieval
time, size, sha256, and license status (the upstream repo declares no license, so prefer
reference-by-hash over vendoring; if you vendor, note the takedown path).

Before executing anything, write `HYPOTHESES.md`:

- at least five falsifiable hypotheses: what it targets, how it observes, how it
  substitutes, how it exfiltrates, what it persists, what it needs from the environment;
- for each, the observation that would prove it wrong, and a confidence;
- one predicted loss mechanism and one predicted detection signal;
- the sealed sha256 of the upstream README, with the unseal date/time.

Then triage, static first:

- file type, strings, imports, AST or disassembly, embedded addresses/URLs/keys;
- `semgrep` (auto plus one custom taint rule for source-to-sink), CodeQL for Python;
- `gitleaks` and `trufflehog` on the repo and the specimen;
- `osv-scanner` and `pip-audit` on any dependency manifest; `trivy fs`; `checkov` and
  `hadolint` on the lab files;
- a capability inventory that separates what the code can do from what the author says
  it does. The gap between those two is a finding.

Then dynamic, inside the sealed lab only:

- Python audit hooks (`sys.addaudithook`) for `open`, `socket.connect`, `subprocess.Popen`,
  `ctypes.dlopen`; `strace -ff`; pcap; clipboard state transitions, not just final values;
- process tree, DNS/SNI, file writes, and every outbound attempt.

Write `TRIAGE.md`: capability inventory, IOCs, ATT&CK mapping, and an explicit unknowns list.

---

## 5. Phase 3 — Lab

`THREAT-MODEL.md` first: protected asset (a simulated balance), adversary capability,
trust boundary, the exact failure to reproduce, and the fidelity criteria. If the real
incident's transaction data is available, pin it and compare mechanics; if not, state
that fidelity is mechanism-level and numbers are not comparable.

Compose services: victim (Xvfb + clipboard manager + wallet CLI + browser), chain
(`bitcoin-cli -regtest` or `anvil` at a pinned block), DNS sinkhole, telemetry
(pcap + audit + Falco), and a local attacker endpoint.

Invariants, enforced in the compose file, not in prose:

- `internal: true` network, no published ports except a localhost-only control port;
- images pinned by digest; non-root user; `read_only`; `cap_drop: [ALL]`;
  `security_opt: [no-new-privileges:true]`; pids and memory limits;
- seeded randomness, known starting balance, pinned block height, fixed clock where possible;
- negative control: benign copy/paste and a normal payment must not trigger the path,
  and must be recorded as baseline;
- one command each: `make lab-up`, `make lab-reset`, `make lab-down`;
- the lab boots offline after the first image pull.

---

## 6. Phase 4 — Attack, in the lab

Reproduce the theft against the simulated victim. Measure the loss from the chain, not
from the PoC's logs: intended address, substituted address, amount, tx id, block height.
Reconcile the difference.

Capture in `evidence/`: `MANIFEST.sha256`, a timestamped command log, pcap, syscall trace,
clipboard timeline, and screen captures. Verify the manifest with `sha256sum -c`.

`findings/FINDINGS.md`: one finding per behavior, each with severity rationale,
reproduction, impact, evidence hashes, and a retest status. If the PoC does not work,
that is a finding; document the gap and the environment mismatch.

---

## 7. Phase 5 — Defense, then unseal

- Write YARA for the specimen, Sigma for the log-visible process/network/file events,
  and a runtime rule (Falco or auditd) for what Sigma cannot see. If there is a web
  surface, add a nuclei template.
- Prove true positive on the attack trace and true negative on the benign baseline, in a
  real backend. A rule that has never fired is not a detection.
- Patch the victim or the wallet UX. Retest: the attack must fail and the benign path
  must still pass.
- Only now unseal the README. Score every hypothesis hit/miss/partial in `RETRO.md`,
  name what you got wrong and why, and record what the writeup knew that the artifact
  did not. Do not skip this; it is the learning loop.

---

## 8. Phase 6 — Verification skill

`verify/SKILL.md` plus `make verify`: one command, deterministic, under five minutes,
no network. It asserts observable behavior (funds diverted or not, clipboard changed or
not, detection fired or not), never internals.

Mutation test it: break the vulnerable behavior, then break the benign path. `make verify`
must fail for the right reason each time. Record both outputs in `verify/`.

Register the skill in `ledger/` with what it covers and what it cannot.

---

## 9. Phase 7 — Oracles and independent review

Write `ORACLES.md`. For each oracle: what it proves, how it could be faked, actual result.

- Ledger: the chain, not the tool, reports the loss.
- Mutation: the verification skill fails when the flaw is removed.
- Detection: TP on attack, TN on baseline, second backend agrees.
- Blind re-run: a verifier on another model, given only `evidence/` and `findings/`,
  reaches or refutes the conclusion.
- Reproducibility: a clean host, offline, same hash manifest.
- Cross-tool: semgrep, CodeQL, and manual review agree on the sink; trivy and osv agree
  on the dependency finding.
- Cold start: a fresh agent with only the repo can restate the task, the state, and the
  next action. No chat history, no oral tradition.

Record disagreement verbatim. Then red-team the evidence: can someone reproduce it
without your reasoning?

---

## 10. Phase 8 — Handoff and ledger

- `HANDOFF.md`: current state, what works, what does not, next three actions, open
  questions, file map, and the exact command to resume.
- `decisions/NNNN-*.md`: one short ADR per real choice, with the alternative rejected.
- `ledger/FINDINGS.md`, `ledger/ATTACK-COVERAGE.md`, and `ledger/TOOL-EFFICACY.md`.
  For tool efficacy, seed ground truth in the lab (three secrets, two known-vulnerable
  deps, one deliberate sink, one benign lookalike) and record what each tool caught,
  missed, and falsely flagged.
- `references/README.md`: provenance schema (URL, retrieval date, sha256, license, why
  kept, reliability grade). Add the source repo as a pinned reference only after
  unsealing; index first, submodule later, only if the operator approves.

---

## 11. Swarm

Write `swarm/roles.md`, then `tasks/0001-stealmybitcoin/SWARM.md` for this task's actual
composition. Every role must own a distinct artifact and catch a distinct failure mode;
delete any role that does not.

- Advisor: scope, hypotheses, stop condition. Never executes, never edits findings.
- Operator: runs the lab and the attack.
- Instrumenter: telemetry and evidence integrity.
- Verifier: independent model, sees artifacts only, cannot see the producer's reasoning.
- Adversary: attacks the lab's fidelity and the evidence chain, not the victim.
- Historian: handoff, ledger, ADRs.

No self-grading. No role-play without an artifact. Record budget, stop condition, and
what each agent was denied. For inspiration, extract patterns only from ARTEX
(session/state machine), Cairn (search plus validation), and CyberStrikeAI (lazy skill
registry, role separation). Do not vendor them.

---

## 12. Definition of done

- [ ] `docker compose up` works from a clean checkout, offline, under ten minutes, no manual steps
- [ ] negative control passes and is recorded
- [ ] attack reproduces; loss measured from the chain and reconciled in `FINDINGS.md`
- [ ] `sha256sum -c evidence/MANIFEST.sha256` passes
- [ ] Sigma/YARA/runtime rule: TP on attack, TN on baseline, second backend agrees
- [ ] patch plus retest: attack fails, benign passes
- [ ] `make verify` green; mutation makes it red for the right reason
- [ ] README unsealed only after predictions; every hypothesis scored in `RETRO.md`
- [ ] blind verifier agrees or its disagreement is recorded
- [ ] cold-start agent can continue from the repo alone
- [ ] no secrets, no egress, teardown verified
- [ ] no commit, no push, no submodule

---

## 13. Decisions that stay with the operator

Do not silently choose these. Pick a default, mark it in `decisions/`, and flag it:

- chain and simulator: Bitcoin regtest, EVM anvil, or both (decide after triage proves which);
- detection backend: Elastic, Splunk free, or OpenSearch;
- specimen handling: reference by hash or vendor with provenance;
- timebox for Task 001;
- severity framework: CVSS plus business impact, or a custom matrix;
- references: pinned archives or submodules;
- whether any output is ever published;
- `[OPERATOR INPUT]` the real incident's transaction id and address, or "unknown".

---

## 14. Do not

- Do not read the upstream writeup before Phase 5.
- Do not commit, push, init git, or add a submodule.
- Do not enable egress, use real keys, real addresses, or real endpoints.
- Do not run every starter tool. Run the ones that can produce a verifiable signal for
  this task, and record the ones you skipped with the reason.
- Do not vendor ARTEX, Cairn, or CyberStrikeAI.
- Do not create empty directories, placeholder documentation, or a tool wrapper you never run.
- Do not let the producer verify its own work.
- Do not write a finding without an artifact hash.
- Do not call anything "secure" or "exploitable" without an oracle that could have said no.
