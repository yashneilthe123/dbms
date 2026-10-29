"""Assemble the Review 3 report as report.json for render_docx.js.

Run from the repository root after a full build:
  python tools/gen_steps.py; (runner or scratch build) -> mysql-output/
  python tools/render_all.py; python tools/attrs.py
  python tools/report/build_report.py
  node tools/report/render_docx.js tools/report/out/report.json reports/SentinelX_Review3_Report.docx

Text that did not change since Review 2 is read from reports/SentinelX_Review2_Report.docx;
every screenshot is rendered from mysql-output/ (the real output of this build).
"""
import json, os, re, sys, zipfile, textwrap

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS = os.path.join(ROOT, 'tools')
sys.path.insert(0, TOOLS)
from render import parse, session_lines, render  # noqa: E402
import gen_steps  # noqa: E402  (defines Q and CQ; writes nothing when imported)

OUT = os.path.join(ROOT, 'tools', 'report', 'out')
SHOTS = os.path.join(ROOT, 'screenshots')
CUSTOM = os.path.join(OUT, 'img')
os.makedirs(CUSTOM, exist_ok=True)
MO = os.path.join(ROOT, 'mysql-output')
META = json.load(open(os.path.join(SHOTS, 'meta.json'), encoding='utf-8'))
ATTRS = json.load(open(os.path.join(TOOLS, 'attrs.json'), encoding='utf-8'))


def explain_rows(step):
    """First 'rows:' estimate in a vertical EXPLAIN output (it changes after every ANALYZE TABLE)."""
    txt = open(os.path.join(MO, step + '.txt'), encoding='utf-8').read()
    return int(re.search(r'^ +rows: (\d+)', txt, re.M).group(1))


def test_summary(step):
    txt = open(os.path.join(MO, step + '.txt'), encoding='utf-8').read()
    passed, failed = re.findall(r'^\|\s+(\d+) \|\s+(\d+) \|$', txt, re.M)[-1]
    return int(passed), int(failed)


TEST_STEPS = {'200_tests': 'root', '201_tests__as_rahul': 'rahul (analyst)', '202_tests__as_divya': 'divya (viewer)',
              '203_tests__as_ananya': 'ananya (admin)'}
TESTS = {k: test_summary(k) for k in TEST_STEPS}
N_TESTS = sum(a for a, b in TESTS.values())
N_FAILED = sum(b for a, b in TESTS.values())
assert N_FAILED == 0, 'a test failed: fix the build before writing the report'
N_QUERIES = len(gen_steps.Q)
CQ_ROWS = {'CQ-01': 4, 'CQ-02': 5, 'CQ-03': 5, 'CQ-04': 7, 'CQ-05': 2, 'CQ-06': 2, 'CQ-07': 3,  # predicted by hand
           'CQ-08': 4, 'CQ-09': 7, 'CQ-10': 2, 'CQ-11': 7}

SCAN_ROWS = explain_rows('181_idx_explain_before')
RANGE_ROWS = explain_rows('182_idx_explain_after')
ANALYZE_MS = float(re.search(r'actual time=[0-9.]+\.\.([0-9.]+) rows=8',
                             open(os.path.join(MO, '183_idx_not_used.txt'), encoding='utf-8').read()).group(1))


# ---------------------------------------------------------------- Review 2 text
def harvest(path):
    z = zipfile.ZipFile(path)
    body = re.search(r'<w:body>(.*)</w:body>', z.read('word/document.xml').decode(), re.S).group(1)

    def text(x):
        t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', x))
        for a, b in (('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'), ('&apos;', "'")):
            t = t.replace(a, b)
        return t

    out, i = [], 0
    pat = re.compile(r'<w:(p|tbl)\b')
    while True:
        m = pat.search(body, i)
        if not m:
            break
        tag, depth = m.group(1), 0
        for e in re.finditer(r'<(/?)w:%s\b[^>]*?(/?)>' % tag, body[m.start():]):
            if e.group(2) == '/':
                continue
            depth += -1 if e.group(1) else 1
            if depth == 0:
                end = m.start() + e.end()
                break
        x = body[m.start():end]
        if tag == 'p':
            out.append({'t': 'p', 'text': text(x)})
        else:
            rows = [['\n'.join(text(p) for p in re.findall(r'<w:p\b.*?</w:p>', c, re.S))
                     for c in re.findall(r'<w:tc>.*?</w:tc>', tr, re.S)]
                    for tr in re.findall(r'<w:tr\b.*?</w:tr>', x, re.S)]
            out.append({'t': 'tbl', 'rows': rows})
        i = end
    return out


R2 = harvest(os.path.join(ROOT, 'reports', 'SentinelX_Review2_Report.docx'))
T = lambda i: R2[i]['text'].strip()          # paragraph text
ROWS = lambda i: R2[i]['rows']                # table rows

# ---------------------------------------------------------------- blocks and figures
blocks, figs, alias = [], {}, {}  # alias: extra names for an existing figure (not counted)


def add(**b):
    blocks.append(b)


def h1(t, new_page=True): add(t='h1', text=t, newPage=new_page)
def h2(t): add(t='h2', text=t)
def h3(t): add(t='h3', text=t)
def p(text, **kw): add(t='p', runs=text if isinstance(text, list) else [{'text': text}], **kw)
def bullets(items): add(t='bullets', items=items)
def code(text): add(t='code', text=text.strip('\n'))
def table(header, rows, cols, **kw): add(t='table', header=header, rows=rows, cols=cols, **kw)


def size(wpx, hpx, max_w=6.5, max_h=6.0):
    w = min(max_w, wpx / 265.0)
    h = hpx * w / wpx
    if h > max_h:
        w, h = w * max_h / h, max_h
    return round(w, 3), round(h, 3)


def fig(path, caption, key=None, wpx=None, hpx=None):
    if wpx is None:
        from PIL import Image
        wpx, hpx = Image.open(path).size
    w, h = size(wpx, hpx)
    n = len(figs) + 1
    figs[key or caption] = n
    add(t='img', path=os.path.relpath(path, OUT), w_in=w, h_in=h)
    add(t='caption', text=f'Fig. {n}  {caption}')
    return n


def step_fig(name, caption, part=None):
    """Screenshot rendered by render_all.py (whole step, or part 1/2 of a routine step)."""
    for m in META[name]:
        if part is None or m['file'].endswith(f'_{part}.png'):
            fig(os.path.join(SHOTS, m['file']), caption, key=name + (f'_{part}' if part else ''),
                wpx=m['w'], hpx=m['h'])
            if part is None and len(META[name]) > 1:
                continue
            return


def load(name):
    so = open(os.path.join(MO, name + '.txt'), encoding='utf-8', errors='replace').read()
    ep = os.path.join(MO, name + '.err.txt')
    se = open(ep, encoding='utf-8', errors='replace').read() if os.path.exists(ep) else ''
    return parse(so, se)


def wrap_lines(lines, width):
    out = []
    for k, t in lines:
        if len(t) > width and k == 'res':
            parts = textwrap.wrap(t, width)
            out += [(k, parts[0])] + [(k, '    ' + x) for x in parts[1:]]
        else:
            out.append((k, t))
    return out


def part_fig(name, idx, caption, key, wrap=None, blocks_=None):
    bl = blocks_ if blocks_ is not None else load(name)
    lines = session_lines([bl[i] for i in idx])
    if wrap:
        lines = wrap_lines(lines, wrap)
    path = os.path.join(CUSTOM, key + '.png')
    w, h = render(lines, path)
    return fig(path, caption, key=key, wpx=w, hpx=h)


def ref(key):
    return '{{fig:%s}}' % key


# ================================================================= title page
add(t='title', text='SENTINELX: CYBER ATTACK INTELLIGENCE AND', b=True, size=30, before=1800, after=0)
add(t='title', text='THREAT HUNTING PLATFORM', b=True, size=30, after=240)
add(t='title', text='PROJECT REPORT (REVIEW 3: FINAL)', b=True, size=22, after=360)
add(t='title', text='Submitted by', after=60)
for who in ('Shlok Gupta (24BCI0061)', 'Shreya Bhushan (24BCI0086)', 'Yashneil Purkayastha (24BDS0158)'):
    add(t='title', text=who, b=True, after=40)
