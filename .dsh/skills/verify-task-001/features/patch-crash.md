# patch-crash

## Sub-features

- Mutation A: `session.upload_progress.enabled=Off` must stop the attack at the
  producer; the benign baseline must still pass.
- Mutation B: a broken `/php-version.php` must fail the benign baseline.
- Crash: the successful callback kills the CLI server parent (`Exited 139`); the
  response is delivered before the crash.

## How to get to it (user POV)

The verifier removes the vulnerable path (mutation A), breaks the app (mutation B), and
checks the side effect of a successful callback. These are the negative controls: a
check that cannot fail proves nothing.

## Driving it with the harness

```sh
make verify
# or only the mutations
make verify-mutation
```

The mutations are `verify/mutation-off.yaml` + `verify/mutation-off.ini` and
`verify/mutation-badapp.yaml` + `verify/bad-php-version.php`.

## Gotchas

- Mutation A must fail for the right reason: no producer OOM, not a broken lab.
- The mutation mount path must resolve from the override file's directory
  (`../verify/mutation-off.ini`), and the file must be mode `0644` because the container
  is root with `CAP_DROP=ALL`.
- The crash is an availability side effect, not a second exploit. Do not report it as
  a separate RCE.
- A single live-attack miss is not a mutation failure; the live check has bounded
  retries.
