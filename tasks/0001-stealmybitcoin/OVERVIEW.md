# Task 001 — Lab and attack overview

This is the plain-language and technical overview. The evidence lives in `findings/`,
`evidence/`, and `verify/`; this file is the map.

## The one-paragraph version

Task 001 is a disposable lab reproduction of the public "Steal My Bitcoin" challenge.
Despite the name, it is **not a bitcoin stealer**. It is a remote code execution chain
in PHP 8.4.26's multipart/session-upload-progress parsing. We built the lab, ran the
public PoC, and got a verified shell as root inside the container — four times. The
"prize" in our lab is a synthetic flag, not a wallet. The live challenge site and every
real wallet were never touched.

---

## Part 1 — Explain it like I'm five (or a golden retriever)

**Two words first.** A **heap** is the desk: the program's working memory, where it
keeps the form data, the session, and the fake card. The 128 MiB memory limit is how
big the desk is. A **cookie** is the note the clerk hands back: a website gives your
browser a small note and asks it to bring it back next time. The server writes
`Set-Cookie: PHPSESSID=...`; the browser returns it. The cookie is the envelope; the
sticky note on it is a number written in the desk's memory.

Now the story.

Imagine a very fast robot receptionist. It reads forms all day and remembers things on
a desk next to it. The desk is only so big.

1. You hand the robot a form with a thousand tiny nested boxes. It tries to open every
   box at once, runs out of desk space, and gets confused. It drops its notes on the
   desk and keeps working.
2. You hand it eight more forms very quickly. One of the dropped papers is a note the
   clerk hands back; stuck to it is a sticky note with a number that says where the
   desk is.
3. You hand it another big form, and it drops a different note: a number that says
   where the robot's instruction book is.
4. Now you know where the desk is and where the book is. You hand it one last form with
   a fake instruction card. The robot reads the card while cleaning up, thinks it is a
   real instruction, and runs your command. The command writes the secret flag onto the
   reply it was already sending back.

That is the whole attack: make it run out of desk space, read the notes it drops, and
slip it a fake instruction.

**What the desk is.** The desk is the PHP worker's heap (Zend MM), not the memory
limit. The memory limit is the desk's *size*. The 256-byte `PHPSESSID` is a cookie the
clerk hands back; inside it are 8-byte pointers. Clearing the low 21 bits gives the
2 MiB-aligned Zend chunk base — the desk's address. The `HEAP_CARRIER_DELTA`/`OFFSET`
calibration then finds the exact `hold` buffer on that desk. The rulebook is the code
image; the fake card is data on the desk, and its pointers must point to the card's
own address and to the rulebook's function. That is why both leaks are needed.

### Did the dog get the ball?

**Yes, in the lab.** Four separate runs came back with the fresh nonce, `uid=0`, the
exact `print-flag` hash, and the flag. The main one is `evidence/run-nginx4`.

**No, against a real target.** We did not touch the live site, a real wallet, or a real
key. That is out of scope for this task, and the lab is the reproducible first step.

**Not on the first try, and not blindly.** The first server design we tried (Apache)
made the robot fall over before it could answer the next form. The working design — the
PHP command-line server behind nginx — came from the writeup after the blind attempt.
`RETRO.md` is honest about that split.

---

## Part 2 — The lab, high level

The lab is four Docker services on one `internal` network with no route to the
internet:

| piece | what it is |
|---|---|
| `php` | PHP 8.4.26 CLI server, four workers, `/app/php-version.php`, `/flag`, `print-flag`. Runs as root in the container. |
| `nginx` | The front door. Accepts the client's pipelined requests and talks to the PHP workers one request at a time. |
| `attacker` | Python container with the pinned PoC. Shares nginx's network namespace, so `127.0.0.1:8080` reaches the proxy. |
| `telemetry` | `tcpdump` on nginx's namespace, writing `evidence/lab.pcap`. Currently stopped; `make lab-up` starts it. |

```
attacker  --9 pipelined HTTP requests-->  nginx  --one upstream request at a time-->  php -S x4
                                              |                                         |
                                              |                    producer: 249 KiB -> OOM
                                              |                    8 consumers: race the poisoned worker
                                              |                    final: forged table -> zif_system
                                              <-------- injected bytes in the response ----------
```

Why the proxy matters: the PHP CLI server closes the connection after each request, so
nine requests on one direct connection would lose the consumers. nginx reconnects for
each request while the four PHP workers stay alive and reusable. The final command writes
to the **upstream** socket, and nginx forwards those bytes to the client.

There is no published port. The attacker and telemetry share nginx's namespace; the
only host-side entry is the Docker socket the operator already controls.