add(t='title', text='Prepared For', before=240, after=60)
add(t='title', text='DATABASE SYSTEMS (BCSE302P) - Lab PROJECT', b=True)
add(t='title', text='Submitted To', before=180, after=60)
add(t='title', text='Dr. Anand Bihari', b=True)
add(t='title', text='School of Computer Science and Engineering', b=True, after=240)
z = zipfile.ZipFile(os.path.join(ROOT, 'reports', 'SentinelX_Review2_Report.docx'))
logo = [n for n in z.namelist() if n.startswith('word/media/18f1e0f5')][0]
open(os.path.join(CUSTOM, 'vit_logo.png'), 'wb').write(z.read(logo))
add(t='img', path='img/vit_logo.png', w_in=3.2, h_in=0.95)

# ================================================================= abstract + contents
h1('Abstract')
p(T(15))
p('The database has 16 tables in Third Normal Form (3NF) and an append-only audit trail, on MySQL 8.0.46. '
  'Review 1 covered the design and Review 2 showed it working. This final report brings both together and adds '
  'what Review 3 asks for: a security layer in which restricted users reach data only through views and '
  'procedures, an audit trail of every change to an incident, a demonstration of SQL injection and its fix, '
  'transactions under concurrency (lost update, row locking, deadlock and isolation levels), query optimisation '
  f'with EXPLAIN and EXPLAIN ANALYZE, backup with point-in-time recovery, and {N_TESTS} automatic tests that run as '
  'four different users. While testing our own design we found and fixed eight real defects, among them a privilege '
  'escalation through a stored procedure and an audit trail the administrator could forge; they are described where '
  'they occur. Every statement in this report was run on MySQL 8.0.46. The figures are images rendered from the '
  'captured mysql client output of that run, which is kept unchanged in the mysql-output folder of the repository.')
p('We also narrowed the scope. The application layer (FastAPI, React) and the machine-learning parts described in '
  'Review 2 were never built; they are dropped from scope, and section 17 lists every change and the reason for it.')
add(t='pagebreak')
add(t='toc')

# ================================================================= 1-5
h1('1. Introduction')
p(T(41))
p(T(42))
p('Review 3 is about turning that working design into something we can defend: every rule enforced by the '
  'database, every user limited to what they need, every change to an incident traceable, every mistake '
  'recoverable, and every claim backed by a test that passes.')
p('Terms used in this report:', keepNext=True)
table(['Term', 'Meaning'], [
    ['SOC', 'Security operations centre: the team that watches for and handles attacks.'],
    ['IOC', 'Indicator of compromise: a value known to be hostile, such as an attacker\'s IP address or a malware hash.'],
    ['CVE, CVSS', 'A published software weakness (CVE-2024-3400) and its severity score from 0 to 10.'],
    ['MITRE ATT&CK', 'A public catalogue of attack techniques; each attack type stores its technique ID (T1110).'],
    ['Retro-hunt', 'Searching old logs for a newly reported bad IP, for the time it was hostile but not yet known.'],
    ['DEFINER / INVOKER', 'Whose rights a view, procedure or trigger runs with: its creator\'s (DEFINER, the MySQL '
                          'default) or the caller\'s (INVOKER).'],
    ['Skip scan', 'A MySQL 8 index access that jumps through a composite index once per value of its first column.'],
    ['Next-key lock', 'An InnoDB lock on an index record and the gap before it, used by locking reads.'],
    ['Binary log', 'MySQL\'s ordered record of every committed change, used for recovery and replication.'],
], [2200, 7160])

h1('2. Objectives', new_page=False)
bullets([T(i).replace(' (Review 2)', '') for i in range(44, 49)] + [
    'Secure the database itself: least privilege, row-level access, an audit trail that even the administrator '
    'cannot erase, protection against SQL injection, and recovery from mistakes.',
    'Back every claim with an automatic test that prints PASS or FAIL.'])

h1('3. Project Scope', new_page=False)
bullets([T(50), T(51), 'Search and reporting views over attacks, assets and risk.', T(53), T(54),
         'User roles (admin, analyst, viewer) with least-privilege access: restricted users reach data only through '
         'views and procedures.',
         'An append-only audit trail of incident changes, and backup with point-in-time recovery.'])
p('Out of scope: real-time detection of attacks, a user interface and machine-learning models. Attacks arrive as '
  'data, as they would from a firewall or IDS, and people use the mysql client or MySQL Workbench.')

h1('4. Key Contacts and Stakeholders', new_page=False)
rows = [r[:] for r in ROWS(57)[1:]]
rows[2][0] = 'Yashneil Purkayastha'
table(ROWS(57)[0], rows, [2400, 2200, 2160, 2600])

h1('5. Project Resource Requirements', new_page=False)
h2('5.1 Hardware Resource Requirements')
bullets([T(60), T(61)])
h2('5.2 Software Resource Requirements')
bullets([T(63).replace('(the machine all screenshots were taken on)', '(the machine all output was captured on)'),
         T(64), T(65),
         'Python 3 for the scripts in tools/ that generate the test data and the step files, render the captured '
         'mysql output into the figures, draw two of the diagrams and lay out this report.',
         'Windows PowerShell for the one-click runner (runner/RUN_ME.bat).',
         T(68)])

# ================================================================= 6-8
h1('6. System Architecture')
p('The database is the whole system. The test data is loaded by plain INSERT scripts; new log batches go through sp_load_log_batch, which loads a batch as one transaction and rolls the whole batch back if any line fails. Everything '
  'that must never be skipped (opening incidents, retro-hunts, protecting indicator history, recording who changed '
  'an incident) is a constraint or trigger inside MySQL. People connect with their own MySQL accounts, and what '
  'they can do is decided by the role on their account: the administrator works with the data, the analyst and the '
  'viewer only through views and procedures. Backups use mysqldump and the binary log.')
fig(os.path.join(ROOT, 'diagrams', 'architecture.png'), 'System architecture', key='arch')

h1('7. Module-wise Functional Description', new_page=False)
mods = [r[:] for r in ROWS(74)[1:]]
mods[0][0] = 'Search and reporting'
mods[5] = ['Roles and security',
           'Admins work with the data but cannot change the schema; analysts work only on their own incidents, '
           'through views and procedures; viewers only see reports. Accounts lock after three wrong passwords.',
           'roles sx_admin, sx_analyst, sx_viewer; v_my_incidents, v_ioc; sp_assign_incident, sp_report_ioc']
mods.append(['Audit trail', 'Records who changed which incident, when, and the old and new status, priority and '
             'owner. Only its triggers write it; no role can change, forge or delete a row.',
             'incident_audit, trg_incident_audit_update/delete, trg_audit_no_update/delete'])
mods.append(['Backup and recovery', 'Nightly dump plus the binary log restore the database to just before a '
             'mistake.', 'mysqldump, binary log, mysqlbinlog (section 15)'])
table(ROWS(74)[0], mods, [1800, 4300, 3260])

h1('8. ER Diagram')
p(T(76))
table(ROWS(77)[0], ROWS(77)[1:], [2600, 6760])
table(ROWS(79)[0], ROWS(79)[1:], [2000, 2900, 900, 3560])
fig(os.path.join(ROOT, 'diagrams', 'er_diagram.png'), 'ER diagram of SentinelX (Chen notation)', key='er')
p('The relational schema below is drawn by a script (tools/draw_relational_schema.py) straight from '
  'sentinelx_schema.sql, so it always matches the tables MySQL actually creates. It replaces the hand-drawn '
  'Review 2 version, which still showed the old partition keys (event_time and log_time inside primary keys) that '
  'Review 2 had already removed. incident_audit appears as a separate table with no relationship line: it is an '
  'implementation table for accountability, not part of the conceptual model, and it deliberately has no foreign '
  'key so that its rows survive the deletion of the incident they describe.')
fig(os.path.join(ROOT, 'diagrams', 'relational_schema.png'), 'Relational schema generated from the DDL', key='rs')

# ================================================================= 9 tables
h1('9. Tables and Constraints')
p(T(85).replace('All 16 tables', 'All 16 tables, and the audit table added in Review 3,')
  .replace('Every column that decides another column is itself a candidate key, so the tables also meet BCNF. ', '')
  .replace('its attributes with data types and constraints, the CREATE TABLE statement',
           'the CREATE TABLE statement with every data type and constraint')
  .replace('The normalisation steps and the 23 attributes removed after review are in section 15.',
           'The normalisation steps are in section 9.1; the 23 attributes removed after Review 1 are listed in '
           'section 15 of the Review 2 report.'))
step_fig('029_ddl_show_tables', 'SHOW TABLES after running the 17 CREATE TABLE statements')
h2('9.1 Normalisation, and the anomaly it prevents')
table(ROWS(516)[0], ROWS(516)[1:], [1800, 7560])
p('The check below runs on the loaded data. The first query confirms a functional dependency (each MITRE technique '
  'belongs to one attack type, so the result is empty). Then the attacks are copied into one flat table together '
  'with their asset\'s criticality, as they would be stored without normalisation, and one row is "corrected": '
  'web-01 now has two criticalities at once, an update anomaly. In the real schema the criticality is stored once, '
  'in asset, so it cannot disagree with itself.')
