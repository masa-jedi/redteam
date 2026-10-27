#!/usr/bin/env python3
"""Benign baseline for Task 001.

Runs inside the attacker container (shares nginx's netns). It exercises the
same surface as the exploit without any memory-limit payload: a version GET, a
small multipart upload with upload-progress fields, and a follow-up GET.

It must never OOM, never return the flag, and never return an anomalous
PHPSESSID. Exit 0 means the baseline held.
"""
from __future__ import annotations

import http.client
import json
import sys

HOST = "127.0.0.1"
PORT = 8080
PATH = "/php-version.php"
FLAG_PREFIX = "FLAG{"


def get(cookie: str | None = None) -> tuple[int, dict, bytes]:
    headers = {"Connection": "close"}
    if cookie:
        headers["Cookie"] = f"PHPSESSID={cookie}"
    conn = http.client.HTTPConnection(HOST, PORT, timeout=15)
    conn.request("GET", PATH, headers=headers)
    response = conn.getresponse()
    body = response.read(1 << 20)
    conn.close()
    return response.status, dict(response.getheaders()), body


def post_small() -> tuple[int, dict, bytes, str]:
    boundary = "baseline-boundary"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"PHPSESSID\"\r\n\r\na\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"PHP_SESSION_UPLOAD_PROGRESS\"\r\n\r\nbaseline\r\n",
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"f\"; filename=\"a.txt\"\r\n\r\nhello\r\n",
        f"--{boundary}--\r\n",
    ]
    body = "".join(parts).encode()
    conn = http.client.HTTPConnection(HOST, PORT, timeout=15)
    conn.request("POST", PATH, body=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "Connection": "close",
    })
    response = conn.getresponse()
    data = response.read(1 << 20)
    headers = dict(response.getheaders())
    set_cookie = headers.get("Set-Cookie", "")
    cookie = ""
    if "PHPSESSID=" in set_cookie:
        cookie = set_cookie.split("PHPSESSID=", 1)[1].split(";", 1)[0]
    conn.close()
    return response.status, headers, data, cookie


def main() -> int:
    checks: dict[str, bool] = {}

    status, headers, body = get()
    checks["get_status_200"] = status == 200
    checks["get_powered_by"] = headers.get("X-Powered-By") == "PHP/8.4.26"
    checks["get_body"] = body.startswith(b"PHP 8.4.26\n")
    checks["get_no_flag"] = FLAG_PREFIX.encode() not in body

    status, headers, body, cookie = post_small()
    oom = b"Allowed memory size" in body and b"exhausted" in body
    checks["post_status_200"] = status == 200
    checks["post_no_oom"] = not oom
    checks["post_cookie_normal"] = len(cookie) in (0, 32)
    checks["post_no_flag"] = FLAG_PREFIX.encode() not in body

    status2, _, body2 = get(cookie or None)
    checks["followup_status_200"] = status2 == 200
    checks["followup_body"] = body2.startswith(b"PHP 8.4.26\n")

    print(json.dumps({
        "baseline": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "post_cookie_bytes": len(cookie),
    }, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
