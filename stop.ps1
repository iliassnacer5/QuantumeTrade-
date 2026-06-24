<#
.SYNOPSIS
    Arrete la stack Quantum Trade AI.

.PARAMETER Purge
    Supprime aussi le volume Postgres (reset complet de la base de donnees).

.EXAMPLE
    .\stop.ps1
    .\stop.ps1 -Purge
#>
param([switch]$Purge)

$ErrorActionPreference = "Stop"
$compose = Join-Path $PSScriptRoot "infra\docker-compose.yml"

if ($Purge) {
    Write-Host "==> Arret + purge du volume Postgres" -ForegroundColor Yellow
    docker compose -f $compose down -v
} else {
    Write-Host "==> Arret de la stack (donnees conservees)" -ForegroundColor Cyan
    docker compose -f $compose down
}
Write-Host "==> Stack arretee." -ForegroundColor Green