step_fig('037_dml_normalisation_check', 'Functional dependency check, and an update anomaly in a denormalised copy')
h2('9.2 The tables')
desc = {  # table: (description paragraph index, normal-form paragraph index)
    'asset': (89, 94), 'vulnerability': (96, 101), 'asset_vulnerability': (103, 108), 'network_log': (110, 115),
    'attack_type': (117, 122), 'mitigation': (124, 129), 'threat_actor': (131, 136), 'malware': (138, 143),
    'attack_event': (145, 150), 'analyst': (152, 157), 'incident': (159, 164), 'incident_event': (166, 171),
    'ioc': (173, 178), 'event_ioc': (180, 185), 'retro_hunt_run': (187, 192), 'retro_hit': (194, 199),
}
new_desc = {
    'malware': 'Malware samples. actor_id becomes NULL if the group is deleted.',
    'attack_event': 'One row per detected attack. Asset and type are required; attacker, malware and CVE are '
                    'optional. triage_priority is set by an analyst and stays NULL until the attack has been triaged.',
    'incident_audit': 'Added in Review 3. One row per change to an incident, written by triggers: who made it '
                      '(USER()), when, and the old and new status, priority and owner. It has no foreign key on '
                      'purpose, so the trail outlives a deleted incident. Two more triggers make it append-only, and '
                      'no role has INSERT, UPDATE or DELETE on it.',
}
new_nf = {
    'attack_event': 'Normal form: Everything depends on event_id. triage_priority is an analyst decision, not a '
                    'function of severity (events 5 and 6 both have severity 9 but are CRITICAL and HIGH), so there '
                    'is no transitive dependency. src_country stays because an IP\'s location changes over time. '
                    'actor_id records who carried out this attack, which is a different fact from who develops the '
                    'malware (malware.actor_id), and it is needed when no malware is known. 3NF.',
    'retro_hunt_run': 'Normal form: Everything depends on run_id. started_at is when the search actually ran '
                      '(SYSDATE() in the trigger), not a copy of the indicator\'s recorded_from, and the counts come '
                      'from v_retro_hunt_summary instead of being stored. 3NF.',
    'incident_audit': 'Normal form: Everything depends on audit_id; the old and new values describe one change. 3NF.',
}
order = [re.sub(r'^\d{3}_ddl_', '', n) for n in sorted(META) if re.match(r'0[12]\d_ddl_', n)
         and not n.endswith('show_tables')]
for tname in order:
    h3('Table: ' + tname)
    p(new_desc.get(tname) or T(desc[tname][0]))
    num = [n for n in META if n.endswith('_ddl_' + tname)][0]
    step_fig(num, f'CREATE TABLE {tname} executed in MySQL')
    p([{'text': new_nf.get(tname) or T(desc[tname][1]), 'b': True}])

# ================================================================= 10 DML
h1('10. Data Population (INSERT, UPDATE, DELETE)')
p(T(201))
h3('INSERT')
step_fig('030_dml_insert_asset', 'INSERT of the 10 assets')
p(T(205).replace('The other 14 tables', 'The other 15 tables'))
step_fig('032_dml_insert_noise_logs', 'Generating 50,000 background log lines with a recursive CTE')
h3('UPDATE')
p('Attacks 25 and 26 have not been triaged yet. An analyst sets their triage priority: attack 25 has severity 7 '
  'but was blocked, so it becomes MEDIUM; attack 26 (severity 4, blocked) becomes LOW.')
step_fig('033_dml_update', 'UPDATE of triage_priority, before and after')
h3('DELETE')
step_fig('034_dml_delete', 'INSERT and DELETE of a temporary asset')
h3('Constraints in action')
p(T(216))
fig(os.path.join(SHOTS, '035_dml_constraints.png'), 'Five rejected statements, one per constraint', key='035')
h3('Row counts')
step_fig('036_dml_row_counts', 'Row count of every table after loading (incident_audit is still empty)')

# ================================================================= 11 queries
h1('11. SQL Implementation')
p(T(223).replace('40 queries', f'{N_QUERIES} queries'))
table(ROWS(224)[0], ROWS(224)[1:], [1900, 4100, 600, 700, 2060])
notes = {'B5': T(261), 'C4': T(278), 'C6': T(285), 'D9': T(314), 'E3': T(325), 'F3': T(339), 'G1': T(353)}
section = {'A': '11.1 A. Basic queries', 'B': '11.2 B. Aggregate queries', 'C': '11.3 C. Joins',
           'D': '11.4 D. Subqueries', 'E': '11.5 E. Set operations', 'F': '11.6 F. Advanced functions',
           'G': '11.7 G. Window functions'}
step_names = {n.split('_', 1)[1]: n for n in META}
for qid, (title, _sql) in gen_steps.Q.items():
    if qid in ('A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1'):
        h2(section[qid[0]])
    p([{'text': f'{qid}. {title}', 'b': True}], keepNext=True)
    if qid in notes:
        p(notes[qid], keepNext=True)
    step_fig(step_names[qid], f'{qid}: {title}')

# ================================================================= 12 advanced
h1('12. Advanced SQL Implementation')
h2('12.1 Complex Business Queries')
p(T(364))
def cq_match(cid):
    step = '%03d_%s' % (99 + int(cid[3:]), cid.replace('-', ''))
    txt = open(os.path.join(MO, step + '.txt'), encoding='utf-8').read()
    got = int(re.findall(r'^(\d+) rows? in set', txt, re.M)[-1])
    assert got == CQ_ROWS[cid], (cid, got)
    return f'Yes: {got} rows, as predicted, with the values listed above'


cq_tables = [i for i, e in enumerate(R2) if e['t'] == 'tbl' and e['rows'] and len(e['rows']) == 7
             and e['rows'][1][1].startswith('CQ-')]
for i, (cid, (question, sql)) in zip(cq_tables, gen_steps.CQ.items()):
    rows = {r[0]: r[1] for r in ROWS(i)[1:]}
    n_next = len(figs) + 1
    p([{'text': cid, 'b': True}], keepNext=True)
    table(['Field', 'Content'], [
        ['ID', cid], ['Business question', question],
        ['SQL', {'text': sql.strip(), 'code': True}],
        ['Expected output', rows['Expected output']],
        ['Actual output screenshot', f'Below (Fig. {n_next})'],
        ['Matches the prediction', cq_match(cid)],
        ['Explanation', rows['Explanation']],
    ], [2000, 7360], cantSplit=True)
    step_fig('%03d_%s' % (99 + int(cid[3:]), cid.replace('-', '')), f'{cid} actual output')

h2('12.2 Views')
p('Six views: four written for the project and the two Review 1 views (v_vulnerability for CVE severity and '
  'v_retro_hunt_summary for retro-hunt counts) that replaced stored columns. v_ioc was added in Review 3 so that '
  'analysts no longer need any access to the ioc table. Whether each view is updatable is read from '
  f'information_schema (Fig. {ref("updatable")}).')
STEP_SQL = {n.split('_', 1)[1]: sql for n, sql in gen_steps.STEPS.items()}


def view_sql(step_key, view):
    sql = STEP_SQL[step_key]
    create = re.search(r'CREATE VIEW %s AS.*?;' % view, sql, re.S).group(0)
    use = re.search(r'^SELECT[^;]*\b%s\b[^;]*;' % view, sql, re.S | re.M)
    return create, (use.group(0) if use else None)


R2V = {v: {r[0]: r[1] for r in ROWS(i)[1:]} for v, i in
       (('v_attack_details', 412), ('v_asset_risk', 416), ('v_my_incidents', 420))}
