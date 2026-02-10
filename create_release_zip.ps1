# create_release_zip.ps1
# Create a ZIP of the project excluding common large/artifact dirs/files.

$zipName = 'Altaakhi_Workshop_cleaned_ps.zip'
$root = Get-Location

$excludeDirs = @('venv', '.venv', '.git', '__pycache__')
$excludeFiles = @('db.sqlite3')
$excludeExts = @('.pyc')

Write-Host "Creating archive $zipName (excluding: $($excludeDirs -join ', '), $($excludeFiles -join ', '))"

$files = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($root.Path.Length+1)
    # exclude by directory name anywhere in the path
    foreach ($d in $excludeDirs) {
        if ($rel -like "*${d}*") { return $false }
    }
    if ($excludeFiles -contains $_.Name) { return $false }
    if ($excludeExts -contains $_.Extension) { return $false }
    if ($_.FullName -eq (Join-Path $root $zipName)) { return $false }
    return $true
}

if (-not $files) {
    Write-Host "No files found to archive."
    exit 1
}

$paths = $files | ForEach-Object { $_.FullName }
Compress-Archive -LiteralPath $paths -DestinationPath $zipName -Force
Write-Host "Created archive: $zipName"
