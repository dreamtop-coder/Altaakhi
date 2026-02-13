# GitHub Actions Secrets — Template (fill before adding in GitHub)

Do NOT commit private keys to the repo. Copy values locally and paste into GitHub → Settings → Secrets and variables → Actions → New repository secret.

Secrets to add (names and placeholders)

- SSH_PRIVATE_KEY
  - Value: <<<PASTE ENTIRE PRIVATE KEY FILE CONTENTS HERE>>>
  - Example source (PowerShell):
    ```powershell
    Get-Content C:\Users\Mahdi\deploy_staging_key -Raw
    ```

- SSH_HOST
  - Value: 192.168.10.233

- SSH_USER
  - Value: deployuser

- REMOTE_REPO_PATH
  - Value: C:\Path\To\Repo\On\Staging  # adjust to actual path on staging

- STAGING_SECRET (optional)
  - Value: any token/password your workflow expects (optional)

Quick UI steps

1. Open GitHub → Repository → Settings → Secrets and variables → Actions → New repository secret.
2. Add each secret name above and paste the corresponding value. Save.

Optional: add via `gh` CLI (example)

```bash
# set SSH_PRIVATE_KEY from local file
gh secret set SSH_PRIVATE_KEY --body "$(cat ~/deploy_staging_key)"
gh secret set SSH_HOST --body "192.168.10.233"
gh secret set SSH_USER --body "deployuser"
gh secret set REMOTE_REPO_PATH --body "C:\Path\To\Repo\On\Staging"
```

Triggering the workflow

- Method A (Actions UI): GitHub → Actions → select `Run staging migrations monitor` → Run workflow.
- Method B (push empty commit):

```bash
git commit --allow-empty -m "trigger: staging migration monitor"
git push origin YOUR_BRANCH
```

Post-run checks

- Open the workflow run → Artifacts → download `migration_run_*.log`.
- Verify `migrate --plan` and `migrate` outputs show success on staging.

Security notes

- Keep `SSH_PRIVATE_KEY` secret; do not paste here or into any chat.
- Limit the key to the `deployuser` virtual account on staging.

If you want, I can prepare the exact GH Secrets values file with placeholders filled (you'll only paste the private key locally).