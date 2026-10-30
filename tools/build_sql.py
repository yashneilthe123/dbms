"""Rebuild sql/NN_*.sql from runner/steps (run gen_steps.py first).

Each sql file keeps its own header and its list of '-- ---- step_name ----' markers;
the body under every marker is replaced with the current step file.
To add a step to an sql file, add its marker line there, then run this.
"""
import os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
STEPS = os.path.join(ROOT, 'runner', 'steps')
steps = {re.sub(r'^\d{3}_', '', f[:-4]): open(os.path.join(STEPS, f), encoding='utf-8').read().replace('\r\n', '\n')
         for f in os.listdir(STEPS) if f.endswith('.sql')}

changed = 0
for fn in sorted(os.listdir(os.path.join(ROOT, 'sql'))):
    if not re.match(r'\d\d_', fn):
        continue
    path = os.path.join(ROOT, 'sql', fn)
    old = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    head, *parts = re.split(r'^-- ---- (\S+) ----\n', old, flags=re.M)
    out = head
    for name in parts[0::2]:
        if name not in steps:
            sys.exit(f'{fn}: no step file for marker {name}')
        who = name.split('__as_')[1] if '__as_' in name else None
        note = f'-- run while logged in as the {who} test user\n' if who else ''
        out += f'-- ---- {name} ----\n' + note + steps[name] + '\n\n'
    out = out.rstrip('\n') + '\n'
    if out != old.rstrip('\n') + '\n':
        open(path, 'w', encoding='utf-8', newline='\n').write(out)
        changed += 1
        print('rebuilt', fn)
print(changed, 'file(s) changed')