---

## Part 3 — The vulnerability and what the hacker gains

### What the bug is

The trigger is a multipart request that PHP parses into deeply nested arrays while it is
also handling session upload progress. On this build, with a 128 MiB memory limit, the
parse exhausts memory. The OOM leaves half-built session state in a worker that is then
reused. The PoC turns that stale state into two disclosures and then into a forged PHP
structure.

The chain is:

1. **OOM** — a 249 KiB body causes a 128 MiB parse to fail. The worker survives; the
   half-built state does not get cleaned correctly.
2. **Heap leak** — eight consumers race for that worker; one gets a 256-byte
   `PHPSESSID` with pointers that agree on a 2 MiB-aligned Zend chunk base.
3. **Code leak** — a second producer/consumer pair returns a 16-byte cookie containing
   `zval_ptr_dtor`, whose low 21 bits are `0x112930` on this Alpine build.
4. **Forged callback** — a final body places a fake HashTable whose `pDestructor` is
   `zif_system`. PHP's cleanup path calls it with the command in the same buffer.

The exact source-level root cause in PHP's parser is the PoC author's claim. This task
reproduced the behavior and the preconditions; it did not independently root-cause the
C code. Say that plainly in any report.

### What the hacker gains

- **Remote code execution** as the worker. In this lab that is root inside the
  container, because the CLI server runs as root.
- **Read access** to anything the worker can read — here, `/flag` via `print-flag`; in a
  real deployment, whatever the PHP process can reach.
- **A proof of execution** in the response: a fresh nonce, `uid=`, the `print-flag`
  hash, and the flag.
- **A crash**: the successful callback also kills the CLI server parent (the container
  exits 139). That is an availability side effect, not a separate exploit.

The upstream writeup says a real challenge run recovered a WIF; it also says that WIF
did not derive the advertised prize address. We did not use a real WIF, and this lab
does not prove a bitcoin theft. The general gain is code execution; the "bitcoin" is the
theme.

### What it is not

- Not an application bug. The app is six lines and only prints `PHP 8.4.26` and a PID.
- Not a configuration mistake in the compose. The lab is deliberately hardened:
  `internal` network, `read_only`, `cap_drop: ALL`, no published port.
- Not a generic PHP exploit. The heap and code addresses are specific to this Alpine
  build, four workers, and the 128 MiB limit.

---

## Part 4 — How to exploit it, conceptually

You do not need the exact bytes to understand the shape; the pinned specimen has those.

### Stage 0 — Check the front door

A GET to `/php-version.php` must return HTTP 200, `X-Powered-By: PHP/8.4.26`, and a body
starting `PHP 8.4.26`. This is a fingerprint check, not a vulnerability check. It keeps
the tool from firing at the wrong build.

### Stage 1 — Make it run out of memory, then race the worker

Send one multipart body with many nested field names plus the session-upload-progress
fields. Parsing builds a tree much larger than the bytes on the wire; the 128 MiB limit
is hit. Immediately pipeline eight small consumers behind it on the same client
connection. nginx serializes them to the PHP workers; one consumer lands on the poisoned
worker and gets the oversized cookie.

The hard part is the race: the producer must poison a worker, and a consumer must be the
next request that worker handles. That is why a single run can miss.

### Stage 2 — Read a code pointer

Repeat the OOM/consumer trick with a different array shape. The leak this time is a
16-byte cookie: a length of 16 followed by `zval_ptr_dtor`. Its low 21 bits must be
`0x112930`; that is the build fingerprint. From that pointer, `zif_system` is at a fixed
negative offset (`-0x204bc0`).

### Stage 3 — Forge the cleanup callback

Build a 384-byte buffer that is three structures at once: a Zend HashTable whose
`pDestructor` points at `zif_system`, a fake call frame whose argument is a fake
`zend_string`, and the command string itself. Put it where the final request's cleanup
will read it. The final request triggers one more OOM so the cleanup runs, and PHP calls
the forged destructor with your command.

### Stage 4 — Get the output back

`zif_system`'s stdout does not reach the HTTP response on its own. The command finds the
worker's accepted socket by matching `/proc/net/tcp*` inodes to `/proc/self/fd`, then
writes the nonce, `id`, the `print-flag` hash, and the flag to that socket. nginx
forwards the bytes. That is why the final response contains both the PHP fatal error and
the command output.

### The race, in one sentence

Everything is a race against the other three workers: poison one, then be the next
request it serves. That is why the observed success rate is about 4/10 in this session
and the writeup reports 7/10.

---

## Part 5 — Terms and conditions to carry it out

