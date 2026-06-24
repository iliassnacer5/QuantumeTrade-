<#
.SYNOPSIS
    Lance toute la stack Quantum Trade AI (backend + frontend + postgres + redis + redpanda).

.DESCRIPTION
    Enveloppe docker compose : crée .env si absent, build et démarre tous les services,
    attend que le backend soit prêt, puis affiche les URLs d'accès.

.PARAMETER Logs
    Suit les logs après le démarrage (Ctrl+C pour quitter sans arrêter la stack).

.PARAMETER NoBuild
    Démarre sans rebuild des images (plus rapide si rien n'a changé).

.EXAMPLE
    .\start.ps1
    .\start.ps1 -Logs
    .\start.ps1 -NoBuild
#>
param(
    [switch]$Logs,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$compose = Join-Path $root "infra\docker-compose.yml"

Write-Host "==> Quantum Trade AI - demarrage" -ForegroundColor Cyan

# 0. Docker disponible ?
try { docker info *> $null } catch {
    Write-Host "ERREUR: Docker ne repond pas. Lancez Docker Desktop puis reessayez." -ForegroundColor Red
    exit 1
}

# 1. .env
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root ".env.example") $envFile
    Write-Host "==> .env cree depuis .env.example" -ForegroundColor Yellow
}

# 2. Build + up
$buildArg = if ($NoBuild) { @() } else { @("--build") }
Write-Host "==> docker compose up -d $buildArg" -ForegroundColor Cyan
docker compose -f $compose up -d @buildArg
if ($LASTEXITCODE -ne 0) { Write-Host "ERREUR au demarrage de la stack." -ForegroundColor Red; exit 1 }

# 3. Attente du backend (health)
Write-Host "==> Attente du backend (http://localhost:8080/health)..." -NoNewline
$ready = $false
foreach ($i in 1..40) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
    Write-Host "." -NoNewline
}
Write-Host ""

if ($ready) {
    Write-Host ""
    Write-Host "  Stack prete !" -ForegroundColor Green
    Write-Host "  ------------------------------------------" -ForegroundColor Green
    Write-Host "  Dashboard  : http://localhost:3000" -ForegroundColor Green
    Write-Host "  API        : http://localhost:8080" -ForegroundColor Green
    Write-Host "  API docs   : http://localhost:8080/docs" -ForegroundColor Green
    Write-Host "  ------------------------------------------" -ForegroundColor Green
    Write-Host "  Arret : .\stop.ps1   |   Logs : .\start.ps1 -Logs" -ForegroundColor DarkGray
    Write-Host ""
} else {
    Write-Host "  Le backend n'a pas repondu a temps. Voir les logs :" -ForegroundColor Yellow
    Write-Host "  docker compose -f infra/docker-compose.yml logs backend" -ForegroundColor Yellow
}

# 4. Logs optionnels
if ($Logs) {
    Write-Host "==> Logs (Ctrl+C pour quitter, la stack reste active)" -ForegroundColor Cyan
    docker compose -f $compose logs -f
}