VIEWS = [
    ('v_attack_details', 'joins 5 tables', 'view_attack_details', '120_view_attack_details',
     R2V['v_attack_details']['Purpose'].replace('so the dashboard and search pages need no joins',
                                                'so searches and reports need no joins'),
     R2V['v_attack_details']['Why useful'].split(' Not updatable')[0].replace('pages query one object',
                                                                              'queries use one object'),
     'No: it uses LEFT JOINs, so MySQL cannot map a change to one base row; the DELETE in the figure is refused '
     '(ERROR 1288). Only SELECT is granted.'),
    ('v_asset_risk', 'aggregated', 'view_asset_risk', '121_view_asset_risk',
     R2V['v_asset_risk']['Purpose'].replace('for the risk panel', 'for risk reporting'),
     R2V['v_asset_risk']['Why useful'].split(' Not updatable')[0],
     'No: GROUP BY, COUNT/SUM and a subquery; the UPDATE in the figure is refused (ERROR 1288).'),
    ('v_my_incidents', 'security, row-restricting', 'view_my_incidents', '122_view_my_incidents',
     R2V['v_my_incidents']['Purpose'],
     'Security: analysts have no privilege on the incident table, only on this view. As root it shows 0 rows, '
     f'because root is not an analyst; rahul\'s session shows his own incidents (Fig. {ref("194a")}).',
     'Yes: one table, no aggregation or join. WITH CHECK OPTION blocks changes that would move a row out of the '
     'view, such as handing an incident to someone else (ERROR 1369).'),
    ('v_ioc', 'security, Review 3', 'view_ioc', '124_view_ioc',
     'The indicator versions we currently believe (recorded_to IS NULL), so analysts can read indicators without any '
     'privilege on the ioc table.',
     'Security and simplification: hides superseded versions and the base table.',
     'Yes in MySQL\'s terms (one table, simple WHERE), but analysts only get SELECT; new indicators go through '
     'sp_report_ioc.'),
    ('v_vulnerability', 'Review 1', 'view_review1_views', '123_view_review1_views',
     'Each CVE with a severity label worked out from its CVSS score, instead of storing severity.',
     'Keeps the vulnerability table in 3NF (no cvss -> severity dependency) while queries still see the label.',
     'Yes for cve_id, cvss and published; the computed severity column itself cannot be updated.'),
    ('v_retro_hunt_summary', 'Review 1', 'view_review1_views', '123_view_review1_views',
     'Per retro-hunt run: lines matched and assets touched, counted from retro_hit.',
     'Replaces two stored counts that could go out of sync.',
     'No: GROUP BY and COUNT.'),
]
for view, kind, key, step, purpose, useful, updatable in VIEWS:
    create, use = view_sql(key, view)
    p([{'text': f'{view} ({kind})', 'b': True}], keepNext=True)
    table(['Field', 'Content'], [
        ['Purpose', purpose],
        ['CREATE VIEW statement', {'text': create, 'code': True}],
        ['Query using the view', {'text': use, 'code': True} if use else 'None separately: its definition and severity column are shown in the figure.'],
        ['Screenshot', f'Fig. {ref("view_" + view)}'],
        ['Why useful', useful],
        ['Updatable?', updatable],
    ], [2200, 7160])
    if not (view == 'v_retro_hunt_summary'):
        if step == '124_view_ioc':
            part_fig(step, [0, 1], 'v_ioc: definition and use', 'view_v_ioc')
        else:
            step_fig(step, f'{view}: definition, use and updatability' if step != '123_view_review1_views'
                     else 'v_vulnerability and v_retro_hunt_summary')
            alias['view_' + view] = len(figs)
    else:
        alias['view_v_retro_hunt_summary'] = alias['view_v_vulnerability']
part_fig('124_view_ioc', [2], 'Updatable or not, for all six views', 'updatable')

h2('12.3 Stored Procedures')
p([{'text': 'sp_assign_incident(incident, analyst) ', 'b': True},
   {'text': 'assigns an incident inside a transaction. It locks the incident row with SELECT ... FOR UPDATE, so two '
            'analysts cannot claim it at the same moment, and rejects closed incidents and viewer accounts with '
            'SIGNAL. Any error rolls the transaction back and is passed to the caller (RESIGNAL). '},
   {'text': 'Fixed in Review 3: ', 'b': True},
   {'text': 'the procedure runs with its definer\'s (root\'s) rights, and in Review 2 it never checked who called it, '
            'so an analyst could use it to give his incident to a colleague or take a colleague\'s incident, which is '
            'exactly what WITH CHECK OPTION stops on v_my_incidents. It now maps USER() (the caller; inside a DEFINER '
            'routine CURRENT_USER() is the definer) to an analyst, and analysts may only claim unassigned incidents '
            'for themselves.'}])
step_fig('140_proc_assign_incident', 'CREATE PROCEDURE sp_assign_incident', part=1)
step_fig('140_proc_assign_incident', 'sp_assign_incident: a valid call, a closed incident and a viewer rejected', part=2)
p([{'text': 'sp_attack_report(from, to) ', 'b': True}, {'text': T(432).split(') ', 1)[1]}])
step_fig('141_proc_attack_report', 'CREATE PROCEDURE sp_attack_report', part=1)
step_fig('141_proc_attack_report', 'sp_attack_report called for 1 to 15 October', part=2)
p([{'text': 'sp_report_ioc and sp_whoami (Review 3). ', 'b': True},
   {'text': 'sp_report_ioc is the only way an analyst can add an indicator. It sets recorded_from with SYSDATE(), '
            'the real clock: NOW() would follow a session\'s SET timestamp, which any user may change, so an analyst '
            'could have backdated when we learned about an indicator (fixed in Review 3, test S12). sp_whoami returns USER() and '
            'CURRENT_USER() side by side, which makes the difference between the caller and the definer visible.'}])
step_fig('142_proc_report_ioc', 'CREATE PROCEDURE sp_report_ioc', part=1)
step_fig('142_proc_report_ioc', 'sp_whoami, and a call by root (both functions return root)', part=2)
p('sp_load_log_batch, the batch loader with an exit handler, is shown with the transactions in section 13.')

h2('12.4 User-Defined Functions')
p([{'text': T(438)}])
step_fig('130_func_severity_label', 'fn_severity_label', part=1)
step_fig('130_func_severity_label', 'fn_severity_label used in a SELECT', part=2)
step_fig('131_func_asset_risk', 'fn_asset_risk', part=1)
step_fig('131_func_asset_risk', 'fn_asset_risk used in a SELECT', part=2)

h2('12.5 Triggers')
p([{'text': T(448)}])
step_fig('150_trg_auto_incident', 'trg_attack_auto_incident', part=1)
step_fig('150_trg_auto_incident', 'trg_attack_auto_incident firing on three new attacks', part=2)
p('Four triggers on ioc: trg_ioc_no_overlap (BEFORE INSERT) rejects a new version whose valid period overlaps an '
  'open one, trg_ioc_no_delete (BEFORE DELETE) and trg_ioc_only_close (BEFORE UPDATE) keep the history append-only, '
  'and trg_ioc_retro_hunt (AFTER INSERT) runs the retro-hunt. Fixed in Review 3: in Review 2 only DELETE was blocked, '
  'so an UPDATE could rewrite an indicator or reopen a closed version; trg_ioc_only_close now allows exactly one '
  'change, closing an open version with recorded_to (tests T32, T33). The overlap check also ignored closed '
  'versions wrongly the other way round: it still counted them, so a corrected version could never be added (T28). '
  'The retro-hunt records the time the search really ran (SYSDATE()).')
for k, name in enumerate(('trg_ioc_no_overlap', 'trg_ioc_no_delete', 'trg_ioc_only_close', 'trg_ioc_retro_hunt'), 1):
    step_fig('151_trg_ioc_rules', name, part=k)
p(T(460).replace('The overlapping second version and the DELETE are both refused.',
                 'The overlapping second version, the DELETE and an UPDATE that tries to change the IP are all refused.'))
step_fig('152_trg_retro_hunt_demo', 'Retro-hunt demonstration, then the three refused changes')
p([{'text': 'Audit triggers (Review 3). ', 'b': True},
   {'text': 'trg_incident_audit_update and trg_incident_audit_delete (AFTER UPDATE / AFTER DELETE on incident) write '
            'one row to incident_audit for every change, so it is recorded whether the change came through a view, a '
            'procedure or a direct statement. They record USER(), not CURRENT_USER(): inside a trigger CURRENT_USER() '
            'is the trigger\'s definer (root), which would make every row look the same. trg_audit_no_update and '
            'trg_audit_no_delete make the trail append-only even for root. No role has INSERT, UPDATE or DELETE on '
            'incident_audit, so nobody can add a forged row (in the first Review 3 build the admin still could: '
            'fixed, tests A06 and T34). TRUNCATE does not fire triggers, which is why no role except root has the DROP '
            'privilege that TRUNCATE needs. The time is SYSDATE(6), which a session cannot move. Gaps in audit_id are '
            'normal: an AUTO_INCREMENT value taken by a change that was later rolled back is not reused.'}])
part_fig('153_trg_audit', [0, 1, 2, 3], 'The four audit triggers', 'audit_create')
part_fig('153_trg_audit', [4, 5, 6], 'An UPDATE is recorded; deleting audit rows is refused', 'audit_demo')

