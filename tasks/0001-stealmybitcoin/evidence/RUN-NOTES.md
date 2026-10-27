# Evidence runs — what each directory is

All paths are relative to this directory. The authoritative hashes are in
`MANIFEST.sha256`; `sha256sum -c MANIFEST.sha256` must pass before any finding is
trusted.

| run | config | result |
|---|---|---|
| `run-heap1` | CLI server directly, no nginx | Producer OOM, connection reset, `RemoteDisconnected`. The 8 consumers were lost. Server-class failure, not a payload failure. |
| `probe-oom.log`, `apache-run-apache1.log` | Apache mod_php built on Alpine | Producer 200 + OOM, then `zend_mm_heap corrupted`, child SIGABRT, reset. Archived as `lab/attempts/apache/`. |
| `run-nginx1` | nginx → CLI server, four workers | Both leaks: heap `0x783213000000`, code `0x5b5334112930` (low21 `0x112930`). Final callback missed (only the OOM fatal). |
| `run-nginx2` | same | Heap stage missed: no 256-byte cookie. Expected race failure. |
| `run-nginx3` | same | Both leaks, final callback missed. Expected race failure. |
| `run-nginx4` | same | **Verified.** Nonce `6c9f411478b49788`, `uid=0`, `print-flag` sha256 `475939…`, flag `FLAG{task001_php8426_lab_9f3c2a}`. Body sha256 `0abf54…`. |
| `run-verify-20261026T103257Z-2` | same, from `make verify` | **Verified.** Nonce `29b2878a6f9356b5`, body sha256 `6eebf8…`. |
| `run-verify-extra-success-20261026T103441Z` | same | **Verified**, but produced while the mutation mount was a directory, so the ini was not applied. It is a base success, not a mutation success. Kept for honesty; do not cite it as a mutation. |
| `run-mutmanual1` | `session.upload_progress=Off` correctly mounted | Producer no longer OOMs; the attack stops at the heap stage with `producer did not return PHP 8.4.26 HTTP 200 OOM`. This is mutation A working. |
| `run-verify-mut-progress-*` | same, from `make verify` | Mutation A evidence after the mount fix. |
| `run-verify-mut-limit-*` | invalid mount (directory, ini not loaded) | Do not use as mutation evidence; superseded. |

The PHP container **exits 139 (SIGSEGV)** after a successful callback: the response is
delivered, then the CLI server parent dies. `php-exit.txt` is the `docker compose ps -a`
snapshot. `make verify` restarts the service between attempts.

`lab.pcap` is the nginx-side capture (client ↔ nginx) for the runs; the nginx access and
PHP logs are saved beside it. The canary `/tmp/flag-access.log` was lost when the
container crashed; the response body plus the independent image read in `ORACLE.txt`
replace it.
