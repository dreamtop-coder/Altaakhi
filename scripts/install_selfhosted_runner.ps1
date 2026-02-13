<#
Install and configure a GitHub self-hosted runner on Windows (PowerShell script).

Usage (interactive):
  - Open a browser to: https://github.com/<OWNER>/<REPO>/settings/actions/runners
  - Click New self-hosted runner -> Windows -> copy the token and run this script with the token

Example:
  .\install_selfhosted_runner.ps1 -RepoOwner MyOrg -RepoName Altaakhi -RunnerName staging-runner -Labels staging -Token <TOKEN>

Notes:
  - Run as Administrator on the staging host (192.168.10.233).
  - Use a repo-level runner token from GitHub UI (Settings → Actions → Runners → New runner).
#>

param(
    [Parameter(Mandatory=$true)][string]$RepoOwner,
    [Parameter(Mandatory=$true)][string]$RepoName,
    [Parameter(Mandatory=$true)][string]$RunnerName,
    [string]$Labels = 'staging',
    [string]$Token
)

if (-not $Token) {
    Write-Host "No token provided. Open the following URL in a browser to create a runner token:"
    Write-Host "https://github.com/$RepoOwner/$RepoName/settings/actions/runners"
    exit 1
}

$RunnerDir = "C:\actions-runner"
if (-not (Test-Path $RunnerDir)) { New-Item -ItemType Directory -Path $RunnerDir | Out-Null }
Set-Location $RunnerDir

$zipUrl = 'https://github.com/actions/runner/releases/latest/download/actions-runner-win-x64.zip'
Write-Host "Downloading runner package from $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile actions-runner.zip -UseBasicParsing

Write-Host 'Extracting...'
Expand-Archive .\actions-runner.zip -DestinationPath . -Force

Write-Host 'Configuring runner...'
& .\config.cmd --url "https://github.com/$RepoOwner/$RepoName" --token $Token --name $RunnerName --labels $Labels --unattended

Write-Host 'Installing runner as a service...'
& .\svc install

Write-Host 'Starting service...'
& .\svc start

Write-Host 'Runner installed. Verify in GitHub repo settings → Actions → Runners that the runner is online.'
