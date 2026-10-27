# Scope — Task 001 (lab only)

## Classification

`lab`. This is a reproduction of a public CTF artifact against a target the operator
builds and owns. It is not an engagement. It does not test the upstream challenge site,
the upstream author, or any third party.

## Target

- `http://127.0.0.1:8080/php-version.php` served by the local nginx proxy in front of
  the PHP 8.4.26 CLI server (`php:8.4.26-fpm-alpine3.23`, four workers); config in `lab/`.
- Container network `task001_lab`, `internal: true`. No published port except a
  loopback bind for the operator and the PoC.
- Synthetic asset: a random flag at `/flag`, readable by the web user, printed by
  `/usr/local/bin/print-flag`. No real key, wallet, seed, or credential exists anywhere
  in the lab.

## Explicit non-targets

- `stealmybitcoin.com` and every public host. The specimen's `parse_target()` permits
  that host; this task never passes it.
- Any real PHP deployment, any third-party API, any DNS name outside the sinkhole.
- Any wallet, chain, or private key. The challenge name is a theme, not an asset. The
  specimen is a PHP memory-corruption exploit.

## Authorization basis

Self-owned lab. The specimen is a public repository with no declared license; it is kept
by hash and provenance, not redistributed. No real-target authorization is claimed or
implied by this file.

## Window and kill switch

- Window: one session, 2026-10-26.
- Kill switch: `make lab-down` removes containers, network, volumes, and captures.
- If the PoC attempts a host other than 127.0.0.1/localhost, stop and record it as a
  scope violation, do not run it.

## Data handling

Raw HTTP may contain the synthetic flag and container-local paths. It stays in
`evidence/`. No real secret is ever placed in the lab. Pcaps and traces are kept only
for this task and are removed by `make lab-down` if they are inside volumes.

## Success

The flag is recovered by the exploit, and the recovery is proven by two independent
oracles: the nonce/hash markers in the HTTP response, and the container's flag value
compared outside the exploit path. A failed reproduction is also a valid result if the
gap is measured and attributed.
