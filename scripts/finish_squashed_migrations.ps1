param(
  [string] $EnvSecret,
  [switch] $Yes
)

if ($EnvSecret) { $env:DJANGO_SECRET_KEY = $EnvSecret }

if (-not $env:DJANGO_SECRET_KEY) {
  Write-Host "DJANGO_SECRET_KEY not set. Provide it via -EnvSecret or set DJANGO_SECRET_KEY env var." -ForegroundColor Red
  exit 1
}

$python = Join-Path -Path "venv/Scripts" -ChildPath "python.exe"
$apps = @("services","cars","inventory")

Write-Host "Running pre-checks (showmigrations + migrate --plan) for apps: $($apps -join ', ')" -ForegroundColor Cyan

foreach ($app in $apps) {
  Write-Host "`n--- showmigrations $app ---" -ForegroundColor Yellow
  & $python manage.py showmigrations $app
  Write-Host "`n--- migrate --plan $app ---" -ForegroundColor Yellow
  & $python manage.py migrate $app --plan
}

if (-not $Yes) {
  $confirm = Read-Host "`nIf the plans look correct, type 'yes' to proceed and record these migrations with --fake"
  if ($confirm -ne 'yes') {
    Write-Host "Aborted by user." -ForegroundColor Yellow
    exit 0
  }
} else {
  Write-Host "Auto-confirmed (--Yes)." -ForegroundColor Green
}

# Apply fake migrations in safe order
foreach ($app in $apps) {
  Write-Host "`nApplying fake migrations for $app ..." -ForegroundColor Cyan
  & $python manage.py migrate $app --fake
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to fake migrate $app (exit code $LASTEXITCODE). Stop." -ForegroundColor Red
    exit $LASTEXITCODE
  }
}

Write-Host "`nDone. Verify with:" -ForegroundColor Green
Write-Host "`n$env:DJANGO_SECRET_KEY='prodkey'; venv\\Scripts\\python.exe manage.py showmigrations" -ForegroundColor White
Write-Host "`nAnd run full migrate plan if needed:" -ForegroundColor White
Write-Host "`n$env:DJANGO_SECRET_KEY='prodkey'; venv\\Scripts\\python.exe manage.py migrate --plan" -ForegroundColor White
