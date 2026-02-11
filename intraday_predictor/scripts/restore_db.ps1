# Restore PostgreSQL from a dump file (for EC2 or any target).
# Usage: .\scripts\restore_db.ps1 [path\to\dump.sql]
# If no path given, uses latest backup in backups\
#
# For EC2: set .env with POSTGRES_HOST=your-ec2-host (or localhost if Postgres on same EC2).

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

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
$PostgresHost = if ($env:POSTGRES_HOST) { $env:POSTGRES_HOST } else { "localhost" }
$PostgresPort = if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { "5432" }
$PostgresPassword = $env:POSTGRES_PASSWORD

# Resolve dump file
$BackupsDir = Join-Path $ProjectDir "backups"
if ($args.Count -gt 0) {
    $DumpFile = $args[0]
} else {
    if (-not (Test-Path $BackupsDir)) {
        Write-Error "No backups directory and no dump file specified."
        exit 1
    }
    $DumpFile = Get-ChildItem -Path $BackupsDir -Filter "predictions_*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $DumpFile) {
        Write-Error "No dump file found in $BackupsDir"
        exit 1
    }
    $DumpFile = $DumpFile.FullName
    Write-Host "Using latest dump: $DumpFile"
}

if (-not (Test-Path $DumpFile)) {
    Write-Error "Dump file not found: $DumpFile"
    exit 1
}

# Restore via Docker (local) or psql (remote)
if ($PostgresHost -eq "localhost" -or $PostgresHost -eq "127.0.0.1") {
    Write-Host "Restoring to local Docker..."
    Get-Content $DumpFile | docker compose -f (Join-Path $ProjectDir "docker-compose.yml") exec -T db psql -U $PostgresUser -d $PostgresDb
} else {
    Write-Host "Restoring to $PostgresHost..."
    $env:PGPASSWORD = $PostgresPassword
    psql -h $PostgresHost -p $PostgresPort -U $PostgresUser -d $PostgresDb -f $DumpFile
}

Write-Host "Restore complete."
