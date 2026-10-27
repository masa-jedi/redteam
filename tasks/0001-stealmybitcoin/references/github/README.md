# GitHub references

Pinned, hashed, and added only after the task's blind phase. A submodule is not added
without the operator's approval.

| id | repo | commit | retrieved | sha256 of specimen | license | why kept | reliability |
|---|---|---|---|---|---|---|---|
| ref-0001 | KillaBoi/StealMyBitcoin-PoC | `bd137b9881734ed3ee922d853c606ccf0e515db7` | 2026-10-26 | `eed0a0d670f9d85539ec7f272a0a42e8bde7080f50c6918efcf14caca9ce82f0` | none declared | the specimen under test | B (primary artifact; narrative is sealed then unsealed) |

## Seal and unseal

- Sealed upstream README sha256:
  `a2897d3be8ec407fb473e4f466b8b365f7a3ae62f175239c39fc163e9745286d`.
- Stored as `tasks/0001-stealmybitcoin/specimen/sealed/upstream-README.md.sealed`.
- Unsealed at 2026-10-26T10:26Z after the blind attempt; a fresh fetch of the pinned
  commit matched the sealed hash.
- The writeup is **not vendored**. Its lab section is the source of the CLI+nginx
  architecture and the 7/10 success rate; the exploit chain is the specimen.
- No license is declared upstream. Keep the specimen by hash and provenance; if the
  operator redistributes the file, record the takedown path. A submodule would not
  change the license question.

## What is not imported

ARTEX, Cairn, and CyberStrikeAI are pattern references only (role separation, state
machine, lazy skill registry). No code is vendored. The Docker base images
(`php:8.4.26-fpm-alpine3.23`, `nginx:1.27-alpine`, `python:3.12-alpine`,
`alpine:3.23`) are dependencies, not references; pin them by digest if the operator
wants a fully reproducible build.
