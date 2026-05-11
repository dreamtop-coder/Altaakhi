import argparse
import time
import os

parser = argparse.ArgumentParser()
parser.add_argument('--files', nargs='+', default=['debug_context_guard.log','debug_post_dump.log'])
parser.add_argument('--timeout', type=int, default=120)
parser.add_argument('--poll', type=float, default=0.5)
args = parser.parse_args()

patterns = ['CTX_GUARD', 'ENFORCE_APPLIED', 'car_id_param', 'ctx_locked', 'ctx_car_id', 'ctx_customer_id']
start = time.time()
positions = {}
for f in args.files:
    if os.path.exists(f):
        positions[f] = os.path.getsize(f)
    else:
        # create empty file to watch
        open(f, 'a').close()
        positions[f] = 0

print(f"Watching {', '.join(args.files)} for patterns: {patterns}. Timeout={args.timeout}s")
found = []
try:
    while True:
        now = time.time()
        if now - start > args.timeout:
            print('Timeout reached, exiting.')
            break
        for f in args.files:
            try:
                cur_size = os.path.getsize(f)
                if cur_size < positions.get(f, 0):
                    # rotated/truncated
                    positions[f] = 0
                if cur_size > positions.get(f, 0):
                    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                        fh.seek(positions[f])
                        for line in fh:
                            line = line.rstrip('\n')
                            for p in patterns:
                                if p in line:
                                    print(f"[{os.path.basename(f)}] {line}")
                                    found.append((f, line))
                        positions[f] = fh.tell()
                        # exit early if ENFORCE_APPLIED seen
                        if any('ENFORCE_APPLIED' in ln for (_f, ln) in found):
                            print('Detected ENFORCE_APPLIED; exiting watcher.')
                            raise KeyboardInterrupt
            except Exception as e:
                # ignore individual file read errors
                # but print small notice
                print(f'Error reading {f}: {e}')
        time.sleep(args.poll)
except KeyboardInterrupt:
    pass

if found:
    print('\nSummary of matches:')
    for f, ln in found:
        print(f'- {os.path.basename(f)}: {ln}')
else:
    print('\nNo matching lines found.')
