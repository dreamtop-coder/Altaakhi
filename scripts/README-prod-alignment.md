Production alignment helpers
===========================

This folder contains helpers to trigger the production alignment workflow and to run the alignment runbook remotely.

Trigger via GH CLI (local machine with `gh` auth):

```powershell
# trigger non-interactive (recommended for CI/automation)
gh workflow run run-production-alignment.yml -f nonInteractive=true

# list recent runs
gh run list --workflow=run-production-alignment.yml --limit 5

# view logs for a run
gh run view <run-id> --log

# download artifacts from a run
gh run download <run-id> --name prod-alignment-artifacts --dir artifacts
```

Trigger from admin workstation via WinRM:

```powershell
# interactive credential prompt (HTTP/NTLM; admin machine and prod-host in same domain)
.\run_remote_alignment_winrm.ps1 -ComputerName prod-host -RepoPath 'C:\path\to\repo' -Credential (Get-Credential) -NonInteractive

# use HTTPS WinRM (recommended). Ensure target has an HTTPS WinRM listener and port 5986 open.
.\run_remote_alignment_winrm.ps1 -ComputerName prod-host -RepoPath 'C:\path\to\repo' -Credential (Get-Credential) -NonInteractive -UseSSL -Port 5986

# if using delegated credentials / existing session and WinRM is reachable, omit -Credential
.\run_remote_alignment_winrm.ps1 -ComputerName prod-host -RepoPath 'C:\path\to\repo' -NonInteractive -UseSSL -Port 5986
```

Notes:
- Run during a maintenance window. The runbook creates `db.sqlite3.bak_<ts>` in the repo root — copy this backup off-host immediately.
- Ensure the production host has a self-hosted runner (if you prefer running via Actions) or that WinRM is enabled and reachable from your admin host.
- If you plan to run `python manage.py migrate --noinput` after alignment, make sure required environment variables (e.g., `DJANGO_SECRET_KEY`) are available in the execution context.
