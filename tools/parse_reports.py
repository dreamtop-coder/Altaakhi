import re
from collections import Counter, defaultdict

FLAKE8 = 'reports/flake8_report_after_fix.txt'
BANDIT = 'reports/bandit_report_after_fix.txt'
CSV_OUT = 'reports/inspection_issues.csv'
MD_OUT = 'reports/inspection_report.md'

# parse flake8
flake8_by_file = Counter()
flake8_codes_by_file = defaultdict(Counter)
flake8_lines = []
try:
    with open(FLAKE8, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            flake8_lines.append(line)
            m = re.match(r'^(.*?):\d+:\d+:\s*([A-Z]\d+)\b', line)
            if m:
                path = m.group(1)
                code = m.group(2)
                flake8_by_file[path] += 1
                flake8_codes_by_file[path][code] += 1
except FileNotFoundError:
    pass

# parse bandit
bandit_by_file = Counter()
bandit_codes_by_file = defaultdict(Counter)
bandit_issues = []
try:
    with open(BANDIT, encoding='utf-8', errors='replace') as f:
        current_code = None
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('>> Issue:'):
                # e.g. >> Issue: [B110:try_except_pass] Try, Except, Pass detected.
                m = re.search(r'\[(B\d+):', line)
                current_code = m.group(1) if m else None
                bandit_issues.append(line)
            elif line.strip().startswith('Location:'):
                # e.g. Location: .\\Altaakhi Workshop\\clean_project.py:34:16
                m = re.search(r'Location:\s+(.*?):\d+', line)
                if m:
                    path = m.group(1)
                    bandit_by_file[path] += 1
                    if current_code:
                        bandit_codes_by_file[path][current_code] += 1
except FileNotFoundError:
    pass

# produce CSV
all_files = set(list(flake8_by_file.keys()) + list(bandit_by_file.keys()))
with open(CSV_OUT, 'w', encoding='utf-8') as out:
    out.write('file,flake8_issues,bandit_issues,top_flake8_codes,top_bandit_codes\n')
    for path in sorted(all_files):
        fcount = flake8_by_file.get(path, 0)
        bcount = bandit_by_file.get(path, 0)
        topf = ';'.join([f'{c}:{n}' for c, n in flake8_codes_by_file[path].most_common(3)])
        topb = ';'.join([f'{c}:{n}' for c, n in bandit_codes_by_file[path].most_common(3)])
        out.write(f'"{path}",{fcount},{bcount},"{topf}","{topb}"\n')

# produce markdown summary
with open(MD_OUT, 'w', encoding='utf-8') as md:
    md.write('# Inspection Report\n\n')
    md.write('## Quick Summary\n\n')
    md.write(f'- Total files with flake8 issues: {len([p for p in flake8_by_file if flake8_by_file[p]>0])}\n')
    md.write(f'- Total files with bandit issues: {len([p for p in bandit_by_file if bandit_by_file[p]>0])}\n')
    md.write('\n')

    md.write('## Top files by combined issue count\n\n')
    combined = Counter()
    for p in all_files:
        combined[p] = flake8_by_file.get(p,0) + bandit_by_file.get(p,0)
    for p, n in combined.most_common(20):
        md.write(f'- {p}: {n} issues (flake8={flake8_by_file.get(p,0)}, bandit={bandit_by_file.get(p,0)})\n')
    md.write('\n')

    md.write('## Top flake8 codes across repo\n\n')
    total_flake8_codes = Counter()
    for p in flake8_codes_by_file:
        total_flake8_codes.update(flake8_codes_by_file[p])
    for code, n in total_flake8_codes.most_common(10):
        md.write(f'- {code}: {n}\n')
    md.write('\n')

    md.write('## Top bandit codes across repo\n\n')
    total_bandit_codes = Counter()
    for p in bandit_codes_by_file:
        total_bandit_codes.update(bandit_codes_by_file[p])
    for code, n in total_bandit_codes.most_common(10):
        md.write(f'- {code}: {n}\n')
    md.write('\n')

    md.write('## Sample flake8 issues (first 10)\n\n')
    for l in flake8_lines[:10]:
        md.write(f'- {l}\n')
    md.write('\n')

    md.write('## Sample bandit issue lines (first 20)\n\n')
    for l in bandit_issues[:20]:
        md.write(f'- {l}\n')
    md.write('\n')

    md.write('## Reports\n\n')
    md.write('- Flake8 report: reports/flake8_report_after_fix.txt\n')
    md.write('- Bandit report: reports/bandit_report_after_fix.txt\n')
    md.write('- CSV summary: reports/inspection_issues.csv\n')

print('Reports generated:', CSV_OUT, MD_OUT)
