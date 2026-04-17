
import os
import sys
import subprocess
import glob

DJANGO_SETTINGS = 'workshop.settings'
REPORT_FILE = 'project_full_check_report.txt'

def is_django_script(filepath):
    # A script is considered Django-dependent if it imports Django models or settings
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        django_keywords = [
            'from django', 'import django', 'from cars.models', 'from clients.models',
            'from invoices.models', 'from services.models', 'from workshop.settings',
        ]
        return any(kw in content for kw in django_keywords)
    except Exception:
        return False

def find_all_scripts():
    # Find all .py files in the current folder only (can be extended later)
    return [f for f in os.listdir('.') if f.endswith('.py') and f != os.path.basename(__file__)]

def main():
    syntax_ok = []
    syntax_fail = []
    logic_ok = []
    logic_fail = []
    skipped = []

    scripts = find_all_scripts()

    print('--- Syntax Check ---')
    for pyfile in scripts:
        try:
            subprocess.check_output([sys.executable, '-m', 'py_compile', pyfile], stderr=subprocess.STDOUT)
            print(f'✔ {pyfile} [OK]')
            syntax_ok.append(pyfile)
        except subprocess.CalledProcessError as e:
            print(f'✖ {pyfile} [Syntax Error]')
            print(e.output.decode())
            syntax_fail.append(pyfile)

    print('\n--- Logic Check ---')
    for script in scripts:
        if script in syntax_fail:
            skipped.append(script)
            continue
        print(f'>>> Running {script}')
        env = os.environ.copy()
        if is_django_script(script):
            env['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS
        try:
            result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=30, env=env)
            if result.returncode == 0:
                print(f'✔ {script} [OK]')
                logic_ok.append(script)
            else:
                print(f'✖ {script} [FAILED]')
                print(result.stdout)
                print(result.stderr)
                logic_fail.append(script)
        except Exception as e:
            print(f'✖ {script} [ERROR]')
            print(e)
            logic_fail.append(script)

    # write final report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('--- Scripts Check Report ---\n')
        f.write(f'Number of scripts: {len(scripts)}\n')
        f.write(f'✔ Syntax OK: {len(syntax_ok)}\n')
        f.write(f'✖ Syntax Errors: {len(syntax_fail)}\n')
        f.write(f'✔ Logic OK: {len(logic_ok)}\n')
        f.write(f'✖ Logic Failures: {len(logic_fail)}\n')
        f.write(f'Skipped (due to Syntax errors): {len(skipped)}\n\n')
        if syntax_fail:
            f.write('--- Syntax Errors ---\n')
            for s in syntax_fail:
                f.write(f'- {s}\n')
        if logic_fail:
            f.write('\n--- Logic Failures ---\n')
            for s in logic_fail:
                f.write(f'- {s}\n')
        if logic_ok:
            f.write('\n--- Successful scripts ---\n')
            for s in logic_ok:
                f.write(f'- {s}\n')
        f.write('\n--- End of report ---\n')

    print(f'\n--- Scripts check finished ---')
    print(f'Report saved to: {REPORT_FILE}')

if __name__ == '__main__':
    main()
