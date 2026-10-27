# ATT&CK coverage — Task 001

| technique | covered | evidence | gap |
|---|---|---|---|
| T1190 Exploit Public-Facing Application | yes | nginx `/php-version.php`; producer + consumers; `run-nginx4` | the lab is the only target; no real exposure measured |
| T1059.004 Command and Shell Interpreter: Unix Shell | yes | `zif_system` runs `sh -c`; `uid=0` in the body | no interactive shell; one command per callback |
| T1005 Data from Local System | yes | `print-flag` reads `/flag`; body contains it | only the synthetic flag; no file enumeration |
| T1499 Endpoint Denial of Service | partial | the CLI server parent exits 139 after the callback; nginx returns 502 | caused by the exploit's cleanup, not a separate DoS; no load test |
| T1071 Application Layer Protocol | no | the command writes to the accepted/upstream socket | no C2 channel, no beaconing |
| T1546 Event Triggered Execution | no | none | no persistence |
| T1053 Scheduled Task/Job | no | none | no persistence |
| T1078 Valid Accounts | no | no credentials | not tested |
| T1046 Network Service Discovery | no | the lab has one endpoint | not tested |
| T1021 Remote Services | no | no lateral movement | not tested |

## Detection coverage

| signal | implemented | tested | gap |
|---|---|---|---|
| YARA on the PoC file | yes | TP specimen / TN app | rewritten client evades |
| Sigma on PHP memory-limit fatal | rule written | surrogate replay on the response body; `log_errors=Off` in the lab | needs `log_errors=On` + a real log backend |
| Anomalous `PHPSESSID` length (16/256) | no rule | observed in `heap.json`/`code.json` | no access-log field for the cookie; needs a proxy log |
| 9-request POST burst / `$request_length` > 200k | no rule | the pcap has the bytes | nginx log format lacks `$request_length` |
| `print-flag` child process | no rule | the `/tmp` canary was lost | needs a persistent runtime sensor |

## Not tested

Persistence, lateral movement, credential access, C2, a real target, a patched PHP
build, and a live SIEM. Do not infer coverage from the lab.