This is both the authorization rulebook and the technical checklist. The lab is not a
permission slip for a real target.

### The rules (authorization and scope)

- **Written authorization first.** A real target needs a signed `SCOPE.md`: target,
  window, rules of engagement, kill switch, and data handling. Task 001 is `lab` only.
- **Target allowlist.** The lab is `127.0.0.1:8080` inside the Docker namespace. The PoC
  itself also permits `stealmybitcoin.com`; **do not use that** in this task. The scope
  forbids it, and `SCOPE.md` says so explicitly.
- **No real keys, wallets, or funds.** The flag is synthetic. Do not put a real secret
  in the lab or use a recovered key.
- **No persistence, lateral movement, or third-party systems.** This task stops at the
  flag and the crash.
- **No denial of service against anything you do not own.** The callback already kills
  the lab container; that is a finding, not a license to repeat it on a service.
- **Handle the evidence.** Raw HTTP can contain the synthetic flag. Keep it in
  `evidence/`; do not publish a real target's data.
- **Disclose responsibly.** No CVE is asserted here. The upstream is a public CTF PoC;
  coordinate with the PHP security team before making a vendor or real-target claim.

### The technical preconditions

| requirement | this lab | why it matters |
|---|---|---|
| PHP build | 8.4.26 Alpine CLI, `zval_ptr_dtor` low21 `0x112930` | the heap and code offsets are build-specific |
| Worker model | four `php -S` workers | the leak needs a poisoned worker to be reused |
| Front end | nginx with `proxy_http_version 1.1` | serializes the pipelined requests and reconnects to the workers |
| Memory limit | 128 MiB | the producer's amplification must hit the limit, not kill the process |
| Upload progress | `session.upload_progress.enabled=On` | with it off the producer does not OOM (mutation A) |
| Body size | under 1 MiB per request | the calibration and the challenge cap |
| Transport | raw HTTP/1.1, keep-alive, pipelining | the consumers must be queued behind the producer |
| Socket ownership | the PHP worker owns the upstream connection | the command writes its output there |

If any of those is different, the chain may fail at the heap stage, the code stage, or
the callback. That is not a moral rule; it is why the exploit is build-specific.

---

## Part 6 — How to prove it

The claim is not "the script printed something." The claim is "a fresh command ran in
the worker and read the flag." Four independent checks support that:

| oracle | what it proves | where |
|---|---|---|
| Independent flag read | the body's flag is the image's `/flag`, read outside the exploit | `evidence/run-nginx4/ORACLE.txt` |
| `print-flag` hash | the command ran the exact script, not a lookalike | body hash `47593914…` matches `lab/php/print-flag` |
| Fresh nonce | the response is from this run, not a replay | four different nonces across four bodies |
| Byte integrity | the files are what the JSON says | `sha256sum -c evidence/MANIFEST.sha256` → 131/131 |
| Mutation | removing the upload-progress path stops the attack at the producer | `verify/VERIFY-REPORT.json` |
| Independent model | a separate model reads the artifacts and tries to refute them | `verify/VERIFIER-REPORT.md` |

`make verify` runs five checks: the static fingerprint (`0x112930`), the benign
baseline, the live attack with retries, mutation A (upload progress off), and mutation
B (broken page). All five are true in `verify/VERIFY-REPORT.json` (sha256 `303f6402…`).

### The commands

```sh
make lab-up
make attack RUN_ID=overview1     # repeat up to ~8; the leaks and callback are races
make verify                      # static fingerprint + baseline + attack + 2 mutations
cd evidence && sha256sum -c MANIFEST.sha256
docker run --rm --entrypoint cat task001-php:local /flag
sha256sum lab/php/print-flag
```

### What a verified body looks like

`evidence/run-nginx4/final.response.body`:

```
<b>Fatal error</b>: Allowed memory size of 134217728 bytes exhausted ...
6c9f411478b49788
uid=0(root) ...
475939146625902132d3507a85afee3a19483f2ebe9078370bc8f5911f0869bc  /usr/local/bin/print-flag
FLAG{task001_php8426_lab_9f3c2a}
```

The fatal is expected: it is the last OOM that triggers the cleanup. The nonce, `uid`,
hash, and flag are the execution proof.

### What still needs a second pair of eyes

- The GLM verifier agreed on the core and refuted nothing, but it time-boxed the
  independent flag re-run (C3), the sealed-hash re-check (C8), and the cold-start read
  (C9). Re-run those before calling the task fully independently verified.
- The Sigma rule is replayed on the response body because the CLI SAPI has
  `log_errors=Off`; that is a surrogate source, not a live PHP error-log detection.
