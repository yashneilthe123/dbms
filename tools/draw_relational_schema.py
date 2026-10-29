"""Draw diagrams/relational_schema.png straight from sql/sentinelx_schema.sql.

Primary-key columns are bold and underlined, foreign keys are marked (FK) and joined to the
key they reference. Link tables and the weak entity have a double border; incident_audit has
a dashed border because it deliberately has no foreign key.
"""
import os, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patches as mpatches

HERE = os.path.dirname(os.path.abspath(__file__))
ddl = open(os.path.join(HERE, '..', 'sql', 'sentinelx_schema.sql'), encoding='utf-8').read()

tables = {}
for name, body in re.findall(r'CREATE TABLE (\w+) \((.*?)\n\);', ddl, re.S):
    cols, pk, fks = [], [], {}
    for line in body.split('\n'):
        line = re.sub(r'--.*$', '', line).strip().rstrip(',')
        if not line:
            continue
        m = re.match(r'PRIMARY KEY \(([^)]*)\)', line)
        if m:
            pk += [c.strip() for c in m.group(1).split(',')]
            continue
        m = re.match(r'FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)', line)
        if m:
            fks[m.group(1)] = m.group(2)
            continue
        if re.match(r'(CHECK|INDEX|UNIQUE)\b', line):
            continue
        col = line.split()[0]
        cols.append(col)
        if 'PRIMARY KEY' in line:
            pk.append(col)
    tables[name] = {'cols': cols, 'pk': pk, 'fks': fks}

DOUBLE = {'mitigation', 'asset_vulnerability', 'incident_event', 'event_ioc', 'retro_hit'}
DASHED = {'incident_audit'}
W, HEAD, ROW = 330, 44, 30

# columns are arranged so that every foreign key joins neighbouring columns or its own column
LAYOUT = {  # name: (x, y_top)
    'analyst': (40, 40), 'incident': (40, 264), 'incident_event': (40, 578),
    'retro_hunt_run': (40, 742), 'retro_hit': (40, 966), 'network_log': (40, 1130),
    'ioc': (540, 40), 'event_ioc': (540, 414), 'attack_event': (540, 578), 'asset': (540, 1042),
    'threat_actor': (1040, 40), 'malware': (1040, 264), 'attack_type': (1040, 518),
    'mitigation': (1040, 742), 'vulnerability': (1040, 936), 'asset_vulnerability': (1040, 1130),
    'incident_audit': (1540, 40),
}
missing = set(tables) - set(LAYOUT)
assert not missing, missing


def height(t):
    return HEAD + ROW * len(tables[t]['cols']) + 10


def row_y(t, col):
    x, y = LAYOUT[t]
    return y + HEAD + ROW * tables[t]['cols'].index(col) + ROW / 2


total_h = max(LAYOUT[t][1] + height(t) for t in tables) + 40
total_w = max(LAYOUT[t][0] for t in tables) + W + 40
fig = plt.figure(figsize=(total_w / 100, total_h / 100), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, total_w); ax.set_ylim(total_h, 0); ax.axis('off')

# foreign-key lines first, so the boxes sit on top
for t, info in tables.items():
    for col, ref in info['fks'].items():
        refcol = tables[ref]['pk'][0] if len(tables[ref]['pk']) == 1 else tables[ref]['pk'][0]
        sx, _ = LAYOUT[t]; tx, _ = LAYOUT[ref]
        y1, y2 = row_y(t, col), row_y(ref, refcol)
        if tx > sx:
            x1, x2, d1, d2 = sx + W, tx, 1, -1
        elif tx < sx:
            x1, x2, d1, d2 = sx, tx + W, -1, 1
        else:  # same column: leave and come back on the right
            x1, x2, d1, d2 = sx + W, tx + W, 1, 1
        bend = max(60, abs(x2 - x1) * 0.45) if tx != sx else 110
        path = Path([(x1, y1), (x1 + d1 * bend, y1), (x2 + d2 * bend, y2), (x2, y2)],
                    [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
        ax.add_patch(FancyArrowPatch(path=path, arrowstyle='-|>', mutation_scale=14, lw=1.0,
                                     color='black', shrinkA=0, shrinkB=0, zorder=1))
        ax.plot([x1], [y1], 'o', color='black', ms=3.5, zorder=3)

for t, info in tables.items():
    x, y = LAYOUT[t]; h = height(t)
    ls = '--' if t in DASHED else '-'
    ax.add_patch(Rectangle((x, y), W, h, fc='white', ec='black', lw=1.6, ls=ls, zorder=2))
    if t in DOUBLE:
        ax.add_patch(Rectangle((x + 5, y + 5), W - 10, h - 10, fc='none', ec='black', lw=0.9, zorder=3))
    ax.plot([x, x + W], [y + HEAD - 6, y + HEAD - 6], color='black', lw=1.2, zorder=3)
    ax.text(x + W / 2, y + HEAD / 2 - 2, t.upper(), ha='center', va='center', fontsize=12.5,
            fontweight='bold', zorder=4)
    for i, c in enumerate(info['cols']):
        cy = y + HEAD + ROW * i + ROW / 2
        label = c + ('  (FK)' if c in info['fks'] else '')
        is_pk = c in info['pk']
        txt = ax.text(x + 16, cy, label, ha='left', va='center', fontsize=11,
                      fontweight='bold' if is_pk else 'normal', zorder=4)
        if is_pk:
            fig.canvas.draw()
            bb = txt.get_window_extent().transformed(ax.transData.inverted())
            ax.plot([bb.x0, bb.x1], [cy + 9, cy + 9], color='black', lw=1.0, zorder=4)

ax.text(40, total_h - 22,
        'Bold underlined = primary key.  (FK) + line = foreign key, arrow points at the referenced key.  '
        'Double border = link table / weak entity.  Dashed = incident_audit (no foreign key on purpose).',
        fontsize=10.5, ha='left', va='center')
out = os.path.join(HERE, '..', 'diagrams', 'relational_schema.png')
plt.savefig(out, facecolor='white')
print('wrote', out, len(tables), 'tables')
