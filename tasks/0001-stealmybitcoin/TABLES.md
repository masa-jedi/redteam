# Tables — Task 001

A snapshot of the tables used in this session. Canonical sources: `SCAN-CHECKLIST.md`
(scan matrix and retry policy), `OVERVIEW.md` (lab/result/agents), `findings/FINDINGS.md`
(evidence), `verify/SKILL.md` (five checks), `ORACLES.md` (oracle results). If a table
here and a canonical file disagree, the canonical file wins.

---

## 1. Did we succeed?

| question | answer |
|---|---|
| Did the lab RCE work? | **Yes.** Four verified bodies, all with the flag and a fresh nonce. Primary: `evidence/run-nginx4`. Verify run: `run-verify-20261026T103741Z-1`. |
| Did we attack the real site? | **No.** Out of scope. No real host, wallet, or key was touched. |
| Was it blind? | **No, not the final success.** The blind phase produced the OOM and rejected two server classes; the CLI+nginx design came from the unsealed writeup. `RETRO.md` records the split. |
| Is it reliable? | **No, it is a race.** About 4/10 base attempts here; the writeup reports 7/10. `make verify` retries up to 8. |
| Is it independently verified? | **Partially.** The flag/byte oracles are independent of the exploit path; the model review agreed on the core but time-boxed C3/C8/C9. |
| Is it detected? | **Partially.** YARA TP/TN; the Sigma selection replayed TP/TN on the response body; no live error-log or runtime rule. |
| Is there a CVE? | **No claim.** The lab reproduces the PoC; a real disclosure needs coordination. |

## 2. `make verify` — five checks

| check | result |
|---|---|
| static calibration | `zval_ptr_dtor=0x712930`, low21 `0x112930` |
| benign baseline | pass (no OOM, no anomalous cookie, no flag) |
| live attack | verified on attempt 2, `run-verify-20261026T103741Z-1` |
| mutation A — upload progress off | attack stops at the producer; baseline still passes |
| mutation B — broken page | baseline correctly fails |

`verify/VERIFY-REPORT.json` sha256 `303f6402…`; all five true.

## 3. Key evidence

| artifact | sha256 | shows |
|---|---|---|
| `evidence/run-nginx4/final.response.body` | `0abf54b04c5de67fe9bdb33db40cc6a5c4c062f220680e6677425ff627e2d6c5` | nonce `6c9f411478b49788`, `uid=0`, `print-flag` hash, flag |
| `evidence/run-nginx4/final.json` | `459c02bc9d3d1d9c7057cd4554e2616be3605434e8ffa2ff5d12454fe8580ecc` | all three markers true; body/raw hashes |
| `evidence/run-nginx4/heap.json` | `ff0ec07854216bd3e705794a50397c56db98aef53516d57dfe5deb74a82f3133` | heap `0x783213000000`; one 256-byte cookie |
| `evidence/run-nginx4/code.json` | `f7d510e47251c0025402840ac2e4ff873896837a86a3895aafc11326fa903cee` | code `0x5b5334112930`; low21 `0x112930` |
| `evidence/run-nginx4/ORACLE.txt` | `360a3a3fc9e795b49e66353383a4620fac0e0d1d63063981a32bd786604897b6` | independent image read: flag and hash |
| `evidence/MANIFEST.sha256` | `8278a7f85dfe66f82568ab7e83b90c78a85e8ba34898e331399b4027d6b6597b` | 131 files, 131/131 OK |
| `verify/VERIFY-REPORT.json` | `303f640225380a380d74f950812e1f678f57968b1cf866a98d841e374e4f4cef` | five checks true |

---

## 4. First tweet review

