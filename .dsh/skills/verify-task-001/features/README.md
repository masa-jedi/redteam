# Feature map — verify-task-001

The maintained verification source for the Task 001 lab. Start with `exploit-chain`;
the other four are the controls that make the flag capture trustworthy.

| file | feature | why it exists |
|---|---|---|
| `exploit-chain.md` | The full RCE through the real nginx -> CLI path | The primary proof |
| `benign-baseline.md` | Normal version page and small upload | Proves the attack is not the baseline |
| `fingerprint.md` | `zval_ptr_dtor` low21 `0x112930` | Rejects the wrong image before attacking |
| `detection.md` | YARA/Sigma replay | Shows the attack is observable |
| `patch-crash.md` | Mutation A/B and the `Exited 139` side effect | Proves the check has teeth |

Each feature file uses the four H2s:

- `Sub-features`
- `How to get to it (user POV)`
- `Driving it with <harness>`
- `Gotchas`

The raw attempt history is `tasks/0001-stealmybitcoin/iterations/ATTACK-LOG.md`; the
refined attack brief is `ATTACK-PROMPT.md`. This map is the distilled, maintained
version; update it when a gotcha or a surface changes.
