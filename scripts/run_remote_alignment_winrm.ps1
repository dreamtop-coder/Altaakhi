# Run the production alignment runbook on a remote Windows host via WinRM/Invoke-Command
# Usage example (from admin workstation):
#   .\run_remote_alignment_winrm.ps1 -ComputerName prod-server -RepoPath 'C:\inetpub\wwwroot\altaakhi' -Credential (Get-Credential)

param(
    [Parameter(Mandatory=$true)] [string]$ComputerName,
    [Parameter(Mandatory=$true)] [string]$RepoPath,
    [Parameter(Mandatory=$false)] [System.Management.Automation.PSCredential]$Credential,
    [switch]$NonInteractive,
    [switch]$UseSSL,
    [int]$Port = 5986
)

$scriptBlock = {
    param($RepoPath, $NonInteractive)
    Set-Location -Path $RepoPath
    if (Test-Path .\venv\Scripts\Activate.ps1) { . .\venv\Scripts\Activate.ps1 }
    else { Write-Host 'Virtualenv activation not found; ensure environment is activated or Python available in PATH' }
    $args = @('.\scripts\run_production_alignment.ps1')
    if ($NonInteractive) { $args += '-NonInteractive' }
    Write-Host "Executing: $($args -join ' ' ) in $RepoPath"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $args
}

try {
    $sessionParams = @{ ComputerName = $ComputerName }
    if ($Credential) { $sessionParams.Credential = $Credential }
    if ($UseSSL) { $sessionParams.UseSSL = $true; $sessionParams.Port = $Port }

    $sess = New-PSSession @sessionParams
    Invoke-Command -Session $sess -ArgumentList $RepoPath, $NonInteractive -ScriptBlock $scriptBlock
} catch {
    Write-Error "Remote execution failed: $_"
} finally {
    if ($sess) { Remove-PSSession -Session $sess -ErrorAction SilentlyContinue }
}
