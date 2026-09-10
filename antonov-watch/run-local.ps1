# Local watcher - runs while this PC is on. Press Ctrl+C to stop.
# Needs Python 3 on PATH (python --version). Edit NTFY_TOPIC below first.

$env:ADSB_HEX    = "50801b"
$env:NTFY_TOPIC  = "CHANGE-ME-to-your-ntfy-topic"
$env:STATE_FILE  = Join-Path $PSScriptRoot "state.json"

Write-Host "Watching $($env:ADSB_HEX) -> ntfy topic '$($env:NTFY_TOPIC)'. Ctrl+C to stop."
while ($true) {
    python (Join-Path $PSScriptRoot "watch.py")
    Start-Sleep -Seconds 300
}
