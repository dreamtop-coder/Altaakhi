"""
Hoist top-level import statements to the top of Python modules.
- Excludes migrations and files under venv/.venv
- Processes app directories passed in the script (default set in SCRIPT_DIRS)

CAUTION: This is an automated heuristic. It moves unindented `import`/`from` lines
that appear after initial module docstring/comments to a single import block. It may
break modules that intentionally perform late imports to avoid circular dependencies.
Use with care and review changes.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIRS = [
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "bookings",
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "cars",
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "clients",
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "invoices",
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "users",
    ROOT / "Altaakhi Workshop" / "Altaakhi Workshop" / "workshop",
]

IMPORT_RE = re.compile(r"^(from \S+ import .*|import \S+.*)$")

def hoist_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # find insertion point: after module docstring and initial comments/blank lines
    insert_idx = 0
    i = 0
    # skip shebang
    if lines and lines[0].startswith("#!"):
        i = 1
    # skip initial comments and blank lines
    while i < len(lines) and (lines[i].strip().startswith("#") or not lines[i].strip()):
        i += 1
    # if docstring starts
    if i < len(lines) and lines[i].strip().startswith(('"""', "'''")):
        quote = lines[i].strip()[:3]
        i += 1
        while i < len(lines) and quote not in lines[i]:
            i += 1
        if i < len(lines):
            i += 1
        # skip following blank/comments
        while i < len(lines) and (lines[i].strip().startswith("#") or not lines[i].strip()):
            i += 1
    insert_idx = i
    # collect top-level import lines (no indentation)
    imports = []
    new_lines = []
    for idx, ln in enumerate(lines):
        if ln.startswith(" ") or ln.startswith("\t"):
            new_lines.append(ln)
            continue
        if IMPORT_RE.match(ln):
            # record module-level import
            imports.append(ln)
            # mark removed by skipping adding to new_lines
            continue
        new_lines.append(ln)
    # avoid touching files with no imports or imports already at top
    if not imports:
        return False
    # remove duplicates while preserving order
    seen = set()
    uniq_imports = [im for im in imports if not (im in seen or seen.add(im))]
    # insert imports at insert_idx in new_lines
    # compute the current line index in new_lines corresponding to insert_idx in original
    # approximate by finding the position of the first occurrence of lines[insert_idx] in new_lines
    if insert_idx < len(lines):
        target_line = lines[insert_idx]
        try:
            pos = new_lines.index(target_line)
        except ValueError:
            pos = 0
    else:
        pos = 0
    out_lines = new_lines[:pos] + uniq_imports + [""] + new_lines[pos:]
    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return True


def main():
    changed = []
    for d in SCRIPT_DIRS:
        if not d.exists():
            continue
        for py in d.rglob("*.py"):
            if "migrations" in py.parts:
                continue
            try:
                if hoist_file(py):
                    changed.append(str(py))
            except Exception as e:
                print(f"Failed to process {py}: {e}")
    print(f"Files changed: {len(changed)}")
    for p in changed:
        print(p)

if __name__ == '__main__':
    main()