h2('12.6 Cursors')
p([{'text': T(464)}])
step_fig('160_cursor_escalate', 'sp_escalate_incidents (cursor)', part=1)
step_fig('160_cursor_escalate', 'sp_escalate_incidents called', part=2)
p([{'text': T(469)}])
step_fig('161_cursor_asset_risk', 'sp_asset_risk_report (cursor)', part=1)
step_fig('161_cursor_asset_risk', 'sp_asset_risk_report called', part=2)
p('A cursor works one row at a time. The same escalation rule can be written as one set-based UPDATE with a join '
  'to the worst severity per incident, which is faster on large tables; the cursor is kept because it also writes a '
  'per-row log of what it changed.')

# ---------------------------------------------------------------- 12.7 security
h2('12.7 SQL Security Implementation')
p('Security is layered. From the outside in: an account locks after three wrong passwords; each account gets one '
  'role; restricted roles reach data only through views and procedures; the view v_my_incidents limits analysts to '
  'their own rows; procedures that run with the definer\'s rights check who called them; every change to an incident '
  'is written to an audit trail that only its triggers can write and no role can change, forge or delete; and the '
  'binary log makes mistakes recoverable '
  '(section 15). Passwords are not stored in our tables at all: users log in as MySQL accounts, whose passwords MySQL '
  'keeps as salted SHA-256 hashes with 5,000 rounds (caching_sha2_password).')
table(['Object', 'sx_admin', 'sx_analyst', 'sx_viewer'], [
    ['16 data tables', 'SELECT, INSERT, UPDATE, DELETE', '-', '-'],
    ['incident_audit', 'SELECT only (written by triggers)', '-', '-'],
    ['Schema changes (CREATE, ALTER, DROP, TRIGGER, GRANT)', '- (root, the DBA, only)', '-', '-'],
    ['v_my_incidents', 'SELECT, UPDATE', 'SELECT, UPDATE (own rows only)', '-'],
    ['v_attack_details, v_vulnerability, v_retro_hunt_summary, v_ioc', 'SELECT', 'SELECT', '-'],
    ['v_asset_risk', 'SELECT', 'SELECT', 'SELECT'],
    ['sp_assign_incident', 'EXECUTE', 'EXECUTE (claims for himself only)', '-'],
    ['sp_report_ioc, sp_whoami', 'EXECUTE', 'EXECUTE', '-'],
    ['sp_search_incidents', 'EXECUTE', 'EXECUTE (granted with the injection demonstration)', '-'],
    ['sp_attack_report', 'EXECUTE', 'EXECUTE', 'EXECUTE'],
    ['Login', 'Locked for 1 day after 3 wrong passwords', 'Same', 'Same'],
    ['User (default role)', 'ananya.rao', 'rahul.mehta', 'divya.iyer'],
], [2700, 2200, 2500, 1960])
table(['Task', 'Evidence'], [
    ['Create 3 or more users/roles', 'CREATE ROLE and CREATE USER with default roles and lockout (Fig. %s)' % ref('190')],
    ['GRANT privileges per role matrix', 'GRANT script (Fig. %s) and SHOW GRANTS output (Fig. %s, %s)' % (ref('190'), ref('191a'), ref('191b'))],
    ['REVOKE demonstration', 'SHOW GRANTS before and after, and a new divya session each time: the SELECT works '
                             'before the REVOKE and fails with ERROR 1142 after it (Fig. %s)' % ref('192')],
    ['Least privilege proof', 'Viewer, analyst and admin log in and try forbidden operations: ERROR 1142, 1369 and 1644 '
                              '(Fig. %s, %s, %s, %s); tests S01-S12, V01-V05, A01-A07 (section 16)' % (ref('193'), ref('194a'), ref('194b'), ref('195'))],
    ['Secure exposure', 'Analyst and viewer have no privilege on any base table; they use views and procedures only. '
                        'The analyst\'s procedures check the caller (Fig. %s)' % ref('194b')],
    ['Audit and recovery (beyond the template)', 'incident_audit (Fig. %s), SQL injection (Fig. %s-%s), point-in-time '
                                                 'recovery (section 15)' % (ref('195'), ref('sqli_setup'), ref('sqli_attack2'))],
], [3000, 6360])
part_fig('190_sec_roles_users', list(range(18)), 'Roles, grants and users', '190')
part_fig('191_sec_show_grants', [0, 1, 2], 'SHOW GRANTS for the three roles', '191a')
part_fig('191_sec_show_grants', [3, 4, 5], 'A user\'s grants show only the role; USING expands it', '191b')
revoke_lines = []
for st, who in (('192_sec_revoke_1_grant', '-- root'), ('192_sec_revoke_2__as_divya', '-- divya, new session'),
                ('192_sec_revoke_3_revoke', '-- root'), ('192_sec_revoke_4__as_divya', '-- divya, new session')):
    revoke_lines += [('err', who)] + session_lines(load(st)) + [('res', '')]
path = os.path.join(CUSTOM, 'revoke.png'); w, h = render(revoke_lines[:-1], path)
fig(path, 'GRANT, then REVOKE: what the viewer can do before and after', key='192', wpx=w, hpx=h)
p('Logged in as the viewer, divya.iyer: reports work, everything else is refused.')
step_fig('193_sec_viewer__as_divya', 'Viewer: allowed and forbidden operations')
alias['193'] = len(figs)
p(T(488))
part_fig('194_sec_analyst__as_rahul', list(range(0, 8)), 'Analyst: own incidents only; tables and DDL refused', '194a')
p('The privilege-escalation fix: sp_whoami shows that rahul calls it but it runs with root\'s rights, so '
  'sp_assign_incident must check the caller itself. Giving his incident away and taking a colleague\'s are refused; '
  'claiming an unassigned incident works. Writing to ioc directly is refused, but reporting a compromised internal '
  'host through sp_report_ioc works, and the retro-hunt trigger finds its 24 old log lines on 9 assets.')
part_fig('194_sec_analyst__as_rahul', list(range(8, 15)), 'Analyst: the procedure checks its caller; IOCs only through a procedure', '194b')
p('Logged in as the admin, ananya.rao: the audit trail names rahul for the changes he made through the view and '
  'through the procedure, and the admin can neither delete it, add a forged row, truncate it nor drop its trigger: '
  'each attempt is refused for lack of privilege (ERROR 1142).')
step_fig('195_sec_admin__as_ananya', 'Admin: the audit trail, and attempts to erase it')
alias['195'] = len(figs)

h3('SQL injection: why GRANT alone does not protect')
p('Two procedures let an analyst search his own incidents by title. The unsafe one pastes the search text into '
  'the SQL with CONCAT; the safe one passes it as a parameter (?). Both run with the definer\'s rights.')
part_fig('196_sec_sqli_setup', [0, 1], 'The unsafe (CONCAT) and the safe (parameterised) search procedure', 'sqli_setup')
p('Rahul only has EXECUTE on the procedure. The text %\' OR 1=1 --  turns the WHERE clause into '
  '"(... AND title LIKE \'%%\') OR 1=1", so every incident comes back, read with root\'s rights; a UNION returns '
  'every analyst\'s email from a table he cannot read. Stacked statements are refused, because PREPARE accepts one '
  'statement only. The parameterised procedure treats the same text as data and returns nothing. It also takes the '
  'caller\'s identity only from the analyst table: it clears the session variable it uses first and refuses a '
  'caller it cannot match, so setting @me by hand does not help (fixed in Review 3, test T35).')
part_fig('197_sec_sqli__as_rahul', [0, 1, 2], 'Injection through the unsafe procedure', 'sqli_attack1')
part_fig('197_sec_sqli__as_rahul', [3, 4, 5], 'Stacked statement refused; the safe procedure is not injectable', 'sqli_attack2')
step_fig('198_sec_sqli_cleanup', 'The vulnerable procedure is dropped after the demonstration')
p('Defences, in order of importance: never build SQL from user text (use parameters or static SQL); give code only '
  'the rights it needs (an INVOKER procedure, or a low-privilege definer instead of root); validate input. GRANT '
  'cannot help, because the injected SQL runs with whatever rights the vulnerable code has. Here that was root, so '
  'the same hole could have read any table on the server, including the password hashes in mysql.user; a definer '
  'account limited to this database would have contained it (section 19).')

# ================================================================= 13 transactions + concurrency
h1('13. Transactions and Concurrency')
p([{'text': 'SAVEPOINT and COMMIT. ', 'b': True}, {'text': T(494).split('. ', 1)[1]}])
step_fig('170_txn_savepoint', 'SAVEPOINT, ROLLBACK TO SAVEPOINT and COMMIT')
p([{'text': 'ROLLBACK. ', 'b': True},
   {'text': 'The second line of the batch points to an asset that does not exist. The script then calls ROLLBACK, so '
            'the log count is unchanged (50,021 before and after).'}])