| tweet claim | verdict | correction / evidence |
|---|---|---|
| `stealmybitcoin.com` “(php2shell)” challenge | label | The upstream artifact calls it the **Steal My Bitcoin PHP 8.4.26 CTF**. `php2shell` is a community nickname, not the repo name. |
| “everyone … calls the bug unexploitable and overhyped” | **half wrong** | The bug **is exploitable** in the calibrated deployment; four verified bodies. It is not generic: it needs the Alpine CLI build, four workers, upload progress, 128M, nginx. “Overhyped” is a judgment; “unexploitable” is false for the lab. |
| “did you even try to solve it?” | rhetorical, but fair | We did. The blind phase produced the OOM and rejected Apache/direct CLI; the CLI+nginx design came from the unsealed writeup. See `RETRO.md`. |
| “can be solved in under five hours” | plausible, unmeasured | Our lab reached a verified RCE ~26 minutes after repo init — but only after the unsealed writeup and with the public PoC. The blind phase did not solve it. The live solve time is not in the artifact. |
| “whoever made it slopped it up … wasting time/tokens” | **partly supported**, partly opinion | The writeup admits the recovered WIF did **not** derive the advertised prize address; the creator acknowledged it. If the initial static page is real, that is a real deployment flaw. “Slopped” and “wasting tokens” are value judgments. |
| “first ~10 hours … nginx → proxy_pass → php -S → index.html” | architecture correct; timeline unverified | The architecture matches the writeup and `decisions/0002-cli-server-nginx.md`. The `index.html`/10-hour history is **not in the writeup** I have. |
| “without a router, PHP CLI server doesn't initialize PHP for static files, so you can't trigger the multipart parser” | **correct** | PHP 8.4.26 `sapi/cli/php_cli_server.c`, `php_cli_server_dispatch` (lines 2298–2354): non-`.php` sets `is_static_file=1`; `php_cli_server_request_startup()` only if `server->router || !is_static_file`. Static path → `php_cli_server_begin_send_static()`. No request startup → no body parser. |
| “after @LiveOverflow called this out, they updated … `/php-version.php`” | endpoint real; attribution unverified | The endpoint is real and is the writeup/lab target. The writeup credits LiveOverflow for **helping contact the creator** (README lines 2 and 344), not for a public static-file callout. |
| “still a crazy setup, running php's single-threaded development server behind nginx” | **imprecise** | The lab runs `PHP_CLI_SERVER_WORKERS=4`: four processes, each single-threaded. The leak stages rely on that pool. |
| “the exploit works reliably now” | **overstated** | The writeup reports **7/10**; our lab **4/10** base attempts, with a known callback-miss mode. It is a race. |
| “made the challenge go viral … server basically got dosed … barely make a request” | unverified | The repo has 466 stars/70 forks, so attention is real. “DDoSed” and the current live state are not in the artifact; we did not test the live site. A four-worker CLI server is tiny enough that solver traffic alone could look like a DoS. |

## 5. Second tweet review

| claim | verdict | correction |
|---|---|---|
| “The CTF aims to demonstrate that PHP2SHELL is **not** realistically exploitable.” | **inverted / unsupported** | The artifact is a PoC **for** the exploit. The writeup is a working chain, the lab uses `/php-version.php`, and our lab reproduced the RCE four times. If the aim were “not exploitable,” a static page would be consistent with the aim, not a scandal. |
| “closest match nginx → PHP cli-server” | **correct** | Our `decisions/0002-cli-server-nginx.md`, the writeup, and the lab agree. FPM and Apache were the wrong hypotheses. |
| “static index.html rather than index.php” | plausible; unverified from our artifact | The source confirms the mechanism; the writeup uses `php-version.php` and does not document the `index.html`/10-hour timeline. Treat as a snapshot. |
| “intentionally made unexploitable” | **conclusion not supported** | A static page makes **that deployment** unreachable; it does not make the vulnerability unexploitable. Once the `.php` endpoint exists, the chain works. |
| “questioning whether this is a good-faith challenge” | **overreach** | The evidence supports a broken initial deployment and some sloppiness — the WIF admission, the endpoint update. It does not support malice. |
| “my scanner independently confirmed at least PHP 8.2+” | **too coarse** | The response already says `X-Powered-By: PHP/8.4.26`; “at least 8.2+” is weaker. The exploit needs the exact Alpine 8.4.26 build and four-worker deployment. |
| “the challenge is unexploitable / overhyped” | **false for the calibrated deployment** | Four verified bodies; `evidence/run-nginx4`, `verify/VERIFY-REPORT.json`. It is racy and build-specific, not unexploitable. |

---

## 6. Is scanning illegal? — risk factors

**Not legal advice.** The legal hooks are unauthorized access/attempt, not the word
“scan.” Jurisdictions differ (US CFAA, EU Directive 2013/40/EU, UK CMA 1990,
Australia/Canada analogues). Get a scope or use passive data.

| factor | lower risk | higher risk |
|---|---|---|
| Authorization | own assets, signed scope, listed bug bounty | “arbitrary” sites; no scope; ignoring a `security.txt`/contact |
| Method | one GET of a public page; browser-like request | auth bypass, injection payloads, exploit bodies, WAF/rate-limit bypass |
| Impact | no state change; no load | OOM, crash, account lockout, data collection |
| Notice | respects `robots.txt`, ToS, `429`/`Retry-After` | ignores blocks, rotates IPs, hides identity |
| Data | no personal data | collecting personal data → GDPR/CCPA etc. |

