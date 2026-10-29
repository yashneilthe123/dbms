"""Draw diagrams/architecture.png: what SentinelX really is (Review 3 scope)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
fig, ax = plt.subplots(figsize=(19.5, 7.2), dpi=100)
ax.set_xlim(0, 1950); ax.set_ylim(0, 720); ax.axis('off')


def box(x, y, w, h, title, sub='', lw=1.2, r=12, bold=True, size=13):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}',
                                fc='white', ec='black', lw=lw))
    if sub:
        ax.text(x + w / 2, y + h / 2 + 12, title, ha='center', va='center', fontsize=size,
                fontweight='bold' if bold else 'normal')
        ax.text(x + w / 2, y + h / 2 - 14, sub, ha='center', va='center', fontsize=11)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha='center', va='center', fontsize=size,
                fontweight='bold' if bold else 'normal')


def arrow(x1, y1, x2, y2, label='', dashed=False):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', lw=1.2, color='black', linestyle='--' if dashed else '-'))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 12, label, ha='center', va='bottom', fontsize=10.5,
                bbox=dict(fc='white', ec='none', pad=1))


# data in
ax.add_patch(FancyBboxPatch((20, 30), 400, 660, boxstyle='round,pad=0,rounding_size=24', fc='white', ec='black', lw=1.2))
ax.text(45, 660, 'DATA IN (TEST DATA)', fontsize=13, fontweight='bold', va='center')
box(40, 520, 360, 90, 'Firewall / IDS logs', '50,021 lines (50,000 by a CTE)', bold=False, size=12.5)
box(40, 400, 360, 90, 'Attacks, IOCs, incidents', '30 attacks, 12 IOCs, 7 incidents', bold=False, size=12.5)
box(40, 280, 360, 90, 'tools/gen_seed.py', 'writes the INSERT scripts', bold=False, size=12.5)
box(40, 160, 360, 90, 'One batch = one transaction', 'a failed batch is rolled back', bold=False, size=12.5)

# database
ax.add_patch(FancyBboxPatch((520, 30), 620, 660, boxstyle='round,pad=0,rounding_size=24', fc='white', ec='black', lw=2.2))
ax.text(545, 660, 'MYSQL 8.0 DATABASE  sentinelx', fontsize=13, fontweight='bold', va='center')
rows = [
    ('16 tables in 3NF + incident_audit', 'keys, foreign keys, CHECK, UNIQUE, ENUM'),
    ('Triggers', 'open incidents, retro-hunt, IOC rules, audit trail'),
    ('Procedures and functions', 'assign incident (checks caller), report IOC, batch load'),
    ('Views', 'v_my_incidents (row-level), v_attack_details, v_ioc ...'),
    ('Indexes', 'idx_src_time (src_ip, log_time) for retro-hunt'),
    ('Roles and accounts', '3 roles, 3 users; lockout after 3 bad logins'),
]
for i, (t, s) in enumerate(rows):
    box(550, 555 - i * 95, 560, 78, t, s, size=12.5)

# users
ax.add_patch(FancyBboxPatch((1290, 30), 640, 660, boxstyle='round,pad=0,rounding_size=24', fc='white', ec='black', lw=1.2))
ax.text(1315, 660, 'PEOPLE  (mysql client / MySQL Workbench)', fontsize=13, fontweight='bold', va='center')
users = [
    ('root  (DBA)', 'schema changes, backups, recovery'),
    ('ananya.rao  (sx_admin)', 'reads and changes data; cannot change schema'),
    ('rahul.mehta  (sx_analyst)', 'views + procedures only; own incidents only'),
    ('divya.iyer  (sx_viewer)', 'risk view and attack report only'),
]
for i, (t, s) in enumerate(users):
    box(1320, 520 - i * 125, 580, 92, t, s, size=12.5)

# backups
box(1320, 45, 580, 60, 'mysqldump + binary log  ->  point-in-time recovery', '', bold=False, size=12)

arrow(420, 360, 518, 360, 'INSERT')
for i in range(4):
    y = 566 - i * 125
    arrow(1318, y, 1142, y)
ax.text(1230, 600, 'GRANTs', ha='center', va='bottom', fontsize=10.5)
arrow(1140, 75, 1318, 75, '', dashed=True)

plt.savefig(os.path.join(HERE, '..', 'diagrams', 'architecture.png'), bbox_inches='tight', facecolor='white')
print('wrote diagrams/architecture.png')
