<#
Runs a safe, interactive migration flow for staging.
Usage examples:
  # interactive (recommended)
  .\scripts\run_migrations_staging.ps1 -EnvSecret 'prodkey'

  # non-interactive (auto-confirm)
  .\scripts\run_migrations_staging.ps1 -EnvSecret 'prodkey' -Yes

Params:
 -EnvSecret: DJANGO_SECRET_KEY to use for the run (required if not set in env)
 -BackupPath: optional path for DB backup (file path for sqlite or a directory)
 -Yes: skip confirmations
 -PythonExe: path to python executable (default: venv\Scripts\python.exe)
 -Tests: optional tests label to run with `manage.py test <label>`; if empty runs `test --failfast`
#>

param(
  [string] $EnvSecret = $env:DJANGO_SECRET_KEY,
  [string] $BackupPath = "",
  [switch] $Yes,
  [string] $PythonExe = "venv\Scripts\python.exe",
  [string] $Tests = ""
)

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

if ($EnvSecret) { $env:DJANGO_SECRET_KEY = $EnvSecret }
if (-not $env:DJANGO_SECRET_KEY) { Fail "DJANGO_SECRET_KEY is not set. Provide via -EnvSecret or set environment variable." }

if (-not (Test-Path $PythonExe)) {
  Fail "Python executable not found at '$PythonExe'. Activate your venv or set -PythonExe." 
}

$python = $PythonExe

Write-Host "Using Python: $python" -ForegroundColor Cyan
Write-Host "DJANGO_SECRET_KEY present: YES" -ForegroundColor Cyan

# Backup
if (-not $BackupPath) {
  if (Test-Path "db.sqlite3") {
    $BackupPath = "db.sqlite3.bak_$(Get-Date -Format yyyyMMddHHmmss)"
  } else {
    $BackupPath = ""
  }
}

if ($BackupPath) {
  if (-not $Yes) {
    $confirm = Read-Host "About to back up database to '$BackupPath'. Type 'yes' to continue"
    if ($confirm -ne 'yes') { Write-Host 'Aborted by user.' -ForegroundColor Yellow; exit 0 }
  } else { Write-Host "Auto-confirmed backup to $BackupPath" -ForegroundColor Green }

  if (Test-Path "db.sqlite3") {
    Copy-Item -Path db.sqlite3 -Destination $BackupPath -Force
    if ($LASTEXITCODE -ne 0) { Fail "Failed to copy db.sqlite3 to $BackupPath" }
    Write-Host "DB backup created: $BackupPath" -ForegroundColor Green
  } else {
    Write-Host "db.sqlite3 not found; skipping sqlite backup. Ensure you have other DB backups for non-sqlite setups." -ForegroundColor Yellow
  }
}

# Helper to run manage.py commands
function RunCmd([string]$args) {
  Write-Host "`n> $python manage.py $args" -ForegroundColor DarkCyan
  & $python manage.py $args
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    Write-Host "Command failed with exit code $code" -ForegroundColor Red
  }
  return $code
}

# showmigrations
if (RunCmd "showmigrations" ) { Write-Host "showmigrations returned non-zero" -ForegroundColor Yellow }

# migrate --plan
$planCode = RunCmd "migrate --plan"
if ($planCode -ne 0) { Fail "Failed to run migrate --plan. Inspect output and fix issues before applying migrations." }

if (-not $Yes) {
  $confirm = Read-Host "If the plan looks correct, type 'yes' to apply migrations"
  if ($confirm -ne 'yes') { Write-Host 'Aborted by user.' -ForegroundColor Yellow; exit 0 }
} else { Write-Host "Auto-confirmed migrate (--Yes)" -ForegroundColor Green }

# Apply migrations
$migCode = RunCmd "migrate"
if ($migCode -ne 0) { Fail "migrate failed. Restore DB from backup and investigate. (backup: $BackupPath)" }

# Verify showmigrations
if (RunCmd "showmigrations") { Write-Host "showmigrations returned non-zero" -ForegroundColor Yellow }

# Django check
if (RunCmd "check") { Fail "manage.py check failed" }

# Run tests (optional)
if ($Tests -ne "") {
  if (RunCmd "test $Tests --failfast") { Fail "Tests failed" }
} else {
  Write-Host "Running quick test suite: test --failfast (may be slow)" -ForegroundColor Cyan
  if (RunCmd "test --failfast") { Write-Host "Tests reported failures or errored (investigate)." -ForegroundColor Yellow }
}

Write-Host "\nMigration run completed. If all steps passed, proceed to repeat on production." -ForegroundColor Green
Write-Host "If you need help running on production, tell me and I can prepare the exact commands or assist." -ForegroundColor Cyan