step_fig('171_txn_rollback', 'A failed batch, rolled back explicitly')
p([{'text': 'A failed statement does not roll back the transaction (found in Review 3). ', 'b': True},
   {'text': 'MySQL undoes only the statement that failed. If the script had said COMMIT instead of ROLLBACK, the '
            'good first line would have been kept and the batch would be half loaded. The Review 2 demonstration '
            'only worked because the script rolled back by hand.'}])
part_fig('172_txn_handler_rollback', [0, 1, 2, 3, 4, 5], 'One INSERT fails, COMMIT keeps the other: half a batch', 'trap')
p('The loader therefore handles it itself: sp_load_log_batch declares an EXIT HANDLER FOR SQLEXCEPTION that rolls '
  'back and re-raises the error. A bad batch leaves no rows; a good batch commits all three.')
part_fig('172_txn_handler_rollback', [6, 7, 8, 9, 10, 11], 'sp_load_log_batch: the handler rolls back the whole batch', 'handler')

h2('13.1 Concurrency')
p('Each scenario uses two mysql sessions at the same time: terminal A (root) and terminal B (ananya.rao, the admin). '
  'In the rehearsal the sessions were timed with DO SLEEP() so that B\'s statements land between A\'s; in the live '
  'demonstration they are typed step by step (demo/06_concurrency.md).')
conc = open(os.path.join(ROOT, 'demo', 'evidence', 'concurrency.txt'), encoding='utf-8').read()
sections = re.split(r'\n================ (.*?) ================\n', conc)


def conc_fig(title, caption, key, upto=None):
    body = sections[sections.index(title) + 1]
    a, b = re.split(r'---------------- terminal B ----------------\n', body.split('---------------- terminal A ----------------\n')[1])
    b = b.split('\n================')[0]
    lines = [('err', '-- Terminal A (root)')]
    lines += session_lines(parse(a, ''))
    lines += [('res', ''), ('err', '-- Terminal B (ananya.rao)')]
    bb = parse(b, '')
    lines += session_lines(bb[:upto] if upto else bb)
    lines = [(k, t) for k, t in lines if not t.startswith('SET SESSION')]
    path = os.path.join(CUSTOM, key + '.png')
    w, h = render(lines, path)
    fig(path, caption, key=key, wpx=w, hpx=h)


p([{'text': 'Lost update. ', 'b': True},
   {'text': 'Both sessions read incident 6 as MEDIUM and each raises it "one level" to HIGH. Two escalations happened, '
            'but the result is HIGH, not CRITICAL: B\'s escalation was lost. Its UPDATE matched the row but changed '
            'nothing (Changed: 0), because A had already written HIGH, and the audit trail shows the same: '
            'old_priority HIGH, new_priority HIGH.'}])
conc_fig('6.1 Lost update (no locking)', 'Lost update: both sessions write HIGH', 'conc1')
table(['Who', 'old_priority', 'new_priority'], [['root', 'MEDIUM', 'HIGH'], ['ananya.rao', 'HIGH', 'HIGH']], [3120, 3120, 3120])
p([{'text': 'The fix: lock the row when you read it. ', 'b': True},
   {'text': 'With SELECT ... FOR UPDATE, B waits until A commits, then reads HIGH and sets CRITICAL. Other fixes are '
            'optimistic versioning (a version column checked in the UPDATE\'s WHERE clause) or an atomic UPDATE that '
            'computes the new value from the current one.'}])
conc_fig('6.2 With SELECT ... FOR UPDATE', 'FOR UPDATE: B waits, reads HIGH, writes CRITICAL', 'conc2')
times = {k: v for k, v in re.findall(r'\| (\w+_at)\s*\|\n\+[-+]+\+\n\| (?:\w+\s+\| )?([\d-]+ [\d:.]+)',
                                       sections[sections.index('6.2 With SELECT ... FOR UPDATE') + 1])}
p(f'SYSDATE(6) is the clock at the moment each statement returned. B asked for the row at {times["b_asks_at"][11:]}, '
  f'A committed at {times["a_commits_at"][11:]}, and B received the row at {times["b_got_row_at"][11:]}: '
  'it waited for A\'s lock and then saw A\'s committed HIGH.')
p([{'text': 'Deadlock. ', 'b': True},
   {'text': 'A locks incident 3 then wants 6; B locks 6 then wants 3. InnoDB detects the cycle, rolls back B with '
            'ERROR 1213 and lets A finish. Prevention: lock rows in one fixed order (lowest incident_id first, as '
            'sp_escalate_incidents does) and retry on 1213.'}])
conc_fig('6.3 Deadlock', 'Deadlock detected; B is rolled back', 'conc3', upto=None)
p('SHOW ENGINE INNODB STATUS confirms it: "' + re.search(r'\*\*\* WE ROLL BACK TRANSACTION \(\d\)', conc).group(0)
  + '", transaction 2 being B.')
p([{'text': 'Isolation levels. ', 'b': True},
   {'text': 'In READ COMMITTED, A read incident 6 as OPEN, B changed it to INVESTIGATING, and A\'s second read inside '
            'the same transaction said INVESTIGATING (a non-repeatable read). In REPEATABLE READ, MySQL\'s default, the '
            'second read still said OPEN, because the transaction reads from its own snapshot.'}])
conc_fig('6.4a READ COMMITTED', 'READ COMMITTED: the second read sees B\'s committed change', 'conc4a')
conc_fig('6.4b REPEATABLE READ', 'REPEATABLE READ: the second read still sees the snapshot', 'conc4b')
table(['Isolation level', 'Dirty read', 'Non-repeatable read', 'Phantom read'], [
    ['READ UNCOMMITTED', 'possible', 'possible', 'possible'],
    ['READ COMMITTED', 'prevented', f'possible (Fig. {ref("conc4a")})', 'possible'],
    ['REPEATABLE READ (default)', 'prevented', f'prevented (Fig. {ref("conc4b")})', 'prevented for plain reads (snapshot); locking reads use next-key locks'],
    ['SERIALIZABLE', 'prevented', 'prevented', 'prevented'],
], [2600, 1700, 2100, 2960])
t65 = {k: v for k, v in re.findall(r'\| (\w+_at)\s*\|\n\+[-+]+\+\n\| ([\d-]+ [\d:.]+)',
                                    sections[sections.index('6.5 Two sessions add the same bad IP at once') + 1])}
p([{'text': 'Our own IOC trigger under concurrency. ', 'b': True},
   {'text': 'Two sessions add the same bad IP at once. A inserts and holds its transaction open; B starts at '
            f'{t65["b_starts_at"][11:]} and its INSERT waits, because the SELECT inside a trigger fired by an INSERT '
            f'is a locking read. A commits at {t65["a_commits_at"][11:]}, and B is rejected by trg_ioc_no_overlap at '
            f'{t65["b_rejected_at"][11:]}: only one version is stored. With unlucky timing InnoDB could instead report '
            'a deadlock (ERROR 1213) and roll one session back; either way the rule holds.'}])
conc_fig('6.5 Two sessions add the same bad IP at once', 'The second INSERT waits for the first, then is rejected', 'conc5')

# ================================================================= 14 indexes
h1('14. Indexing and Query Optimisation')
p('Besides the primary keys and the indexes MySQL creates for foreign keys, we added five. idx_src_time '
  '(src_ip, log_time) on network_log serves the retro-hunt and is measured below. idx_time and idx_src on attack_event '
  'serve searches by time and by source IP; on today\'s 30 attacks the optimiser may still prefer a full scan, and '
  'they are there for when the table grows. idx_value on ioc finds an indicator by value (used by the overlap '
  'trigger), and idx_incident (incident_id, changed_at) on incident_audit returns one incident\'s history in order.')
step_fig('180_idx_list', 'Indexes on network_log and attack_event')
p(T(504))
step_fig('181_idx_explain_before', 'EXPLAIN without idx_src_time: full table scan')
step_fig('182_idx_explain_after', 'EXPLAIN with idx_src_time: range read of 8 rows')
table(ROWS(509)[0], [[c.replace('50,163', f'{SCAN_ROWS:,}') for c in r] for r in ROWS(509)[1:]],
      [3000, 3180, 3180])
