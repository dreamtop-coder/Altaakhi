param(
  [Parameter(Mandatory=$true)][string]$EnvSecret,
  [switch]$Yes
)

$py = "venv\Scripts\python.exe"
$timestamp = (Get-Date).ToString("yyyyMMddHHmmss")
$log = "migration_run_$timestamp.log"

Write-Output "Using Python: $py"
Write-Output "Log file: $log"
$env:DJANGO_SECRET_KEY = $EnvSecret

if (-not $Yes) {
  Write-Output "About to back up DB. Type 'yes' to continue:"
  $confirm = Read-Host
  if ($confirm -ne 'yes') { Write-Output "Aborted by user."; exit 1 }
}

# Backup DB
try {
  $bak = "db.sqlite3.bak_$timestamp"
  Copy-Item db.sqlite3 $bak -ErrorAction Stop
  Write-Output "DB backup created: $bak" | Tee-Object -FilePath $log -Append
} catch {
  Write-Output "ERROR: Failed to copy db.sqlite3 to $bak" | Tee-Object -FilePath $log -Append
  exit 1
}

# Helper to run command and stop on non-zero
function Run-Step($args) {
  Write-Output "`n> $args" | Tee-Object -FilePath $log -Append
  if ($args -is [string]) {
    $parts = $args -split ' '
  } else {
    $parts = $args
  }
  & $py @parts 2>&1 | Tee-Object -FilePath $log -Append
  if ($LASTEXITCODE -ne 0) {
    Write-Output "`n> FAILED: '$args' returned exit code $LASTEXITCODE" | Tee-Object -FilePath $log -Append
    Write-Output "See $log for full output."
    exit $LASTEXITCODE
  }
}

# Run showmigrations
Run-Step "manage.py showmigrations"

# Preview plan
Run-Step "manage.py migrate --plan"

# Apply migrations
Run-Step "manage.py migrate"

# Post-checks
Run-Step "manage.py showmigrations"
Run-Step "manage.py check"

Write-Output "`nMigrations completed successfully. Log: $log" | Tee-Object -FilePath $log -Append
