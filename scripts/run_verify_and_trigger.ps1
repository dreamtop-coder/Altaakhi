# Verify and trigger the production alignment workflow, saving outputs to artifacts/
# Usage: run from repo root in PowerShell where you have `gh` and `git` available:
#   .\scripts\run_verify_and_trigger.ps1

try {
    $ts = Get-Date -Format yyyyMMddHHmmss
    $outDir = Join-Path -Path . -ChildPath ("artifacts\workflow_verify_$ts")
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null

    Write-Host "Saving outputs to: $outDir"

    Write-Host "1) Default branch"; gh repo view --json defaultBranchRef --jq .defaultBranchRef.name 2>&1 | Tee-Object (Join-Path $outDir 'default_branch.txt')

    Write-Host "2) Workflow list"; gh workflow list --limit 50 2>&1 | Tee-Object (Join-Path $outDir 'workflow_list.txt')

    $default = gh repo view --json defaultBranchRef --jq .defaultBranchRef.name 2>$null
    if (-not $default) { Write-Host 'Could not determine default branch'; exit 2 }

    Write-Host "3) Show workflow file on remote branch: origin/$default";
    git fetch origin 2>&1 | Tee-Object (Join-Path $outDir 'git_fetch.txt')
    $remotePath = "origin/$($default):.github/workflows/run-production-alignment.yml"
    git show $remotePath 2>&1 | Tee-Object (Join-Path $outDir 'workflow_file_on_remote.txt')

    Write-Host "4) Trigger workflow (non-interactive)";
    gh workflow run .github/workflows/run-production-alignment.yml -f nonInteractive=true --ref $default 2>&1 | Tee-Object (Join-Path $outDir 'workflow_trigger.txt')

    Write-Host "5) Poll for a run and gather logs/artifacts (will poll up to 12 times)";
    $runId = $null
    for ($i=0; $i -lt 12; $i++) {
        Start-Sleep -Seconds 5
        gh run list --workflow=run-production-alignment.yml --limit 5 2>&1 | Tee-Object (Join-Path $outDir 'run_list_poll.txt')
        $runId = gh run list --workflow=run-production-alignment.yml --limit 1 --json databaseId --jq .[0].databaseId 2>$null
        if ($runId) { break }
        Write-Host "Waiting for run to appear... ($i)"
    }

    if (-not $runId) { Write-Host 'No run found after polling; check Actions settings' ; exit 3 }

    Write-Host "Found run id: $runId" | Tee-Object (Join-Path $outDir 'run_id.txt')
    Write-Host "Collecting run logs..."
    gh run view $runId --log 2>&1 | Tee-Object (Join-Path $outDir 'run_logs.txt')

    Write-Host "Attempting to download artifacts (if any)"
    gh run download $runId --name prod-alignment-artifacts --dir $outDir 2>&1 | Tee-Object (Join-Path $outDir 'artifact_download.txt')

    Write-Host "Done. Check folder: $outDir"
} catch {
    Write-Host "Error: $_"
    exit 1
}
