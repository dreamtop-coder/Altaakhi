param(
    [string]$WorkflowName = 'Run staging migrations monitor',
    [string]$WorkflowFile = '.github/workflows/run-staging-migrations.yml',
    [string]$Ref = 'main',
    [int]$MaxAttempts = 30,
    [int]$SleepSeconds = 10,
    [string]$ArtifactName = 'migration-log',
    [string]$OutDir = 'artifacts'
)

Write-Host "Triggering workflow '$WorkflowName' (ref=$Ref)..."
gh workflow run $WorkflowFile --ref $Ref 2>&1 | Write-Host

Write-Host "Waiting briefly for GitHub to register the run..."
Start-Sleep -Seconds 5

for ($i = 1; $i -le $MaxAttempts; $i++) {
    Write-Host ("Attempt {0}/{1}: checking for latest run id..." -f $i, $MaxAttempts)
    $run = gh run list --limit 1 --json databaseId,name,headBranch,status,conclusion,createdAt --jq .[0] 2>$null
    if (-not $run) {
        Write-Host ("No run returned yet. Sleeping {0} seconds..." -f $SleepSeconds)
        Start-Sleep -Seconds $SleepSeconds
        continue
    }

    $runObj = $run | ConvertFrom-Json
    $runId = $runObj.databaseId
    Write-Host ("Found run: id={0}, name={1}, status={2}, created={3}" -f $runId, $runObj.name, $runObj.status, $runObj.createdAt)

    Write-Host "Attempting to fetch run logs (best-effort)..."
    gh run view $runId --log 2>&1 | Write-Host

    Write-Host ("Trying to download artifact '{0}' for run {1}..." -f $ArtifactName, $runId)
    if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
    $dl = gh run download $runId --name $ArtifactName --dir $OutDir 2>&1
    Write-Host $dl

    if (Test-Path $OutDir) {
        Write-Host "Artifact directory created. Contents:"
        Get-ChildItem $OutDir | Select-Object Name,Length | Format-Table
        Write-Host ("Done. Artifact(s) downloaded to .\{0}" -f $OutDir)
        exit 0
    }

    Write-Host ("Artifact not found yet. Sleeping {0} seconds before retrying..." -f $SleepSeconds)
    Start-Sleep -Seconds $SleepSeconds
}

Write-Error "Reached max attempts ($MaxAttempts) without finding artifact '$ArtifactName'."
exit 2
