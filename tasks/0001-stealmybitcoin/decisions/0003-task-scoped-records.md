# ADR 0003 — Task-scoped decisions, ledger, references

Status: accepted, 2026-10-26.

## Context

The first pass put `decisions/`, `ledger/`, and `references/` at the repository root.
Those records are specific to one task: an ADR about this lab, this task's finding
ledger, and the references used to build it. A second task would either collide in the
same directories or need task prefixes everywhere, and a handoff would have to jump out
of the task directory to be complete.

## Options

1. Root directories with `tasks/<id>/` subdirectories inside them. Keeps a global index,
   but the task is not self-contained.
2. **Task-scoped directories**: `tasks/<id>/decisions/`, `tasks/<id>/ledger/`,
   `tasks/<id>/references/`. The task directory is the handoff unit.
3. A database or generated index. Not justified for a file-based historical log.

## Decision

Option 2. The repository root keeps only cross-task material: `CONSTITUTION.md`,
`README.md`, `Makefile`, `PROMPT.md`, and `swarm/` (role definitions). Each task owns
its decisions, ledger, references, evidence, findings, detections, and verification.

## Consequences

- `README.md`, `HANDOFF.md`, and the prompt's original target shape are updated or
  annotated. The prompt is preserved as issued, with a structure note pointing here.
- Future tasks copy the task-scoped pattern; the root does not accumulate per-task
  records.
- A reference or ADR can be sealed and reviewed with its task without touching another
  task's history.
- The paths inside the moved files are relative to the task (for example
  `ledger/TOOL-EFFICACY.md`, `lab/attempts/apache/`, `verify/VERIFIER-REPORT.md`), so
  they remain correct after the move.
