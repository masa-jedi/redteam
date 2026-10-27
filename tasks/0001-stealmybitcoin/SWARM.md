# Swarm composition — Task 001

| role | agent | artifacts | denied | result |
|---|---|---|---|---|
| Advisor | main agent, before execution | `SCOPE.md`, `HYPOTHESES.md`, `THREAT-MODEL.md` | no lab execution while writing hypotheses | produced H1–H8; H2 later falsified |
| Operator | main agent | `lab/`, `evidence/run-*`, `probe.py` | no editing the verifier report | four verified runs; one Apache dead end |
| Instrumenter | main agent | `evidence/MANIFEST.sha256`, logs, pcap, `ORACLE.txt` | no interpreting a finding without the raw file | 131-file manifest; 131/131 OK |
| Verifier | GLM-5.3 (`glm-5.3-abliterated`, thought_level=max), task `node:delegated-task:command%3Amcp%3A6a18aad6-32e4-4823-9716-5df5aefb6e5b%3Adelegate-task%3Atask001-verifier-round-1` | `verify/VERIFIER-REPORT.md` | no file edits; artifacts only; no producer reasoning | completed; core agreed; C3/C8/C9 time-boxed; no refutations |
| Adversary | the verifier's C10 + the producer's mutation pass | `ORACLES.md` mutation rows | no accepting "one lucky run" | mutation A/B pass; the independent replay is pending |
| Historian | main agent | `HANDOFF.md`, `RETRO.md`, `decisions/`, `ledger/` | no rewriting the Apache failure | done except the verifier reconciliation |

## What the swarm caught

- The advisor's H2 (Apache) was wrong; the operator's own evidence falsified it, and the
  historian recorded the miss instead of deleting it.
- The producer's first mutation A was invalid: a relative mount became a directory and
  the ini never loaded. The verifier pass and the `php -i` check caught it; the mutation
  was rewritten to `../verify/...` with mode 0644.
- The verifier agreed on the core and named the producer-run flag oracle as not
  re-run; no refutations were produced. Its time-box on C3/C8/C9 is recorded in
  `verify/VERIFIER-REPORT.md`, not hidden.

## What was not used

- No separate "planner" loop or role-play chat. The advisor was a phase, not a second
  agent, because the task was bounded.
- No cross-provider code review of the exploit. The binary and the lab are the objects;
  the verifier reviews the claims and evidence.
- No ARTEX/Cairn/CyberStrikeAI code. Only the role-separation and artifact-handoff
  pattern is borrowed; nothing is vendored.
