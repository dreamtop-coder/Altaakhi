#!/usr/bin/env python3
"""Create a ZIP archive of the project excluding common large/artifact dirs.

Exclude: venv, .venv, .git, __pycache__, db.sqlite3, *.pyc
"""
import os
import zipfile

root = os.getcwd()
zip_name = 'Altaakhi_Workshop_cleaned.zip'
exclude_names = {'venv', '.venv', '.git', '__pycache__'}
exclude_files = {'db.sqlite3'}
exclude_exts = {'.pyc'}

def should_skip(file_name):
    if file_name in exclude_files:
        return True
    for ext in exclude_exts:
        if file_name.endswith(ext):
            return True
    return False

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
    for folder, dirs, files in os.walk(root):
        # remove excluded directories from traversal
        dirs[:] = [d for d in dirs if d not in exclude_names]

        for f in files:
            if should_skip(f):
                continue
            abs_path = os.path.join(folder, f)
            # skip the generated zip file itself
            if os.path.abspath(abs_path) == os.path.abspath(os.path.join(root, zip_name)):
                continue
            arcname = os.path.relpath(abs_path, root)
            zf.write(abs_path, arcname)

print('Created archive:', zip_name)