## 7. How to tell whether a site is PHP

| signal | reliability | notes |
|---|---|---|
| `X-Powered-By: PHP/8.4.26` | High, if present | Most direct; absent does not mean no PHP |
| `Set-Cookie: PHPSESSID` | High | Default PHP session name; can be renamed |
| `wp-content`, `wp-includes`, `wp-json`, `wp-admin`, `?ver=` | High for WordPress | WordPress is PHP |
| `Set-Cookie: laravel_session`, `XSRF-TOKEN` | High for Laravel/PHP | Framework-specific |
| `Set-Cookie: ci_session` | High for CodeIgniter/PHP | |
| `Set-Cookie: SESS…` / Drupal paths | High for Drupal/PHP | |
| `.php` in URL (`/index.php`, `?page=`) | Medium | Routing/frameworks can hide it |
| `Server: nginx` or `Apache` | None for the language | That is the web server, not PHP |
| `Server: PHP 8.4.26 Development Server` | High | CLI server exposed directly |
| PHP error text (`Fatal error:`, `Warning:`) | Medium-high | Often hidden in production |
| `X-Debug-Token` (Symfony), `Whoops` (Laravel) | Medium-high | Debug pages leak the stack |
| `generator` meta / `robots.txt` / `sitemap.xml` | Medium | CMS hints, not proof |

Passive sources at 1,000 scale: HTTP Archive / BigQuery `httparchive.technologies`,
Wappalyzer, BuiltWith, W3Techs, urlscan.io, Shodan/Censys, Common Crawl.

---

## 8. Cost at 1,000 targets

| phase | requests/target | 1,000 targets | wall time at 50 concurrent | egress | marginal cost |
|---|---|---|---|---|---|
| header + `/php-version.php` scan | 2–3 | 2–3k | ~1–3 min | ~10–50 MB | cents; a $5 VPS-hour is plenty |
| + light behavior triage | 5–10 | 5–10k | ~3–8 min | ~50–200 MB | same |
| full exploit confirmation, one attempt | ~9 | ~9k | ~10–30 min | ~1.6 GB | bandwidth pennies; **risk is the cost** |
| with 3–5 retries | ~27–45 | 27–45k | ~30–90 min | ~5–8 GB | 1,000 OOMs/crashes, one-shot containers |

## 9. Scan vs confirmation

| | scan | confirmation |
|---|---|---|
| what it is | 2–5 GETs/light probes | the 9-request OOM chain |
| target impact | none/low | OOM, possible crash, one-shot container |
| what it proves | a candidate | the exploit |
| authorization | scan scope | explicit exploit scope + owner knowledge |
| scale | 1,000 is feasible | a small authorized sample |
| time | 1–3 min at 50 concurrent | 10–30 min, plus retries/restarts |
| cost | cents | bandwidth cheap; blast radius high |

## 10. Matrix A — scan signals

| # | check | request / observation | positive signal | confidence | what it means | next action |
|---|---|---|---|---|---|---|
| A1 | Scope | is the target in the signed scope? | host/path/method/rate/window allowed | — | no scope, no packet | stop if not allowed |
| A2 | Final origin | `GET /`, one redirect max | final host/TLS/`Server` stable | — | avoid scanning a CDN/redirect chain by accident | record final URL |
| A3 | PHP version header | `GET /`, `GET /php-version.php` | `X-Powered-By: PHP/8.4.26` | Medium | version candidate, not exact build | go to A4 |
| A4 | Version endpoint | `GET /php-version.php` | 200, body starts `PHP 8.4.26` | Medium-high | `.php` endpoint exists; parser reachable | candidate; lab next |
| A5 | Root is static | `GET /`; `GET /index.php` | 200 HTML at `/`, 404 at `/index.php`, no `Set-Cookie` | Low / negative | static path does not initialize PHP; `/` alone is not a trigger | do not conclude “unexploitable”; try A4 |
| A6 | Proxy / CDN | headers on A3/A4 | `Server: nginx`, `Via`, `cf-ray`, `x-sucuri` | Medium | proxy and rate-limit surface | adjust concurrency |
| A7 | Worker count hint | 5× `GET /php-version.php`; if body prints `PID:` | PID varies | Medium | multi-worker hint; leak needs reusable pool | strengthen candidate |
| A8 | Session/upload hint | one **small** multipart POST with `PHP_SESSION_UPLOAD_PROGRESS` and a tiny file; no OOM payload | `Set-Cookie: PHPSESSID` length 32 | Medium | upload-progress may be on | candidate; lab next |
| A9 | Direct CLI server | `Server:` header | `PHP 8.4.26 Development Server` | Medium | CLI server exposed directly, not behind nginx | different deployment; lab |
| A10 | Proxy transport | two GETs on one keep-alive connection | both 200, `Connection: keep-alive` | Low-medium | proxy/pipelining behavior; transport plausible | note only |
| A11 | WAF / rate limit | response to A2–A4 | 403/429/JS challenge | — | stop or back off; never bypass | stop |
| A12 | Exact build | not visible remotely | `zval_ptr_dtor` low21 `0x112930` only via the code leak | High only in lab | exploit’s build precondition | lab, not scan |

