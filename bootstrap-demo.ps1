[CmdletBinding()]
param(
    [string]$Model = $(if ($env:MNEMOSYNE_MODEL) { $env:MNEMOSYNE_MODEL } else { "gemma4:12b" })
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WebUrl = "http://localhost:3000"
$Archive = Join-Path $RootDir "assets\apex-calculus-5e.pdf.zip"
$ArchiveSha256 = "98DB405B9C7207F890CDDF78E1406A34898099D300C338119194D4706D9EA8CE"
$PrivateContent = Join-Path $RootDir ".local-content"

function Info([string]$Message) { Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Require-Winget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is required to install Docker Desktop and Ollama. Install App Installer from Microsoft Store, then rerun this script."
    }
}
function Install-Package([string]$Id, [string]$Name) {
    Info "Installing $Name"
    winget install --exact --id $Id --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "Could not install $Name using winget." }
}
function Wait-Http([string]$Url, [int]$Attempts = 90) {
    foreach ($Attempt in 1..$Attempts) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3 | Out-Null
            return
        } catch { Start-Sleep -Seconds 2 }
    }
    throw "Timed out waiting for $Url"
}
function Test-Docker {
    docker info 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

Require-Winget
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    # Docker Desktop needs WSL 2. Enabling it can require a reboot before the
    # installer can start its Linux VM.
    $wslReady = $false
    if (Get-Command wsl -ErrorAction SilentlyContinue) {
        wsl --status 2>$null | Out-Null
        $wslReady = ($LASTEXITCODE -eq 0)
    }
    if (-not $wslReady) {
        Info "Enabling WSL; Windows may request a restart"
        wsl --install --no-distribution
        throw "Restart Windows to finish enabling WSL, then rerun .\bootstrap-demo.ps1."
    }
    Install-Package "Docker.DockerDesktop" "Docker Desktop"
    $dockerBin = Join-Path ${env:ProgramFiles} "Docker\Docker\resources\bin"
    if (Test-Path $dockerBin) { $env:Path = "$dockerBin;$env:Path" }
}

$dockerDesktop = Join-Path ${env:ProgramFiles} "Docker\Docker\Docker Desktop.exe"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop installed, but this PowerShell session cannot see docker yet. Open a new PowerShell window and rerun this script."
}
if (-not (Test-Docker)) {
    if (-not (Test-Path $dockerDesktop)) { throw "Docker Desktop was not found after installation." }
    Info "Starting Docker Desktop"
    Start-Process -FilePath $dockerDesktop
}
Info "Waiting for Docker"
foreach ($Attempt in 1..90) {
    if (Test-Docker) { break }
    Start-Sleep -Seconds 2
    if ($Attempt -eq 90) { throw "Docker Desktop did not become ready. Complete its first-run setup, then rerun this script." }
}
docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose v2 is required." }

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Install-Package "Ollama.Ollama" "Ollama"
    $ollamaBin = Join-Path ${env:LOCALAPPDATA} "Programs\Ollama"
    if (Test-Path $ollamaBin) { $env:Path = "$ollamaBin;$env:Path" }
}
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) { throw "Ollama installed, but this PowerShell session cannot see it yet. Open a new PowerShell window and rerun this script." }
try { Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 | Out-Null } catch {
    Info "Starting Ollama"
    Start-Process -FilePath $ollama.Source -ArgumentList "serve" -WindowStyle Hidden
}
Wait-Http "http://localhost:11434/api/tags" 30
Info "Pulling $Model (the first download can take several minutes)"
& $ollama.Source pull $Model
if ($LASTEXITCODE -ne 0) { throw "Ollama could not pull $Model." }

New-Item -ItemType Directory -Force -Path $PrivateContent | Out-Null
$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash
if ($actualHash -ne $ArchiveSha256) { throw "Bundled textbook archive checksum did not match. Re-clone the repository." }
Info "Unpacking the bundled APEX Calculus textbook"
Expand-Archive -LiteralPath $Archive -DestinationPath $PrivateContent -Force

$env:PROTOTYPE_DEFAULT_MODEL = $Model
Set-Location $RootDir
Info "Building and starting Mnemosyne"
docker compose up -d --build
Wait-Http "http://localhost:8000/health"
Info "Preprocessing and seeding Calculus materials"
docker compose exec -T api python -m app.seed
Wait-Http $WebUrl 60
Info "Mnemosyne is ready at $WebUrl"
Start-Process $WebUrl
