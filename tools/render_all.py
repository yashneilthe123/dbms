import os, json, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from render import parse, session_lines, render
OUT = os.path.join(HERE, '..', 'mysql-output'); IMG = os.path.join(HERE, '..', 'screenshots')
os.makedirs(IMG, exist_ok=True)
names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith('.txt') and not f.endswith('.err.txt'))
meta = {}
def load(n):
    so = open(f'{OUT}/{n}.txt', encoding='utf-8', errors='replace').read()
    ep = f'{OUT}/{n}.err.txt'
    se = open(ep, encoding='utf-8', errors='replace').read() if os.path.exists(ep) else ''
    return parse(so, se)
# groups of block indexes per image; default = everything in one image
SPLIT = {
  '000_reset': None, '031_dml_seed_data': None,       # not shown
  '151_trg_ioc_rules': [[0], [1], [2], [3]],            # drop SHOW TRIGGERS (very wide)
}
for n in names:
    blocks = load(n)
    groups = SPLIT.get(n, 'all')
    if groups is None:
        continue
    if groups == 'all':
        # routines: put the CREATE statement in its own image, demos in another
        first = ' '.join(blocks[0]['sql']).upper() if blocks else ''
        if any(k in first for k in ('CREATE PROCEDURE', 'CREATE FUNCTION', 'CREATE TRIGGER')) and len(blocks) > 1:
            groups = [[0], list(range(1, len(blocks)))]
        else:
            groups = [list(range(len(blocks)))]
    meta[n] = []
    for gi, g in enumerate(groups):
        lines = session_lines([blocks[i] for i in g])
        fn = f'{n}.png' if len(groups) == 1 else f'{n}_{gi + 1}.png'
        w, h = render(lines, f'{IMG}/{fn}')
        width_chars = max(len(t) + 7 for _, t in lines)
        meta[n].append({'file': fn, 'w': w, 'h': h, 'chars': width_chars, 'lines': len(lines)})
json.dump(meta, open(f'{IMG}/meta.json', 'w'), indent=1)
print(len(meta), 'steps', sum(len(v) for v in meta.values()), 'images')
big = [(k, m['file'], m['chars'], m['lines']) for k, v in meta.items() for m in v if m['chars'] > 120 or m['lines'] > 70]
print('wide/tall:', big)
