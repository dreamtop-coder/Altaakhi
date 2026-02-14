<#
.SYNOPSIS
  Runbook to align `django_migrations` on production safely.

USAGE (on production host):
  Open PowerShell in the repo root and run:
    .\scripts\run_production_alignment.ps1

This script:
 - creates a DB backup
 - activates the virtualenv
 - attempts `manage.py migrate <app> <squashed>` --fake for each app
 - if migrate fails, falls back to running `scripts\apply_squashed_marks.py` (idempotent SQL inserts)
 - writes logs to `artifacts\prod_alignment_<ts>.log` and exports `showmigrations` and `django_migrations` dumps

PRECONDITIONS: run during a maintenance window and keep the backup off-host.
#>

param(
    [switch]$NonInteractive
)

function Log { param($s) $s = "$((Get-Date).ToString('s')) - $s"; $s | Tee-Object -FilePath $LogFile -Append; Write-Host $s }

$ts = Get-Date -Format yyyyMMddHHmmss
$LogDir = Join-Path -Path . -ChildPath artifacts
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$LogFile = Join-Path $LogDir "prod_alignment_$ts.log"

Log "Starting production alignment run"

# 1) Backup DB
$bak = "db.sqlite3.bak_$ts"
Log "Backing up db.sqlite3 -> $bak"
Copy-Item db.sqlite3 $bak -ErrorAction Stop
Log "Backup created: $bak"

# Optional: prompt to copy backup off-host
if (-not $NonInteractive) {
    $copyOff = Read-Host "Copy backup off-host now? Enter remote path or leave empty to skip"
    if ($copyOff) {
        try {
            Copy-Item $bak $copyOff -ErrorAction Stop
            Log "Backup copied to $copyOff"
        } catch { Log ("Failed copying backup to {0}: {1}" -f $copyOff, $_) }
    }
}

# 2) Activate venv
if (Test-Path .\venv\Scripts\Activate.ps1) {
    Log "Activating virtualenv"
    & .\venv\Scripts\Activate.ps1
} else {
    Log "Virtualenv activation script not found at .\venv\Scripts\Activate.ps1 - ensure environment is activated before running this script"
}

# 3) Attempt migrate --fake per-app
$targets = @{
    'cars' = '0001_squashed_0004_maintenancerecord_maintenance_date'
    'inventory' = '0001_squashed_0007_part_track_purchases_part_track_sales'
    'services' = '0001_squashed_0003_add_car_fk'
}

$migrateFailures = @()
foreach ($app in $targets.Keys) {
    $mig = $targets[$app]
    Log "Attempting: python -u manage.py migrate $app $mig --fake"
    $proc = & python -u manage.py migrate $app $mig --fake 2>&1
    $proc | Tee-Object -FilePath $LogFile -Append
    if ($LASTEXITCODE -ne 0) {
        Log ("migrate --fake failed for {0}:{1}" -f $app, $mig)
        $migrateFailures += $app
    } else {
        Log ("migrate --fake succeeded for {0}:{1}" -f $app, $mig)
    }
}

if ($migrateFailures.Count -gt 0) {
    Log "Some migrate --fake attempts failed: $($migrateFailures -join ', ')"
    Log "Running fallback: scripts\apply_squashed_marks.py (idempotent inserts)"
    $out = & python .\scripts\apply_squashed_marks.py 2>&1
    $out | Tee-Object -FilePath $LogFile -Append
    if ($LASTEXITCODE -ne 0) { Log "Inserter script failed: see log" } else { Log "Inserter script completed" }
}

# 4) Verification
Log "Collecting showmigrations -> artifacts\showmigrations_after_prod_$ts.txt"
& python -u manage.py showmigrations --list > (Join-Path $LogDir "showmigrations_after_prod_$ts.txt") 2>> $LogFile
Log "Exporting django_migrations -> artifacts\django_migrations_after_prod_$ts.txt"
& python -u scripts/print_django_migrations.py > (Join-Path $LogDir "django_migrations_after_prod_$ts.txt") 2>> $LogFile

Log "Completed production alignment run. Check $LogFile and artifacts showmigrations/django_migrations files."
