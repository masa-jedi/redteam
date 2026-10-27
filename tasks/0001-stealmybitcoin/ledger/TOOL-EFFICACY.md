# Tool efficacy — Task 001

The starter stack is for code, dependencies, infrastructure, and web templates. The
finding is a memory-corruption bug in the PHP runtime reached by a crafted multipart
body. Most of the stack is the wrong layer; this table records what was run and what
was deliberately skipped, with the reason. It is not a claim that the tools are useless.

| tool | layer | run? | result / reason |
|---|---|---|---|
| gitleaks | secrets in the repo | no | The only secret is the synthetic `FLAG{…}`; scanning it would flag the lab's own dummy. The repo has no credentials; `print-flag` reads `/flag`, it does not embed one. |
| trufflehog | secrets | no | same as gitleaks; no real secret material in the repo. |
| semgrep | app code (PHP/Python) | no | The app is six lines and has no sink. The vulnerability is in the PHP C parser, not the application. A scan of the app cannot see it. |
| CodeQL | compiled/app code | no | No application code of interest; the PHP runtime is out of scope for the lab's CodeQL setup. |
| osv-scanner | dependency manifests | no | The PoC is standard-library Python; the lab has no dependency manifest. No input. |
| pip-audit | Python dependencies | no | same: stdlib only, no `requirements.txt`. |
| trivy | image/OS/config | no | The image is Alpine + PHP 8.4.26 from source; an OS scan finds base-image CVEs, not the parser bug. A `trivy image task001-php:local` run is a next step to quantify the noise. |
| checkov | IaC | no | The compose is hardened (`internal`, `read_only`, `cap_drop: ALL`, `no-new-privileges`, limits). A checkov pass would confirm config, not the finding. |
| hadolint | Dockerfile | no | The Dockerfiles pin base tags but not digests; that is a reproducibility issue to fix separately, not this finding. |
| nuclei | HTTP templates | no | No template exists for this parser bug; the app has one version endpoint. A nuclei tech-detect would only confirm PHP. |
| ZAP | web app | no | The app has no parameters or forms; a baseline scan would report the version page. Wrong layer. |
| Burp | web app | no | Not available in this environment; the same reasoning as ZAP. |

## What would have found it

- The response-body fatal + the anomalous `PHPSESSID` + the OOM burst, correlated.
- A runtime sensor for `print-flag` as a child of the CLI server.
- Not a code/dependency/infra scanner. The readelf fingerprint was the useful static
  check: it confirmed the build, not the exploit.

## The seeded-ground-truth plan (next pass)

To measure rather than reason, add `kit/fixtures/` with three synthetic secrets, two
known-vulnerable dependency versions, one deliberate taint sink, and one benign
lookalike. Run gitleaks/trufflehog, osv/pip-audit, semgrep, and trivy against the
fixtures and record TP/FP per tool. That is deliberately not done in this session; a
fixture built after the fact is easy to overfit.

## Commands for the next pass

```sh
# secrets
docker run --rm -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:latest detect -s /repo
# dependencies (after fixtures)
docker run --rm -v "$PWD:/src" ghcr.io/google/osv-scanner:latest -r /src
# image noise
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image --severity HIGH,CRITICAL task001-php:local
```
