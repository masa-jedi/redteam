# Constitution

This repo is an evidence system for authorized security research. It is not a notes
folder and not a portfolio. Two classes of work exist and never mix:

- `lab`: reproducible, offline, synthetic target. No real host, key, or third party.
- `engagement`: a real target under a signed scope. Out of bounds until `SCOPE.md`
  exists, is signed, and names the target, window, rules of engagement, kill switch,
  and data handling.

## Non-negotiables

1. No commit, push, `git init`, or submodule unless the operator asks in that turn.
2. A lab run has no route to the internet. `internal: true` network, sinkholed DNS.
3. The solution stays sealed until the predictions are written and hashed.
4. Every claim cites an artifact path and its sha256. No artifact, no finding.
5. The producer never verifies its own work. A separate verifier gets artifacts only.
6. Real-target work requires a signed scope. No scope, no packets.
7. Teardown removes containers, networks, volumes, captured secrets, and traces.

## Evidence schema

Every finding row carries: id, claim, artifact path, sha256, command, timestamp (UTC),
producer, verifier, confidence, retest status. A claim without a hash is a draft, not a
finding. Raw HTTP, pcaps, and traces are stored, not summarized away.

## Severity

Technical severity (exploitability, prerequisites, blast radius) plus business impact
(asset value, detectability, recoverability). CVSS is an input, not the answer. A finding
that requires a misconfiguration is labeled as such, not inflated.

## Handoff contract

A fresh agent with only this repo can restate the task, the current state, and the next
action, and can run `make verify` without chat history. If it cannot, the task is not done.

## Definition of done

Attack reproduced and measured by an independent oracle; detection proven true-positive
and true-negative; fix retested; evidence manifest verifies; mutation test fails for the
right reason; blind verifier agrees or its disagreement is recorded; teardown works.

## Structure rule

A directory exists because a task put a file in it. No empty scaffolding, no placeholder
docs, no tool wrapper that was never run. Extract a template only after a task proves it.