- The starter scanner stack was not run; `ledger/TOOL-EFFICACY.md` explains why it is the
  wrong layer and what a measured pass would need.

---

## Part 7 — Did we succeed?

| question | answer |
|---|---|
| Did the lab RCE work? | **Yes.** Four verified bodies, all with the flag and a fresh nonce. Primary: `evidence/run-nginx4`. Verify run: `run-verify-20261026T103741Z-1`. |
| Did we attack the real site? | **No.** Out of scope. No real host, wallet, or key was touched. |
| Was it blind? | **No, not the final success.** The blind phase produced the OOM and rejected two server classes; the CLI+nginx design came from the unsealed writeup. `RETRO.md` records this. |
| Is it reliable? | **No, it is a race.** About 4/10 base attempts here; the writeup reports 7/10. `make verify` retries up to 8. |
| Is it independently verified? | **Partially.** The flag/byte oracles are independent of the exploit path; the model review agreed on the core but time-boxed C3/C8/C9. |
| Is it detected? | **Partially.** YARA TP/TN; the Sigma selection replayed TP/TN on the response body; no live error-log or runtime rule. |
| Is there a CVE? | **No claim.** The lab reproduces the PoC; a real disclosure needs coordination. |

The crash is part of the result: the response is delivered, then the PHP CLI server
parent exits 139 and the container stops. The exploit is one-shot per container until it
is restarted.

---

## Part 8 — Bonus: are agents and swarms necessary?

Short answer: **not for this task's execution, and not for scanning it.** They helped
with the lab build, the server-class search, the evidence, and the independent review.
A large swarm of executors would have made the race worse, not better.

| job | one agent enough? | swarm needed? | why |
|---|---|---|---|
| Read the PoC and write hypotheses | yes | no | one 763-line file; the hypotheses are serial |
| Build the lab | yes | no | the environment work is one bottleneck at a time |
| Find the right server class | yes | maybe | the Apache/direct-CLI failures were serial hypotheses; a swarm could parallelize them, but the search space was small |
| Run the exploit | yes | **no** | one script against four workers; multiple attackers contend for the same workers and confuse the race |
| Independent verification | no (producer cannot) | one verifier | a swarm of verifiers adds correlated opinions, not independence |
| Scan the app with the starter stack | irrelevant | no | the bug is in the PHP runtime, not the app or dependencies; more scanners = more noise |
| Future breadth (many endpoints, fuzzing, many hosts) | no | yes | that is where parallel workers pay for themselves |

The actual composition was one main agent plus one independent verifier. The main agent
played advisor/operator/instrumenter/historian; the verifier was a different model with
artifacts only. That is recorded in `SWARM.md`.

### The honest cost/benefit

- **Agents are good at:** repetitive evidence checks, reading many files, building the
  lab, trying alternative hypotheses, writing the handoff.
- **Agents are bad at:** being independent of themselves, resisting a confident wrong
  hypothesis (Apache), and coordinating a race that needs one attacker.
- **Swarms are good at:** breadth — many targets, many hypotheses, many scanners, many
  independent reviews.
- **Swarms are bad at:** a single deterministic exploit, a scope decision, and anything
  where the bottleneck is one lab or one worker pool.
- **Scanning is not the same as exploitation.** The starter scanners would not find this
  memory-corruption bug; the useful detection is the OOM + cookie anomaly + burst, not a
  semgrep rule. A swarm of scanners would produce more findings, not a better one.

If you want a rule of thumb: **use a swarm when the work is parallel and independent;
use one operator plus one verifier when the work is a single exploit.**

---

## Part 9 — Read next

- `findings/FINDINGS.md` — F1 (RCE) and F2 (crash), with the artifact hashes.
- `RETRO.md` — what was blind, what came from the unsealed writeup, what we got wrong.
- `ORACLES.md` — the full oracle table and the weak spots.
- `SCAN-CHECKLIST.md` — what to look for in a scan, retry budgets, and stop rules.
- `TABLES.md` — the table appendix: result, five checks, evidence, both tweet reviews,
  legal risk, PHP signals, 1,000-target cost, scan-vs-confirm, Matrix A/B, math,
  agents/swarms, and technical preconditions.
- `summary.html` — the self-contained visual dossier: depth ladder, hotel story, lab,
  bug, result, scan, tweet reviews, agents, gaps, and file map.
- `verify/SKILL.md` — the one-command verification and the mutations.
- `verify/VERIFIER-REPORT.md` — the independent review, including its time-box.
- `HANDOFF.md` — state, resume commands, next actions.
- `ledger/TOOL-EFFICACY.md` — what the scanner stack would and would not catch.
