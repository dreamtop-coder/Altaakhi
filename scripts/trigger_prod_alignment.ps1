# Trigger the GitHub Actions workflow that runs the production alignment runbook
# Usage: run locally where `gh` is authenticated and you have permission to trigger workflows

param(
    [switch]$NonInteractive
)

$workflow = 'run-production-alignment.yml'
Write-Host "Triggering workflow $workflow (repository must be checked out here)"

$inputs = @{ }
if ($NonInteractive) { $inputs['nonInteractive'] = 'true' }

# Trigger workflow via gh CLI
$cmd = "gh workflow run $workflow"
if ($inputs['nonInteractive']) { $cmd += " -f nonInteractive=true" }

Write-Host "Running: $cmd"
Invoke-Expression $cmd

Write-Host "You can monitor the run with: gh run list --workflow $workflow --limit 5"
Write-Host "Or view logs for the latest run: gh run view <run-id> --log"
