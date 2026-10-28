import re, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ddl = open(os.path.join(HERE, '..', 'sql', 'sentinelx_schema.sql')).read()
out = {}
for body, name in [(m.group(0), m.group(1)) for m in re.finditer(r'CREATE TABLE (\w+) \((.*?)\n\);', ddl, re.S)]:
    inner = re.search(r'\((.*)\n\);', body, re.S).group(1)
    lines = [re.sub(r'\s*--.*$', '', l).strip().rstrip(',') for l in inner.split('\n')]
    lines = [l for l in lines if l]
    cols, extra = [], []
    for l in lines:
        if re.match(r'(PRIMARY KEY|FOREIGN KEY|CHECK|INDEX|UNIQUE)\b', l):
            extra.append(l)
            continue
        m = re.match(r'(\w+)\s+(ENUM\([^)]*\)|DECIMAL\([^)]*\)|\w+(?:\(\d+\))?(?: UNSIGNED)?)\s*(.*)', l)
        col, typ, rest = m.groups()
        cols.append([col, typ, rest])
    # attach table-level constraints to their columns
    def add(col, text):
        for c in cols:
            if c[0] == col:
                c[2] = (c[2] + '; ' if c[2] else '') + text
    for e in extra:
        m = re.match(r'PRIMARY KEY \(([^)]*)\)', e)
        if m:
            ks = [k.strip() for k in m.group(1).split(',')]
            for k in ks: add(k, 'Part of composite PRIMARY KEY (' + ', '.join(ks) + ')')
            continue
        m = re.match(r'FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)(.*)', e)
        if m:
            add(m.group(1), f'FOREIGN KEY to {m.group(2)}({m.group(3)})' + (m.group(4).replace(' ON DELETE', ', on delete').lower() if m.group(4) else ''))
            continue
        m = re.match(r'INDEX (\w+) \(([^)]*)\)', e)
        if m:
            first = m.group(2).split(',')[0].strip()
            add(first, f'Indexed ({m.group(1)}: {m.group(2)})')
            continue
        if e.startswith('CHECK'):
            target = None
            for c in cols:
                if re.search(r'\b' + c[0] + r'\b', e):
                    target = c[0]; break
            add(target, e)
    rows = []
    for col, typ, rest in cols:
        r = rest.replace('AUTO_INCREMENT PRIMARY KEY', 'PRIMARY KEY, AUTO_INCREMENT').strip()
        if not r: r = 'NULL allowed'
        rows.append([col, typ, r])
    out[name] = rows
json.dump(out, open(os.path.join(HERE, 'attrs.json'), 'w'), indent=1)
for k, v in out.items():
    print(k); [print('   ', r) for r in v]
