# Export PostgreSQL data from local Docker for migration to EC2.
# Run from intraday_predictor directory: .\scripts\export_db.ps1
# Output: backups\predictions_YYYYMMDD_HHMMSS.sql

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$BackupsDir = Join-Path $ProjectDir "backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputFile = Join-Path $BackupsDir "predictions_$Timestamp.sql"

# Load .env if present
$EnvFile = Join-Path $ProjectDir ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$PostgresUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "predictor" }
$PostgresDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "predictions" }

New-Item -ItemType Directory -Force -Path $BackupsDir | Out-Null

Write-Host "Exporting $PostgresDb (user: $PostgresUser) from local Docker..."
Push-Location $ProjectDir
docker compose exec -T db pg_dump -U $PostgresUser --no-owner --no-acl $PostgresDb | Out-File -FilePath $OutputFile -Encoding utf8
Pop-Location

Write-Host "Exported to: $OutputFile"
Get-Item $OutputFile | Select-Object FullName, Length