p(f'Row counts in EXPLAIN are estimates from the table statistics, so they move slightly after every '
  f'ANALYZE TABLE ({SCAN_ROWS:,} in this run, against 50,021 rows actually stored); the access type is '
  f'what matters: ALL reads every row, range reads only the matching slice of the index.')
p(T(511))
p('Reading the EXPLAIN with the index, column by column:', keepNext=True)
table(['Column', 'Value', 'Meaning'], [
    ['type', 'range (was ALL)', 'Read one slice of the index instead of every row'],
    ['key', 'idx_src_time', 'The index the optimiser chose'],
    ['key_len', '187', 'Both index columns are used: src_ip VARCHAR(45) in utf8mb4 takes 45 x 4 + 2 bytes, plus 5 bytes '
                       'for the DATETIME log_time'],
    ['rows', f'{RANGE_ROWS} (was {SCAN_ROWS:,})', 'Estimated rows to read'],
    ['Extra', 'Using index condition', 'The log_time range is checked inside the index before a row is fetched; '
                                       'dst_asset_id is not in the index, so each matching row is still read'],
], [1500, 2200, 5660])
h2('14.1 When an index is not used')
p('idx_src_time is (src_ip, log_time). A filter on log_time alone cannot seek it, because the index is sorted by '
  'src_ip first (the leftmost-prefix rule). With skip scan switched off MySQL reads the whole index; MySQL 8.0.13 '
  'and later can instead skip-scan it, doing one range read for each of the 1,004 distinct source IPs.')
bl183 = load('183_idx_not_used')
part_fig('183_idx_not_used', [0, 1], 'Leftmost prefix: full index scan, or skip scan', 'idx_prefix', blocks_=bl183)
p('A function on the indexed column hides it from the optimiser: SUBSTRING_INDEX(src_ip, ...) reads the whole index, '
  'while the same filter written as a prefix LIKE becomes a range read of about 16 rows.')
part_fig('183_idx_not_used', [2, 3], 'A function hides the index; a prefix LIKE uses it', 'idx_func', blocks_=bl183)
p('EXPLAIN ANALYZE runs the query and reports real times and row counts next to the estimates: 8 rows, read in '
  f'{ANALYZE_MS:.3f} ms through idx_src_time.')
part_fig('183_idx_not_used', [4], 'EXPLAIN ANALYZE of the retro-hunt lookup', 'idx_analyze', wrap=110, blocks_=bl183)
p('Indexes are not free: every INSERT into network_log must also update each index, and they take disk and memory. '
  'On a 10-row table such as asset an index brings nothing, because the whole table is one page.')

# ================================================================= 15 backup
h1('15. Backup and Point-in-Time Recovery')
p('A full backup is a snapshot of one moment. The binary log records every change after it, in order, each at a '
  'numbered position. To undo a mistake made at 3:15 PM we restore the snapshot and replay the binary log from the '
  'snapshot\'s position up to the position just before the bad statement. We stop at a position, not a time: '
  '--stop-datetime has one-second resolution, and the bad statement may share its second with good ones. This was '
  'rehearsed on a separate MySQL 8.0.46 server, not run live.')
table(['Step', 'Command or statement', 'Result'], [
    ['1. Nightly full backup', {'text': 'mysqldump --single-transaction --source-data=2\n  --routines --triggers --events\n  --databases sentinelx --result-file=sentinelx_full.sql', 'code': True},
     'Consistent snapshot; the file records binlog.000002 position 16453827'],
    ['2. Work after the backup', {'text': "INSERT INTO attack_event ... '203.0.113.123' ...\nUPDATE incident SET status = 'INVESTIGATING'\n  WHERE incident_id = 6;", 'code': True},
     'Must survive the recovery'],
    ['3. The accident', {'text': 'DELETE FROM asset_vulnerability;', 'code': True}, 'All 9 patch records gone'],
    ['4. Find it', {'text': "SHOW BINLOG EVENTS IN 'binlog.000002'\n  FROM 16453827;", 'code': True},
     'The bad transaction starts at position 16454920'],
    ['5. Restore and replay', {'text': 'mysql --init-command="SET sql_log_bin=0"\n  -e "source sentinelx_full.sql"\nmysqlbinlog --read-from-remote-server\n  --start-position=16453827\n  --stop-position=16454920 --disable-log-bin\n  --result-file=replay.sql binlog.000002\nmysql -e "source replay.sql"', 'code': True},
     'Snapshot back, then the two good transactions replayed'],
    ['6. Check', {'text': 'SELECT COUNT(*) FROM asset_vulnerability;', 'code': True},
     '9 rows back; the post-backup attack and the status change are present (Fig. %s)' % ref('pitr_check')],
], [1800, 4560, 3000])
pitr = open(os.path.join(ROOT, 'demo', 'evidence', 'pitr.txt'), encoding='utf-8').read()
ev = pitr.split('== binlog events')[1].split('\n', 1)[1].split('\n== replay.sql')[0]
ev_lines = [l for l in ev.split('\n') if l.startswith(('+', '|'))]
lines = [('prompt', "SHOW BINLOG EVENTS IN 'binlog.000002' FROM 16453827 LIMIT 19;")] + [('res', l) for l in ev_lines]
path = os.path.join(CUSTOM, 'pitr_events.png'); w, h = render(lines, path)
fig(path, 'The binary log after the backup: two good transactions, then the DELETE at 16454920', key='pitr', wpx=w, hpx=h)
chk = pitr.split('== after restore + replay ==')[1]
chk_tables = re.findall(r'(\+[-+]+\+\n\|.*?\|\n\+[-+]+\+\n(?:\|.*?\|\n)+\+[-+]+\+)', chk)
prompts = ['SELECT COUNT(*) AS patches FROM asset_vulnerability;',
           "SELECT COUNT(*) AS post_backup_attack FROM attack_event WHERE src_ip = '203.0.113.123';",
           'SELECT incident_id, status FROM incident WHERE incident_id = 6;']
chk_lines = []
for pr, tb in zip(prompts, chk_tables):
    chk_lines += [('prompt', pr)] + [('res', l) for l in tb.split('\n')] + [('res', '')]
path = os.path.join(CUSTOM, 'pitr_check.png'); w, h = render(chk_lines[:-1], path)
fig(path, 'After restore and replay: the deleted rows are back and the later work is kept', key='pitr_check', wpx=w, hpx=h)
p('Durability after a power failure is a different mechanism: InnoDB writes every change to its redo log and '
  'flushes it to disk at each COMMIT (innodb_flush_log_at_trx_commit = 1), the doublewrite buffer protects against '
  'half-written pages, and after a crash InnoDB replays the redo log. A committed DELETE is durable too; only a backup '
  'and the binary log can undo it. Users and grants live in the mysql schema and are re-created by 12_security.sql '
  'rather than by this dump.')

# ================================================================= 16 testing
h1('16. Testing')
p(f'13_tests.sql holds {N_TESTS} automatic tests. Each one states a claim made in this report and checks it: either a value '
  '(sp_check) or the exact error number a statement must raise (sp_expect_error, which runs the statement as dynamic '
  'SQL and catches the error). Both helpers are SQL SECURITY INVOKER, so a test never runs with more rights than the '
  'user running it. The runner executes them as root and then logged in as the analyst, the viewer and the admin.')
user_of = TEST_STEPS
rows, summary = [], []
for step, user in user_of.items():
    txt = open(os.path.join(MO, step + '.txt'), encoding='utf-8').read()
    for m in re.finditer(r'^\| ([TSVA]\d\d)\s*\| (.*?)\s*\| (.*?)\s*\| (.*?)\s*\| (PASS|FAIL)\s*\|$', txt, re.M):
        rows.append([m.group(1), user, m.group(2), m.group(3), m.group(4), m.group(5)])
    s = re.findall(r'^\|\s+(\d+) \|\s+(\d+) \|$', txt, re.M)[-1]
    summary.append([user, s[0], s[1]])
rows.sort(key=lambda r: ('TSVA'.index(r[0][0]), int(r[0][1:])))
table(['ID', 'Run as', 'What it checks', 'Expected', 'Actual', 'Result'], rows, [600, 1350, 4110, 1200, 1200, 900], small=True)
p('Error numbers: 1062 duplicate key, 1142 privilege denied, 1265 ENUM value rejected, 1288 view not updatable, '
  '1369 CHECK OPTION failed, 1370 EXECUTE denied, 1451/1452 foreign key, 1644 SIGNAL from our triggers and procedures, '
  '3819 CHECK constraint; 0 means the statement had to succeed.')
table(['Run as', 'Passed', 'Failed'], summary + [['Total', str(sum(int(s[1]) for s in summary)),
                                                    str(sum(int(s[2]) for s in summary))]], [3120, 3120, 3120])
