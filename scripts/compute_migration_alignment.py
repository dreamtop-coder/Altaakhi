#!/usr/bin/env python3
import re
from pathlib import Path

prod = Path('artifacts/django_migrations_production.txt').read_bytes().decode('utf-8', errors='replace')
staging = Path('artifacts/manage_showmigrations_20260214004534.log').read_bytes().decode('utf-8', errors='replace')

# parse production lines of form: id | app | name | applied
prod_pairs = []
for line in prod.splitlines():
    line=line.strip()
    if not line or line.startswith('```'):
        continue
    # expect pattern like: 1 | contenttypes | 0001_initial | 2026-01-22...
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 4 and parts[0].isdigit():
        _, app, name, applied = parts[:4]
        prod_pairs.append((app, name, applied))

prod_set = set((a,n) for a,n,_ in prod_pairs)

# parse staging showmigrations lines like: [X]  contenttypes.0001_initial
staging_pairs = []
for line in staging.splitlines():
    line=line.strip()
    m = re.match(r"\[.\]\s*(\S+)\.(\S+)", line)
    if m:
        app, name = m.group(1), m.group(2)
        # consider only applied ones: lines starting with [X]
        if line.startswith('[X]'):
            staging_pairs.append((app, name))

staging_set = set(staging_pairs)

missing_in_prod = staging_set - prod_set
extra_in_prod = prod_set - staging_set

out = []
out.append('# Missing in production (present in staging) -> recommend marking applied on production')
for app,name in sorted(missing_in_prod):
    out.append('# manage.py command:')
    out.append(f'python -u manage.py migrate {app} {name} --fake')
    out.append('# SQL alternative (after backup):')
    out.append(f"INSERT INTO django_migrations(app,name,applied) VALUES('{app}','{name}','2026-02-14 00:48:31');")
    out.append('')

out.append('# Extra in production (present in production but not applied in staging) - review before deleting')
for app,name in sorted(extra_in_prod):
    out.append(f"# production has: {app}.{name}")

print('\n'.join(out))

# Additional check: find apps that have both squashed and non-squashed applied names in production
apps = {}
for app,name,_ in prod_pairs:
    apps.setdefault(app, []).append(name)

dupes = {}
for app, names in apps.items():
    has_squashed = any('squash' in n or 'squashed' in n for n in names)
    has_non = any(not ('squash' in n or 'squashed' in n) for n in names)
    if has_squashed and has_non:
        dupes[app] = names

if dupes:
    print('\n# WARNING: the following apps in production have BOTH squashed and original migration names applied (may cause mixed-history issues):')
    for app,names in dupes.items():
        print(f'# {app}:')
        for n in names:
            print(f'#   - {n}')
    print('\n# Recommendation: keep DB backups; prefer adding any missing squashed rows on other envs rather than deleting originals here. If you must normalize, insert the squashed row (or run migrate --fake) on environments missing it, then optionally remove originals after careful review.')
