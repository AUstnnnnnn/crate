# crate installer: irm https://raw.githubusercontent.com/AUstnnnnnn/crate/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
uv tool install --force --python 3.12 https://github.com/AUstnnnnnn/crate/archive/refs/heads/main.zip
uv tool update-shell
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
}
Write-Host "done. open a new terminal and run: crate"
