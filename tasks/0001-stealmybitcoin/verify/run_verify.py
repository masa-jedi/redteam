#!/usr/bin/env python3
"""Task 001 verification skill.

Drives the lab the way the PoC does, then checks that the result is real and
that the check has teeth:

1. static calibration of the CLI binary shipped in the victim image;
2. benign baseline (version page, small upload, follow-up GET);
3. live attack with bounded retries, then integrity checks on nonce, hashes,
   heap alignment, code fingerprint, and the independently read flag;
4. mutation A: remove the session-upload-progress path and require the attack to fail;
5. mutation B: break the benign page and require the baseline to fail.

Exit 0 only when every check passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TASK = REPO / "tasks" / "0001-stealmybitcoin"
LAB = TASK / "lab"
VERIFY = TASK / "verify"
EVIDENCE = TASK / "evidence"
BASE_COMPOSE = LAB / "compose.yaml"
LIMIT_COMPOSE = VERIFY / "mutation-off.yaml"
BADAPP_COMPOSE = VERIFY / "mutation-badapp.yaml"
IMAGE = "task001-php:local"
STAMP = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
REPORT: dict[str, dict] = {}


def base_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("DOCKER_CONFIG", str(REPO / ".docker"))
    env["LAB_UID"] = str(os.getuid())
    env["LAB_GID"] = str(os.getgid())
    return env


def run(cmd: list[str], env: dict[str, str] | None = None,
        timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=REPO, env=env or base_env(), capture_output=True,
        text=True, timeout=timeout,
    )


def compose(args: list[str], files: list[Path] | None = None,
            env: dict[str, str] | None = None,
            timeout: int = 300) -> subprocess.CompletedProcess:
    files = files or [BASE_COMPOSE]
    cmd = ["docker", "compose"]
    for path in files:
        cmd += ["-f", str(path)]
    cmd += args
    return run(cmd, env=env, timeout=timeout)


def check(name: str, ok: bool, detail: str) -> bool:
    REPORT[name] = {"ok": ok, "detail": detail}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)
    return ok


def wait_php(tries: int = 30) -> bool:
    for _ in range(tries):
        proc = run(["docker", "inspect", "--format",
                    "{{.State.Health.Status}}", "task001-php-1"], timeout=10)
        if proc.stdout.strip() == "healthy":
            return True
        time.sleep(1)
    return False


def static_calibration() -> tuple[bool, str]:
    tmp = tempfile.NamedTemporaryFile(suffix=".php", delete=False)
    tmp.close()
    try:
        with open(tmp.name, "wb") as out:
            proc = subprocess.run(
                ["docker", "run", "--rm", "--entrypoint", "cat", IMAGE,
                 "/usr/local/bin/php"],
                cwd=REPO, env=base_env(), stdout=out, stderr=subprocess.PIPE,
                timeout=120,
            )
        if proc.returncode != 0:
            return False, f"docker run failed: {proc.stderr.decode()[:200]}"
        proc = run(["readelf", "-sW", tmp.name], timeout=60)
        for line in proc.stdout.splitlines():
            if line.rstrip().endswith(" zval_ptr_dtor") and "FUNC" in line:
                value = int(line.split()[1], 16)
                low = value & 0x1FFFFF
                return low == 0x112930, (
                    f"zval_ptr_dtor=0x{value:x} low21=0x{low:x} expected 0x112930")
        return False, "zval_ptr_dtor not found in the CLI binary"
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return False, "unreachable"


def baseline(files: list[Path] | None = None,
             no_deps: bool = True) -> tuple[bool, subprocess.CompletedProcess]:
    args = ["run", "--rm"]
    if no_deps:
        args.append("--no-deps")
    args += ["attacker", "/verify/baseline.py"]
    proc = compose(args, files=files, timeout=120)
    ok = proc.returncode == 0 and '"baseline": "pass"' in proc.stdout
    return ok, proc


def image_flag() -> str:
    proc = run(["docker", "run", "--rm", "--entrypoint", "cat", IMAGE, "/flag"],
               timeout=60)
    return proc.stdout.strip()


def image_print_flag_hash() -> str:
    proc = run(["docker", "run", "--rm", "--entrypoint", "sha256sum", IMAGE,
                "/usr/local/bin/print-flag"], timeout=60)
    return proc.stdout.split()[0] if proc.stdout.split() else ""


def run_attack(run_id: str, files: list[Path] | None = None
               ) -> tuple[dict | None, Path, subprocess.CompletedProcess]:
    env = base_env()
    env["RUN_ID"] = run_id
    proc = compose(["run", "--rm", "--no-deps", "attacker"], files=files,
                   env=env, timeout=300)
    out_dir = EVIDENCE / f"run-{run_id}"
    final = out_dir / "final.json"
    data = json.loads(final.read_text()) if final.exists() else None
    return data, out_dir, proc


def verify_success(out_dir: Path) -> tuple[bool, str]:
    final = json.loads((out_dir / "final.json").read_text())
    body = (out_dir / "final.response.body").read_bytes()
    raw = (out_dir / "final.response.http").read_bytes()

    if not final.get("execution_proof_verified"):
        return False, "final.json says the proof did not verify"
    if hashlib.sha256(body).hexdigest() != final.get("response_body_sha256"):
        return False, "response body hash does not match final.json"
    if hashlib.sha256(raw).hexdigest() != final.get("response_sha256"):
        return False, "raw response hash does not match final.json"
    if not all(final.get(k) for k in ("nonce_seen", "id_seen", "binary_hash_seen")):
        return False, "one of the three proof markers is false"

    flag = image_flag()
    if not flag or flag.encode() not in body:
        return False, "independently read /flag is not in the response body"
    digest = image_print_flag_hash()
    if not digest or digest.encode() not in body:
        return False, "independent print-flag hash is not in the response body"
    if b"uid=" not in body:
        return False, "uid marker missing"

    code = json.loads((out_dir / "code.json").read_text())
    candidates = [int(x, 16) for x in code.get("candidate_addresses", [])]
    if len(candidates) != 1 or (candidates[0] & 0x1FFFFF) != 0x112930:
        return False, f"code candidate invalid: {code.get('candidate_addresses')}"

    heap = json.loads((out_dir / "heap.json").read_text())
    bases = [int(x, 16) for x in heap.get("candidate_addresses", [])]
    if len(bases) != 1 or (bases[0] & ((1 << 21) - 1)) != 0:
        return False, f"heap candidate invalid: {heap.get('candidate_addresses')}"

    return True, (f"nonce/hash/flag verified; heap={heap['candidate_addresses'][0]} "
                  f"code={code['candidate_addresses'][0]}")


def live_attack(attempts: int) -> tuple[bool, str]:
    last_error = ""
    for index in range(attempts):
        if index:
            compose(["up", "-d", "php"], timeout=120)
            wait_php()
        run_id = f"verify-{STAMP}-{index}"
        final, out_dir, proc = run_attack(run_id)
        if final and final.get("execution_proof_verified"):
            ok, detail = verify_success(out_dir)
            if ok:
                return True, f"attempt {index + 1}: {detail} ({out_dir.name})"
        if (out_dir / "run.json").exists():
            last_error = json.loads((out_dir / "run.json").read_text()).get("error", "")
        if not last_error:
            lines = (proc.stderr or proc.stdout or "").strip().splitlines()
            last_error = lines[-1] if lines else "no output"
        print(f"  attempt {index + 1}/{attempts} did not prove: {last_error}", flush=True)
    return False, f"no verified proof in {attempts} attempts (last: {last_error})"


def mutation_limit() -> tuple[bool, str]:
    files = [BASE_COMPOSE, LIMIT_COMPOSE]
    compose(["up", "-d", "--force-recreate", "php"], files=files, timeout=180)
    wait_php()
    base_ok, _ = baseline(files=files, no_deps=True)

    run_id = f"verify-mut-progress-{STAMP}"
    final, out_dir, _ = run_attack(run_id, files=files)
    proof = bool(final and final.get("execution_proof_verified"))
    error = ""
    if (out_dir / "run.json").exists():
        error = json.loads((out_dir / "run.json").read_text()).get("error", "")
    stopped_early = any(
        token in error.lower()
        for token in ("strict address", "did not return a valid cookie",
                      "producer did not return")
    )
    compose(["up", "-d", "--force-recreate", "php"], timeout=180)
    wait_php()
    ok = base_ok and not proof and stopped_early
    return ok, (f"baseline_ok={base_ok} attack_proof={proof} "
                f"stopped_early={stopped_early} error={error[:140]}")


def mutation_badapp() -> tuple[bool, str]:
    files = [BASE_COMPOSE, BADAPP_COMPOSE]
    compose(["up", "-d", "--force-recreate", "php"], files=files, timeout=180)
    time.sleep(1)
    base_ok, proc = baseline(files=files, no_deps=True)
    compose(["up", "-d", "--force-recreate", "php"], timeout=180)
    wait_php()
    ok = not base_ok
    return ok, (f"baseline_rejected_bad_page={ok} "
                f"exit={proc.returncode} out={proc.stdout.strip()[:160]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mutation-only", action="store_true")
    parser.add_argument("--attempts", type=int, default=8)
    args = parser.parse_args()

    results: dict[str, bool] = {}

    if not args.mutation_only:
        up = compose(["up", "-d", "--build", "php", "nginx"], timeout=600)
        if up.returncode != 0:
            print(up.stderr[-2000:], file=sys.stderr)
            return 2
        wait_php()

        ok, detail = static_calibration()
        results["static_calibration"] = check("static calibration", ok, detail)

        ok, proc = baseline(no_deps=False)
        results["benign_baseline"] = check(
            "benign baseline", ok,
            "pass" if ok else (proc.stdout or proc.stderr)[-300:])

        ok, detail = live_attack(args.attempts)
        results["live_attack"] = check("live attack", ok, detail)

    ok, detail = mutation_limit()
    results["mutation_limit"] = check("mutation A (no upload progress)", ok, detail)

    ok, detail = mutation_badapp()
    results["mutation_badapp"] = check("mutation B (broken page)", ok, detail)

    # leave the lab in the unmutated state
    compose(["up", "-d", "--force-recreate", "php"], timeout=180)

    report = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verify": "pass" if all(results.values()) else "fail",
        "checks": REPORT,
    }
    (VERIFY / "VERIFY-REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"verify": report["verify"], "checks": results}, indent=2))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
