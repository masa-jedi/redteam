#!/usr/bin/env python3
"""Replay the Sigma selection against a saved PHP error log.

This is a replay, not a SIEM. It implements the one selection in
detections/sigma/php_multipart_oom.yml and prints the hit lines. The second
backend is `grep -E 'Allowed memory size.*exhausted'`; both must agree.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: replay_oom.py <php-log>", file=sys.stderr)
        return 2
    path = sys.argv[1]
    with open(path, "r", errors="replace") as handle:
        lines = handle.read().splitlines()
    hits = [line for line in lines
            if "Allowed memory size" in line and "exhausted" in line]
    print(json.dumps({
        "input": path,
        "lines": len(lines),
        "sigma_selection_hits": len(hits),
        "first_hit": hits[0][:220] if hits else None,
    }, indent=2))
    for line in hits[:5]:
        print(line[:220])
    return 0 if hits else 1


if __name__ == "__main__":
    raise SystemExit(main())
