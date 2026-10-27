rule StealMyBitcoin_PHP8426_PoC
{
    meta:
        description = "Python PoC for the PHP 8.4.26 multipart/session-upload-progress chain"
        author = "task-001"
        reference = "https://github.com/KillaBoi/StealMyBitcoin-PoC"
        specimen_sha256 = "eed0a0d670f9d85539ec7f272a0a42e8bde7080f50c6918efcf14caca9ce82f0"
        date = "2026-10-26"
        tlp = "CLEAR"

    strings:
        $s1 = "PHP_SESSION_UPLOAD_PROGRESS" ascii
        $s2 = "COOKIE-LAB-BOUNDARY" ascii
        $s3 = "zif_system" ascii
        $s4 = "print-flag" ascii
        $s5 = "multipart/form-data; boundary=" ascii

    condition:
        filesize < 1MB and 3 of them
}
