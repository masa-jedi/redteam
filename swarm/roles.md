# Swarm roles

Agents are workers with artifacts, not personas. Every role owns a file and catches a
failure mode the others do not. Delete a role that has neither.

## Roles

| role | owns | must not | catches |
|---|---|---|---|
| **Advisor** | scope, hypothesis register, stop condition, risk call | execute the lab, edit findings | scope creep, unfalsifiable plans, a missing oracle |
| **Operator** | lab bring-up, exploit runs, raw evidence | grade its own result, edit the verifier's report | broken assumptions about the target |
| **Instrumenter** | telemetry, hashes, manifest, reproducibility | interpret a finding without the operator's raw data | evidence that cannot be re-checked |
| **Verifier** | independent claim table, cold-start check | modify files, see the producer's reasoning | self-grading, overclaims, a handoff that only works in chat |
| **Adversary** | falsification pass on the lab and evidence | accept "it worked once" | replay, fabrication, a lab that always returns a flag |
| **Historian** | handoff, ADRs, ledgers, retro | rewrite a failed attempt as a success | context loss between sessions |

## Independence rules

- The producer never verifies. The verifier gets artifacts and claims only, not the
  producer's chain of thought.
- A role's output is a file or a structured report, never a chat assertion.
- The advisor cannot edit the findings; the operator cannot edit the verifier's report.
- Every role records what it was denied, so the next agent can see the constraints.
- No self-grading at the task level: the final "verified" line requires an oracle that
  could have said no (mutation, independent flag, blind re-run).

## Budget and stop

- One session per task unless the operator extends it.
- Stop when: the verification skill passes, the independent report is reconciled, the
  handoff is cold-start complete, and no claim is missing its artifact hash.
- Stop early on: a scope violation, a real-target request without a signed scope, or
  evidence that cannot be reproduced.

## Task 001 composition

Recorded in `tasks/0001-stealmybitcoin/SWARM.md`.