p('Each test step ends by printing its own passed/failed count; the totals above are read from those lines.')

# ================================================================= 17 scope revision
h1('17. Scope Revision and Design Changes since Review 2')
md = open(os.path.join(ROOT, 'reports', 'Review3_scope_revision.md'), encoding='utf-8').read()
sec11 = md.split('## 1.1 What we removed, and why')[1].split('## 1.2')[0]
paras = [x.strip() for x in sec11.split('\n\n') if x.strip() and not x.strip().startswith('|')]
for x in paras:
    p(re.sub(r'`([^`]*)`', r'\1', x.replace('\n', ' ')))
tbl = [l for l in sec11.split('\n') if l.startswith('|')][2:]
table(['Removed', 'Where Review 2 claimed it', 'Review 3 status'],
      [[re.sub(r'`([^`]*)`', r'\1', c.strip()) for c in l.strip('|').split('|')] for l in tbl], [2200, 2300, 4860])
p('Design changes since Review 2 (numbering continues from the Review 2 change log):', keepNext=True)
chg = md.split('## 1.2 Design changes since Review 2')[1].split('## 1.3')[0]
crow = [l for l in chg.split('\n') if l.startswith('| ') and not l.startswith('| #') and not l.startswith('| ---')]
crows = [[re.sub(r'`([^`]*)`', r'\1', c.strip()) for c in l.strip('|').split('|')] for l in crow]
crows = [[n, c, re.split(r'(?<=[.:])\s', r, maxsplit=1)[0]] for n, c, r in crows]
table(['#', 'Change', 'Reason (details in the section concerned)'], crows, [500, 3600, 5260], small=True)

# ================================================================= 18 checklist
h1('18. Review 3 Requirements Checklist', new_page=False)
table(['Requirement', 'Evidence', 'Where', 'Status'], [
    ['Complete database with all tables populated', '17 tables, 50,021 log lines, 30 attacks, row counts', '9, 10', 'Done'],
    ['Full scripts, re-runnable from scratch', '01_ddl.sql to 13_tests.sql run cleanly on an empty server; one-click runner; fixed ERROR 1046', '10, 17', 'Done'],
    ['Advanced SQL', f'{N_QUERIES} queries in 7 categories; 11 complex queries, each matching its hand prediction', '11, 12.1', 'Done'],
    ['Views (2-3 minimum)', '6 views with the full template, updatable or not for each: 5-table join, aggregated, row-restricting, v_ioc, two Review 1 views', '12.2', 'Done'],
    ['Stored procedures (at least 2)', 'sp_assign_incident, sp_attack_report, sp_report_ioc, sp_whoami, sp_load_log_batch, search pair', '12.3, 12.7, 13', 'Done'],
    ['User-defined functions (at least 2)', 'fn_severity_label, fn_asset_risk', '12.4', 'Done'],
    ['Triggers (at least 2)', '9 triggers: auto-incident, retro-hunt, three IOC rules, four for the audit trail', '12.5', 'Done'],
    ['Cursors (at least 2)', 'sp_escalate_incidents, sp_asset_risk_report', '12.6', 'Done'],
    ['Transactions and concurrency', 'SAVEPOINT, ROLLBACK, exit-handler rollback; lost update, FOR UPDATE, deadlock, two isolation levels and the IOC trigger, each run in two real sessions', '13', 'Done'],
    ['Indexing and query optimisation', f'EXPLAIN before/after ({SCAN_ROWS:,} estimated rows to {RANGE_ROWS}); leftmost prefix, skip scan, function on column, EXPLAIN ANALYZE', '14', 'Done'],
    ['Security implementation', '3 roles, 3 users, GRANT/REVOKE shown by behaviour, least privilege, secure exposure, lockout, forge-proof audit trail, SQL injection', '12.7', 'Done'],
    ['Testing (15 or more cases)', f'{N_TESTS} tests run as four users, {N_TESTS} pass', '16', 'Done'],
    ['Normalisation and anomalies', 'Normalisation steps, an FD check and an update anomaly shown on the data', '9.1', 'Done'],
    ['Backup and recovery', 'mysqldump plus binary log, rehearsed to the position before a DELETE', '15', 'Done'],
    ['Final report', 'This document', '-', 'Done'],
    ['Live demonstration and viva', 'Run sheet and rerunnable segment files (demo/README.md), viva map (docs/viva_map.md)', 'repository', 'Ready'],
], [2500, 4560, 1300, 1000])

# ================================================================= 20-23
h1('19. Limitations and Future Scope', new_page=False)
lim = md.split('## 1.3 Limitations (replaces Review 2 section 17)')[1].split('# 2.')[0]
bullets([re.sub(r'`([^`]*)`', r'\1', l[2:].strip()) for l in lim.split('\n') if l.startswith('- ')] + [
    'Future: run the procedures under a dedicated low-privilege definer account instead of root, so that a mistake '
    'in one procedure cannot reach the whole database.',
    'Future: very high log volumes would need archive tables or partitioning for old logs, and a streaming loader.'])

h1('20. Conclusion', new_page=False)
p('Review 1 gave us a clean 3NF design and Review 2 showed it working. Review 3 made it defensible. Testing our own '
  'work found eight real defects: a script that only ran because our runner hid its mistake; a stored procedure that '
  'let an analyst bypass the row-level security we were proud of; a rollback demonstration that relied on a manual '
  'ROLLBACK; a trigger that made closed indicators permanent; an audit trail the administrator could add forged rows '
  'to; indicator history that an UPDATE could rewrite; times that a session could backdate with SET timestamp; and a '
  'search procedure that trusted a session variable. Each is fixed and has a test. The database now enforces its own '
  'rules, limits every user to what they need, records who changed each incident, behaves correctly in every '
  f'concurrent scenario we ran, recovers from an accidental delete, and proves this with {N_TESTS} tests that pass on '
  'a clean build. The biggest lesson was that a security feature is only as strong as the code that runs with more '
  'rights than its caller.')

h1('21. Acknowledgement', new_page=False)
p('An AI assistant (Claude, by Anthropic) was used to review our SQL for defects, to help write parts of the Review 3 '
  'scripts and to help draft this report. Every script was run on MySQL 8.0.46, and every result in this report is '
  'the real output of that run.')

h1('22. Work Break Down', new_page=False)
wb = [r[:] for r in ROWS(527)[1:]]
wb[0][2] = wb[0][2].replace('FastAPI backend', 'FastAPI backend (dropped from scope, section 17)')
wb[2][1] = 'Yashneil Purkayastha'
wb[2][2] = wb[2][2].replace('React dashboard', 'React dashboard (dropped from scope, section 17)').replace('this report', 'the Review 2 report')
for r, resp in zip(wb, (
        'Transactions and concurrency (13), indexing and optimisation (14), backup and recovery (15), IOC trigger '
        'fixes. Demo: steps 1 and 4, introduction and close',
        'Security (12.7): role and privilege fixes, audit trail, SQL injection; views (12.2). Demo: step 2 and '
        'concurrency terminal A',
        f'Testing (16, {N_TESTS} tests), complex-query verification (12.1), normalisation evidence (9.1), this report. '
        'Demo: SQL injection, steps 3 and 5, concurrency terminal B')):
    r.append(resp)
table(['Registration Number', 'Name', 'Work Assigned (Reviews 1 and 2)', 'Review 3 responsibility (presents and defends)'], wb,
      [1500, 1500, 3260, 3100])

h1('23. Review Evaluation', new_page=False)
table(['COMPONENT', 'MARKS', 'SHLOK GUPTA', 'SHREYA BHUSHAN', 'YASHNEIL PURKAYASTHA'],
      [['Project work with screenshot', '5', '', '', ''], ['Viva', '5', '', '', ''], ['TOTAL', '10 MARKS', '', '', '']],
      [2560, 1300, 1800, 1850, 1850])

# ---------------------------------------------------------------- resolve figure references, write
def resolve(x):
    if isinstance(x, str):
        return re.sub(r'\{\{fig:([^}]+)\}\}', lambda m: str(figs.get(m.group(1)) or alias[m.group(1)]), x)
    if isinstance(x, list):
        return [resolve(y) for y in x]
    if isinstance(x, dict):
        return {k: resolve(v) for k, v in x.items()}
    return x


spec = {'title': 'SentinelX Review 3 Report', 'author': 'Shlok Gupta, Shreya Bhushan, Yashneil Purkayastha',
        'blocks': resolve(blocks)}
json.dump(spec, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(blocks), 'blocks,', len(figs), 'figures,', len(rows), 'test rows')
