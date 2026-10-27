# fingerprint

## Sub-features

- The victim image's CLI binary must be the Alpine PHP 8.4.26 build.
- `zval_ptr_dtor` must have low 21 bits `0x112930`.
- `zif_system - zval_ptr_dtor` must be `-0x204bc0`.

## How to get to it (user POV)

The verifier extracts `/usr/local/bin/php` from `task001-php:local` and reads its
symbols. This is the "is this the right build?" check that runs before any packet is
sent to the attack surface.

## Driving it with the harness

```sh
docker run --rm --entrypoint cat task001-php:local /usr/local/bin/php > /tmp/task001-php-cli
readelf -sW /tmp/task001-php-cli | grep ' zval_ptr_dtor$'
```

`verify/run_verify.py` does this automatically as its static calibration check. The
expected low21 is `0x112930`.

## Gotchas

- A wrong image (Debian, Apache module, FPM) can have a different low21 even when the
  function delta matches. The delta is necessary, not sufficient.
- The fingerprint is build-specific, not a generic PHP exploit constant. Do not reuse
  it for another PHP version.
- The static check is not the live proof; it only rejects an obviously wrong image.
