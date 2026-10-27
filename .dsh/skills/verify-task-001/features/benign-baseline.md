# benign-baseline

## Sub-features

- A GET of `/php-version.php` returns `PHP 8.4.26` and no fatal.
- A small multipart upload returns a normal 32-byte `PHPSESSID` (or no session cookie),
  not a 256-byte over-read.
- A follow-up GET still returns the version page; no shell, no flag, no crash.

## How to get to it (user POV)

A normal visitor opens the version page and submits a small form. The baseline is the
"nothing bad happened" path that the exploit must be distinguishable from.

## Driving it with the harness

```sh
make verify
```

The verification runs `verify/baseline.py` in the attacker container against
`http://127.0.0.1:8080/php-version.php`. It passes only if the version page is correct,
the small upload has no anomalous cookie, and the follow-up GET is still healthy.

For a standalone run:

```sh
docker compose -f tasks/0001-stealmybitcoin/lab/compose.yaml run --rm attacker \
  /verify/baseline.py
```

## Gotchas

- A broken version page must fail the baseline; that is mutation B's job.
- The baseline does not prove the exploit; it proves the lab is not already broken.
- The 32-byte cookie is the normal shape. A 256-byte cookie in the baseline would mean
  the heap over-read is firing outside the attack.
