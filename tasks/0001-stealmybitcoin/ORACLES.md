# Oracles — Task 001

What can say the result is right, other than the producer. Each row names how the
oracle could lie and what actually happened. A claim without a row here is a draft.

| oracle | what it proves | how it could lie | result |
|---|---|---|---|
| **Independent flag read** | The flag in the HTTP body is the flag in the built victim image, read outside the exploit path. | The image could have been rebuilt after the run; the `ORACLE.txt` records the image ID and timestamp. | **pass (producer-run).** `docker run --rm --entrypoint cat task001-php:local /flag` = `FLAG{task001_php8426_lab_9f3c2a}`, image `sha256:f9b5ae80…`, body matches. `run-nginx4/ORACLE.txt` sha256 `360a3a3f…`. The GLM verifier time-boxed C3 and did not re-run it. |
| **Binary hash** | The command executed the exact `print-flag` script, not a lookalike. | The hash could be copied from the source into a forged body. | **pass.** Body hash `47593914…` equals `sha256sum lab/php/print-flag` and the image's copy. The verifier confirmed the source hash; the in-image copy is producer-run only. |
| **Fresh nonce** | The response is from this run, not a replay or cache. | A nonce could be guessed or copied after the fact; the PoC generates 16 hex chars microseconds before the request. | **pass.** Four distinct nonces across four verified bodies: `6c9f411478b49788`, `29b2878a6f9356b5`, `dc4630df4a1cabb8`, `91f5eefe641036e3`. |
| **Byte integrity** | The evidence files are what the JSON says they are. | The JSON and files could both be edited. | **pass.** `sha256sum -c evidence/MANIFEST.sha256` 131/131 OK; the manifest hash `8278a7f8…`; each `final.json` body/raw hash recomputes. |
| **Heap alignment** | The leaked value is a Zend 2 MiB chunk base, not a random pointer. | A lucky aligned value could pass the filter. | **pass.** `0x783213000000`, `0x745eebc00000`; both `& 0x1fffff == 0`; one 256-byte consumer cookie each. |
| **Code fingerprint** | The leaked function is `zval_ptr_dtor` from the Alpine build the PoC was calibrated for. | The low21 filter is a hint; another code pointer could share it by chance (1/2^21). | **pass.** `0x5b5334112930`, `0x5a4dac912930`; static `readelf` on the image's CLI: `0x712930`. |
| **Mutation A** | The upload-progress path is necessary; removing it stops the attack at the producer. | A generic failure (bad image, broken proxy) could also stop the attack. | **pass.** Baseline still passes; the exact error is `producer did not return PHP 8.4.26 HTTP 200 OOM`; mutation B separately proves a broken app fails the baseline. |
| **Mutation B** | The benign baseline has teeth. | A failure for the wrong reason would also "pass" this check. | **pass.** The bad page returns 500, `get_status_200=false`, exit 1; the restore makes it pass again. |
| **Detection replay** | A rule fires on the attack and stays quiet on benign input. | A rule written after seeing the line can overfit. | **partial.** YARA: TP on the specimen, TN on the app. Sigma selection: 1 hit on the attack body, 0 on the benign body; `grep` agrees. The body is a surrogate because the CLI SAPI has `log_errors=Off`; no runtime rule, no access-log correlation. |
| **Blind re-run** | An independent model, given only the artifacts and the claims, reaches or refutes the conclusion. | The verifier could trust the producer's files without checking. | **partial.** GLM-5.3 agreed C1/C2/C4(partial)/C5/C6/C7, refuted nothing, and time-boxed C3/C8/C9. Report: `verify/VERIFIER-REPORT.md`. |
| **Reproducibility** | The chain can be re-run from the repo, not just from one lucky capture. | The container and worker state could be left over from the original. | **pass.** Four verified bodies from separate runs; `make verify` rebuilds/restarts and passes; the lab is disposable. |
| **Cold start** | A fresh agent with only the repo can continue. | The agent could be reading this chat. | **partial.** The verifier did not finish the handoff read; it called the task reconstructable from the artifacts it read. A dedicated fresh-agent read remains open. |
| **Cross-tool** | A second tool sees the same binary/config fact. | Both tools share a blind spot. | **partial.** `readelf` on the image CLI confirms `0x112930`; the Debian and Apache builds were rejected by the same check. The scanner stack (semgrep/trivy/gitleaks) was not run against the exploit; see `ledger/TOOL-EFFICACY.md`. |

## The one that could have said no

The mutation is the negative control. Without A, "the attack succeeded" could be a
broken lab that always returns a flag; with A, the same harness that passes on the
vulnerable build must fail when the upload-progress path is removed, and the baseline
must still pass. The independent flag read is the second control: the body's flag is
checked against the image, not against the PoC's own report.

## What is still weak

- The nonce and hash are in the same response as the flag; a compromised PHP worker
  could forge all three. The independent image read is the only check outside that
  path, and it only proves the flag's value, not that the command ran. The `uid=0` and
  `print-flag` hash in the same body are the execution evidence; they are produced by
  the command, so they are not independent of it. A separate runtime canary would
  close this gap; the `/tmp` canary was lost when the container crashed. Record it as
  a known weakness, not as a solved problem.
- The detection backend is a replay, not a live SIEM.
- The independent verifier time-boxed C3 (flag re-run), C8 (seal re-check), and C9
  (cold start). They are open; the producer-run evidence is in `ORACLE.txt` and
  `HYPOTHESES.md`.
- The severity is for the lab; the real-world rate and exposedness are not measured.
