# Scan triage and iteration checklist — Task 001

**Scope first.** This is for authorized testing. `CONSTITUTION.md` requires a signed
`SCOPE.md` for real-target work; the Task 001 scope is lab-only. A scan can be allowed
where an exploit is not. Do not bypass a WAF, a `429`, or a rate limit.

**One rule:** `scan != attack`. A scan is 2–5 light requests. A confirmation is the OOM
exploit, which can kill the worker/container. A version header is a candidate, not a
confirmation.

---

## Matrix A — what to look for in a scan

| # | Check | Request / observation | Positive signal | Confidence | What it means | Next action |
|---|---|---|---|---|---|---|
| A1 | Scope | Is the target in the signed scope? | Host, path, method, rate, window allowed | — | No scope, no packet | Stop if not allowed |
| A2 | Final origin | `GET /`, follow at most one redirect | Final host/TLS/`Server` stable | — | Avoid scanning a CDN/redirect chain by accident | Record the final URL |
| A3 | PHP version header | `GET /` and `GET /php-version.php` | `X-Powered-By: PHP/8.4.26` | Medium | Version candidate; not the exact build | Go to A4 |
| A4 | Version endpoint | `GET /php-version.php` | 200, body starts `PHP 8.4.26` | Medium-high | The `.php` endpoint exists, so the parser can be reached | Candidate; lab next |
| A5 | Root is static | `GET /`; `GET /index.php` | 200 HTML at `/`, 404 at `/index.php`, no `Set-Cookie` | Low / negative | The static path does not initialize PHP; `/` alone is not a trigger | Do not conclude “unexploitable”; try A4 |
| A6 | Proxy / CDN | Headers on A3/A4 | `Server: nginx`, `Via`, `cf-ray`, `x-sucuri` | Medium | Proxy behavior and rate-limit surface | Adjust concurrency |
| A7 | Worker count hint | 5× `GET /php-version.php`; if the body prints `PID:` | PID varies across requests | Medium | Multi-worker hint; the leak needs a reusable pool | Strengthen candidate |
| A8 | Session/upload hint | One **small** multipart POST with `PHP_SESSION_UPLOAD_PROGRESS` and a tiny file; no OOM payload | `Set-Cookie: PHPSESSID` length 32 | Medium | Session upload-progress may be on; required for the OOM path | Candidate; lab next |
| A9 | Direct CLI server | `Server:` header | `PHP 8.4.26 Development Server` | Medium | CLI server exposed directly, not behind nginx | Different deployment; lab |
| A10 | Proxy transport | Two GETs on one keep-alive connection | Both 200, `Connection: keep-alive` | Low-medium | Proxy/pipelining behavior; transport is plausible | Note only |
| A11 | WAF / rate limit | Response to A2–A4 | 403/429/JS challenge | — | Stop or back off; do not bypass | Stop |
| A12 | Exact build | Not visible remotely | `zval_ptr_dtor` low21 `0x112930` only via the code leak | High only in the lab | The exploit’s build precondition | Lab, not scan |

**What the scan cannot see:** the exact Alpine build, `session.upload_progress`, the
four-worker pool, the 128 MiB limit, or the heap. Those are the exploit’s preconditions.
A scan produces **candidates**; the lab or an authorized exploit confirms.

---

## Matrix B — iteration / retry budget

| Stage | What you are doing | Budget | Fresh state? | Stop / backoff |
|---|---|---|---|---|
| B1 | Baseline GET | 1 request | No | 1 retry only on timeout/5xx; no retry on 4xx |
| B2 | Endpoint probe | 1–2 requests | No | If 404, mark static-only; no exploit |
| B3 | PID sample | 5 requests | No | If PID is constant, lower confidence; no retry loop |
| B4 | Small upload probe | 1 request | No | If no cookie, lower confidence; do **not** send the 249 KiB producer |
| B5 | Lab confirmation (`make verify`) | 8 attempts | Restart the container after a crash | Stop on success; the lab is disposable |
| B6 | Authorized production confirmation | 1–2 planned; 3–5 absolute max with a written scope | Check target health before/after; a restart resets the heap | Stop on success, target-down, WAF/429, or 3 consecutive same-mode misses |
| B7 | Same target, repeated tries | Use B5/B6 budget, not a loop | If the container restarted, the heap state resets; if not, the worker pool persists | Do not blind-retry; re-validate the fingerprint/lab first |
| B8 | 1,000 targets | 3 requests each for the scan; **do not** run 1,000 exploit attempts | — | Scan → dedupe → lab → authorized sample |

### The same-target rule

The exploit is a race. A retry can be justified, but the budget is **risk-bound**, not
just probability-bound:

- Each attempt sends the OOM producer. That is a resource-exhaustion event, not a GET.
- On success, the PHP CLI server parent can exit 139; the target may need a restart.
- If the target restarts, the heap state resets; the next attempt is a genuinely new
  state. If it does not restart, the worker pool persists; a retry may hit a different
  worker.
- **3 consecutive misses with the same failure mode** (heap miss, code miss, or callback
  miss) means stop and re-validate the build, worker count, upload-progress setting, and
  lab. Do not turn a race into a brute-force DoS.

---

## The math

Per-attempt success `p` varies: about **0.4** in our lab, **0.7** upstream. Probability
of at least one success in `n` independent attempts:

`1 - (1 - p)^n`

| p | 1 | 2 | 3 | 5 | 8 | 10 |
|---|---|---|---|---|---|---|
| 0.4 | 40% | 64% | 78% | 92% | 98% | 99.4% |
| 0.7 | 70% | 91% | 97% | 99.8% | 99.99% | 99.999% |

Expected attempts: `1/p` ≈ 2.5 at p=0.4, 1.4 at p=0.7.

The lab uses 8 because it is disposable. A production target uses 1–2 because the
attempt is intrusive and the scope is the limit, not the probability.

---

## Stop rules

- **403 / 429 / JS challenge / WAF:** stop or honor `Retry-After`; never bypass.
- **Target down or 5xx after an exploit attempt:** stop; report the availability impact.
- **3 consecutive same-mode misses:** stop; re-validate the fingerprint and lab.
- **Success:** stop; capture the nonce, flag/hash, and evidence; do not “verify again.”
- **Scope/RoE limit reached:** stop, regardless of the math.
- **A scan negative:** mark it; do not retry to “make it positive.”
- **A version header:** candidate only; do not call it a confirmed exploit.

---

## What maps to the repo

- `TABLES.md` — the table appendix, including a snapshot of this matrix.
- `OVERVIEW.md` — the plain-language + technical walkthrough, including the T&C.
- `verify/SKILL.md` — the lab’s five checks and the 8-attempt retry policy.
- `findings/FINDINGS.md` — F1 (RCE) and F2 (crash), with evidence hashes.
- `ledger/TOOL-EFFICACY.md` — why the starter scanner stack is the wrong layer.
- `SCOPE.md` / `../../CONSTITUTION.md` — the authorization gate.
- `evidence/run-nginx4` — a verified body; `verify/VERIFY-REPORT.json` — the lab pass.
