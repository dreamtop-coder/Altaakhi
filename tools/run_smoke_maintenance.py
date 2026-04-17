import os
import sys

# use test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')

# ensure project root on sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# run the smoke script in its own __main__ context
import runpy
runpy.run_path('scripts/smoke_test_maintenance.py', run_name='__main__')
