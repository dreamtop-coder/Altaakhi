# git_commit_push.ps1
# Script to add all changes, commit with the merged commit message, and push to the current branch

# تأكد أنك في مجلد المشروع

$commitFile = "commit-message-short.txt"

if (-Not (Test-Path $commitFile)) {
    Write-Host "ERROR: Commit message file '$commitFile' not found."
    exit 1
}

# Check git is available
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "ERROR: 'git' not found in PATH."
    Write-Host "Install Git for Windows: https://git-scm.com/download/win"
    Write-Host "Or use: winget install --id Git.Git -e --source winget (if winget is available)."
    Write-Host "After installation re-open PowerShell and re-run this script."
    exit 1
}

Write-Host "Adding all changes..."
git add -A

Write-Host "Committing using $commitFile..."
git commit -F $commitFile

Write-Host "Pushing to the remote branch..."
git push origin $(git branch --show-current)

Write-Host "Done."
