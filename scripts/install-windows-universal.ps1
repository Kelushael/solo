$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Kelushael/solo.git"
$SoloRoot = Join-Path $env:USERPROFILE ".solo"
$AppDir = Join-Path $SoloRoot "app"
$VenvDir = Join-Path $SoloRoot "venv"
$BinDir = Join-Path $env:USERPROFILE "bin"
$EnvFile = Join-Path $SoloRoot ".env"

Write-Host "`n1PA Solo Windows Installer" -ForegroundColor Yellow
Write-Host "Installs Solo, caches the solo command, then launches chat.`n"

New-Item -ItemType Directory -Force -Path $SoloRoot | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Git via winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Python via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --source winget
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Ollama via winget..." -ForegroundColor Yellow
    winget install --id Ollama.Ollama -e --source winget
}

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "Pulling DeepSeek 7B-class model..." -ForegroundColor Yellow
    ollama pull deepseek-coder:6.7b
}

if (Test-Path (Join-Path $AppDir ".git")) {
    Write-Host "Updating Solo repo..." -ForegroundColor Yellow
    Push-Location $AppDir
    git pull --ff-only
    Pop-Location
} else {
    if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
    git clone $RepoUrl $AppDir
}

Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv $VenvDir
& (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $VenvDir "Scripts\pip.exe") install -r (Join-Path $AppDir "requirements.txt")

if (-not (Test-Path $EnvFile)) {
@"
SOLO_HOST=0.0.0.0
SOLO_PORT=8787
SOLO_LIVE=0
TRADERSPOST_WEBHOOK_URL=
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=deepseek-coder:6.7b
MIN_SCORE=75
MAX_CONTRACTS=2
DAILY_EXIT_EST=16:45
WEBHOOK_SECRET=change-me
"@ | Set-Content -Path $EnvFile -Encoding UTF8
}

$SoloCmd = Join-Path $BinDir "solo.cmd"
$SoloStartCmd = Join-Path $BinDir "solo-start.cmd"
$SoloLogsCmd = Join-Path $BinDir "solo-logs.cmd"

@"
@echo off
cd /d "$AppDir"
"$VenvDir\Scripts\python.exe" solo_cli.py
"@ | Set-Content -Path $SoloCmd -Encoding ASCII

@"
@echo off
cd /d "$AppDir"
"$VenvDir\Scripts\python.exe" solo_agent.py
"@ | Set-Content -Path $SoloStartCmd -Encoding ASCII

@"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -Wait '$SoloRoot\logs\solo.jsonl'"
"@ | Set-Content -Path $SoloLogsCmd -Encoding ASCII

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$BinDir;$UserPath", "User")
    $env:Path = "$BinDir;$env:Path"
}

Write-Host "`nInstalled. From now on type: solo" -ForegroundColor Green
Write-Host "Engine mode: solo-start"
Write-Host "Logs: solo-logs"
Write-Host "Launching Solo now...`n" -ForegroundColor Yellow
& $SoloCmd