## 11. Matrix B — iteration / retry budget

| stage | what you are doing | budget | fresh state? | stop / backoff |
|---|---|---|---|---|
| B1 | Baseline GET | 1 request | No | 1 retry only on timeout/5xx; no retry on 4xx |
| B2 | Endpoint probe | 1–2 requests | No | 404 → mark static-only; no exploit |
| B3 | PID sample | 5 requests | No | constant PID → lower confidence; no retry loop |
| B4 | Small upload probe | 1 request | No | no cookie → lower confidence; never send the 249 KiB producer |
| B5 | Lab confirmation (`make verify`) | 8 attempts | restart the container after a crash | stop on success; the lab is disposable |
| B6 | Authorized production confirmation | **1–2 default**; 3–5 only with an explicit scope and owner agreement | check target health before/after; a restart resets the heap | success, target-down, WAF/429, or 3 consecutive same-mode misses → stop |
| B7 | Same target, repeated tries | use B5/B6 budget, not a loop | if the container restarted, the heap resets; if not, the worker pool persists | do not blind-retry; re-validate the fingerprint/lab first |
| B8 | 1,000 targets | 3 scan requests each; **no 1,000 exploit attempts** | — | scan → dedupe → lab → authorized sample |

## 12. Success math

Probability of at least one success in `n` independent attempts: `1 − (1 − p)^n`.

| p | 1 | 2 | 3 | 5 | 8 | 10 |
|---|---|---|---|---|---|---|
| **0.4** (our lab) | 40% | 64% | 78% | 92% | 98% | 99.4% |
| **0.7** (upstream) | 70% | 91% | 97% | 99.8% | 99.99% | 99.999% |

Expected attempts: `1/p` ≈ 2.5 at p=0.4, 1.4 at p=0.7.

---

## 13. Agents and swarms

| job | one agent enough? | swarm needed? | why |
|---|---|---|---|
| Read the PoC and write hypotheses | yes | no | one 763-line file; hypotheses are serial |
| Build the lab | yes | no | environment work is one bottleneck at a time |
| Find the right server class | yes | maybe | the Apache/direct-CLI failures were serial hypotheses; small search space |
| Run the exploit | yes | **no** | one script against four workers; multiple attackers contend and confuse the race |
| Independent verification | no (producer cannot) | one verifier | a swarm of verifiers adds correlated opinions, not independence |
| Scan the app with the starter stack | irrelevant | no | the bug is in the PHP runtime, not the app/dependencies |
| Future breadth (many endpoints, fuzzing, many hosts) | no | yes | that is where parallel workers pay off |

## 14. Technical preconditions

| requirement | this lab | why it matters |
|---|---|---|
| PHP build | 8.4.26 Alpine CLI; `zval_ptr_dtor` low21 `0x112930` | heap and code offsets are build-specific |
| Worker model | four `php -S` workers | the leak needs a poisoned worker to be reused |
| Front end | nginx with `proxy_http_version 1.1` | serializes pipelined requests and reconnects to the workers |
| Memory limit | 128 MiB | the producer must hit the limit, not kill the process |
| Upload progress | `session.upload_progress.enabled=On` | with it off the producer does not OOM (mutation A) |
| Body size | under 1 MiB per request | calibration and challenge cap |
| Transport | raw HTTP/1.1, keep-alive, pipelining | consumers must queue behind the producer |
| Socket ownership | PHP worker owns the upstream connection | the command writes its output there |
