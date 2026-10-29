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
blocks, figs = [], {}


def add(**b):
    blocks.append(b)


def h1(t, new_page=True): add(t='h1', text=t, newPage=new_page)
def h2(t): add(t='h2', text=t)
def h3(t): add(t='h3', text=t)
def p(text, **kw): add(t='p', runs=text if isinstance(text, list) else [{'text': text}], **kw)
def bullets(items): add(t='bullets', items=items)
def code(text): add(t='code', text=text.strip('\n'))
def table(header, rows, cols, **kw): add(t='table', header=header, rows=rows, cols=cols, **kw)


def size(wpx, hpx, max_w=6.5, max_h=8.2):
    w = min(max_w, wpx / 210.0)
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
  'with EXPLAIN and EXPLAIN ANALYZE, backup with point-in-time recovery, and 49 automatic tests that run as four '
  'different users. While testing our own design we found and fixed four real defects, including a privilege '
  'escalation through a stored procedure; they are described where they occur. Every statement in this report was '
  'run on MySQL 8.0.46 and every screenshot is its real output.')
p('We also narrowed the scope. The application layer (FastAPI, React) and the machine-learning parts described in '
  'Review 2 were never built and have been removed; section 17 lists every change and the reason for it.')
add(t='pagebreak')
add(t='toc')

# ================================================================= 1-5
h1('1. Introduction')
p(T(41))
p(T(42))
p('Review 3 is about turning that working design into something we can defend: every rule enforced by the '
  'database, every user limited to what they need, every change traceable, every mistake recoverable, and every '
  'claim backed by a test that passes.')

h1('2. Objectives', new_page=False)
bullets([T(i) for i in range(44, 49)] + [
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
bullets([T(63), T(64), T(65),
         'Python 3 for the scripts in tools/ that generate the test data, the step files, the screenshots and two of '
         'the diagrams.',
         'Windows PowerShell for the one-click runner (runner/RUN_ME.bat).',
         T(68),
         'An AI assistant (Claude, by Anthropic) was used to review our SQL for defects and to help draft parts of the '
         'Review 3 scripts and this report. Every script was run on MySQL 8.0.46 and every output shown is the real '
         'result.'])

# ================================================================= 6-8
h1('6. System Architecture')
p('The database is the whole system. Test data is loaded in batches, each batch as one transaction. Everything '
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
             'owner. Nobody but the DBA can remove it.',
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
p(T(85).replace('All 16 tables', 'All 16 tables, and the audit table added in Review 3,'))
step_fig('029_ddl_show_tables', 'SHOW TABLES after running the 17 CREATE TABLE statements')
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
                      'purpose, so the trail outlives a deleted incident, and two more triggers make it append-only.',
}
new_nf = {
    'attack_event': 'Normal form: Everything depends on event_id. triage_priority is an analyst decision, not a '
                    'function of severity (events 5 and 6 both have severity 9 but are CRITICAL and HIGH), so there '
                    'is no transitive dependency. src_country stays because an IP\'s location changes over time; '
                    'actor_id stays because malware is shared between groups. 3NF.',
    'incident_audit': 'Normal form: Everything depends on audit_id; the old and new values describe one change. 3NF.',
}
order = [re.sub(r'^\d{3}_ddl_', '', n) for n in sorted(META) if re.match(r'0[12]\d_ddl_', n)
         and not n.endswith('show_tables')]
for tname in order:
    h3('Table: ' + tname)
    p(new_desc.get(tname) or T(desc[tname][0]))
    table(['Attribute', 'Data Type', 'Constraint'], ATTRS[tname], [2300, 2200, 4860])
    num = [n for n in META if n.endswith('_ddl_' + tname)][0]
    step_fig(num, f'CREATE TABLE {tname} executed in MySQL')
    p([{'text': new_nf.get(tname) or T(desc[tname][1]), 'b': True}])

# ================================================================= 10 DML
h1('10. Data Population (INSERT, UPDATE, DELETE)')
p(T(201))
h3('INSERT')
step_fig('030_dml_insert_asset', 'INSERT of the 10 assets')
p(T(205))
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
step_fig('036_dml_row_counts', 'Row count of every table after loading')

# ================================================================= 11 queries
h1('11. SQL Implementation')
p(T(223))
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
cq_tables = [i for i, e in enumerate(R2) if e['t'] == 'tbl' and e['rows'] and len(e['rows']) == 7
             and e['rows'][1][1].startswith('CQ-')]
for i, (cid, (question, sql)) in zip(cq_tables, gen_steps.CQ.items()):
    rows = {r[0]: r[1] for r in ROWS(i)[1:]}
    n_next = len(figs) + 1
    if cid != 'CQ-01':
        add(t='pagebreak')
    p([{'text': cid, 'b': True}], keepNext=True)
    table(['Field', 'Content'], [
        ['ID', cid], ['Business question', question],
        ['SQL', {'text': sql.strip(), 'code': True}],
        ['Expected output', rows['Expected output']],
        ['Actual output screenshot', f'Below (Fig. {n_next})'],
        ['Explanation', rows['Explanation']],
    ], [2000, 7360])
    step_fig('%03d_%s' % (99 + int(cid[3:]), cid.replace('-', '')), f'{cid} actual output')

h2('12.2 Views')
p('Four views written for the project, plus the two Review 1 views (v_vulnerability for CVE severity and '
  'v_retro_hunt_summary for retro-hunt counts) that replaced stored columns. In Review 3 v_ioc was added so that '
  'analysts no longer need any access to the ioc table.')
for idx, (title, step) in zip((412, 416, 420), (('v_attack_details (joins 5 tables)', '120_view_attack_details'),
                                                ('v_asset_risk (aggregated)', '121_view_asset_risk'),
                                                ('v_my_incidents (security, row-restricting)', '122_view_my_incidents'))):
    rows = {r[0]: r[1] for r in ROWS(idx)[1:]}
    purpose = rows['Purpose'].replace('so the dashboard and search pages need no joins', 'so searches and reports need no joins')
    useful = rows['Why useful'].replace('pages query one object', 'queries use one object')
    p([{'text': title, 'b': True}], keepNext=True)
    table(['Field', 'Content'], [['Purpose', purpose],
                                 ['CREATE VIEW statement, query using the view and screenshot', f'Fig. {len(figs) + 1} below'],
                                 ['Why useful', useful]], [2600, 6760])
    step_fig(step, f'{title.split(" ")[0]}: definition, use and updatability')
p([{'text': 'v_ioc (security, Review 3)', 'b': True}], keepNext=True)
table(['Field', 'Content'], [
    ['Purpose', 'The indicator versions we currently believe (recorded_to IS NULL), so analysts can read indicators '
                'without any privilege on the ioc table.'],
    ['CREATE VIEW statement, query using the view and screenshot', f'Fig. {len(figs) + 1} below'],
    ['Why useful', 'Security and simplification: hides superseded versions and the base table. Updatable in principle '
                   '(one table, no aggregation), but analysts only get SELECT; new indicators go through sp_report_ioc.']],
    [2600, 6760])
step_fig('124_view_ioc', 'v_ioc: definition and use')
p([{'text': 'Review 1 views', 'b': True}], keepNext=True)
step_fig('123_view_review1_views', 'v_vulnerability and v_retro_hunt_summary')

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
   {'text': 'sp_report_ioc is the only way an analyst can add an indicator; it always sets recorded_from to the '
            'current time, so nobody can backdate when we learned about it. sp_whoami returns USER() and '
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
p(T(453) + ' Fixed in Review 3: trg_ioc_no_overlap now ignores versions that were closed with recorded_to. '
  'trg_ioc_no_delete tells users to close a version that way, but the overlap check still counted closed versions, '
  'so a corrected version could never be added (test T28).')
for k, name in enumerate(('trg_ioc_no_overlap', 'trg_ioc_no_delete', 'trg_ioc_retro_hunt'), 1):
    step_fig('151_trg_ioc_rules', name, part=k)
p(T(460))
step_fig('152_trg_retro_hunt_demo', 'Retro-hunt demonstration, then the two refused changes')
p([{'text': 'Audit triggers (Review 3). ', 'b': True},
   {'text': 'trg_incident_audit_update and trg_incident_audit_delete (AFTER UPDATE / AFTER DELETE on incident) write '
            'one row to incident_audit for every change, so it is recorded whether the change came through a view, a '
            'procedure or a direct statement. They record USER(), not CURRENT_USER(): inside a trigger CURRENT_USER() '
            'is the trigger\'s definer (root), which would make every row look the same. trg_audit_no_update and '
            'trg_audit_no_delete make the trail append-only. TRUNCATE does not fire triggers, which is why no role '
            'except root has the DROP privilege that TRUNCATE needs.'}])
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
  'is written to an audit trail that nobody but the DBA can remove; and the binary log makes mistakes recoverable '
  '(section 15). Passwords are not stored in our tables at all: users log in as MySQL accounts, whose passwords MySQL '
  'keeps as salted SHA-256 hashes with 5,000 rounds (caching_sha2_password).')
table(['Object', 'sx_admin', 'sx_analyst', 'sx_viewer'], [
    ['All 17 base tables', 'SELECT, INSERT, UPDATE, DELETE', '-', '-'],
    ['Schema changes (CREATE, ALTER, DROP, TRIGGER, GRANT)', '- (root, the DBA, only)', '-', '-'],
    ['v_my_incidents', 'SELECT, UPDATE', 'SELECT, UPDATE (own rows only)', '-'],
    ['v_attack_details, v_vulnerability, v_retro_hunt_summary, v_ioc', 'SELECT', 'SELECT', '-'],
    ['v_asset_risk', 'SELECT', 'SELECT', 'SELECT'],
    ['sp_assign_incident', 'EXECUTE', 'EXECUTE (claims for himself only)', '-'],
    ['sp_report_ioc, sp_whoami, sp_search_incidents', 'EXECUTE', 'EXECUTE', '-'],
    ['sp_attack_report', 'EXECUTE', 'EXECUTE', 'EXECUTE'],
    ['incident_audit', 'SELECT (append-only)', '-', '-'],
    ['Login', 'Locked for 1 day after 3 wrong passwords', 'Same', 'Same'],
    ['User (default role)', 'ananya.rao', 'rahul.mehta', 'divya.iyer'],
], [2700, 2200, 2500, 1960])
table(['Task', 'Evidence'], [
    ['Create 3 or more users/roles', 'CREATE ROLE and CREATE USER with default roles and lockout (Fig. %s)' % ref('190')],
    ['GRANT privileges per role matrix', 'GRANT script (Fig. %s) and SHOW GRANTS output (Fig. %s, %s)' % (ref('190'), ref('191a'), ref('191b'))],
    ['REVOKE demonstration', 'SHOW GRANTS before and after REVOKE (Fig. %s)' % ref('192')],
    ['Least privilege proof', 'Viewer, analyst and admin log in and try forbidden operations: ERROR 1142, 1369 and 1644 '
                              '(Fig. %s, %s, %s, %s); tests S01-S11, V01-V05, A01-A05 (section 16)' % (ref('193'), ref('194a'), ref('194b'), ref('195'))],
    ['Secure exposure', 'Analyst and viewer have no privilege on any base table; they use views and procedures only. '
                        'The analyst\'s procedures check the caller (Fig. %s)' % ref('194b')],
    ['Audit and recovery (beyond the template)', 'incident_audit (Fig. %s), SQL injection (Fig. %s-%s), point-in-time '
                                                 'recovery (section 15)' % (ref('195'), ref('sqli_setup'), ref('sqli_attack2'))],
], [3000, 6360])
part_fig('190_sec_roles_users', list(range(18)), 'Roles, grants and users', '190')
part_fig('191_sec_show_grants', [0, 1, 2], 'SHOW GRANTS for the three roles', '191a')
part_fig('191_sec_show_grants', [3, 4, 5], 'A user\'s grants show only the role; USING expands it', '191b')
step_fig('192_sec_revoke', 'GRANT, then REVOKE, with SHOW GRANTS before and after')
figs['192'] = len(figs)
p('Logged in as the viewer, divya.iyer: reports work, everything else is refused.')
step_fig('193_sec_viewer__as_divya', 'Viewer: allowed and forbidden operations')
figs['193'] = len(figs)
p(T(488))
part_fig('194_sec_analyst__as_rahul', list(range(0, 8)), 'Analyst: own incidents only; tables and DDL refused', '194a')
p('The privilege-escalation fix: sp_whoami shows that rahul calls it but it runs with root\'s rights, so '
  'sp_assign_incident must check the caller itself. Giving his incident away and taking a colleague\'s are refused; '
  'claiming an unassigned incident works. Writing to ioc directly is refused, but reporting a compromised internal '
  'host through sp_report_ioc works, and the retro-hunt trigger finds its 24 old log lines on 9 assets.')
part_fig('194_sec_analyst__as_rahul', list(range(8, 15)), 'Analyst: the procedure checks its caller; IOCs only through a procedure', '194b')
p('Logged in as the admin, ananya.rao: the audit trail names rahul for the changes he made through the view and '
  'through the procedure, and even the admin cannot delete it, truncate it or drop its trigger.')
step_fig('195_sec_admin__as_ananya', 'Admin: the audit trail, and attempts to erase it')
figs['195'] = len(figs)

h3('SQL injection: why GRANT alone does not protect')
p('Two procedures let an analyst search his own incidents by title. The unsafe one pastes the search text into '
  'the SQL with CONCAT; the safe one passes it as a parameter (?). Both run with the definer\'s rights.')
part_fig('196_sec_sqli_setup', [0, 1], 'The unsafe (CONCAT) and the safe (parameterised) search procedure', 'sqli_setup')
p('Rahul only has EXECUTE on the procedure. The text %\' OR 1=1 --  turns the WHERE clause into '
  '"(... AND title LIKE \'%%\') OR 1=1", so every incident comes back, read with root\'s rights; a UNION returns '
  'every analyst\'s email from a table he cannot read. Stacked statements are refused, because PREPARE accepts one '
  'statement only. The parameterised procedure treats the same text as data and returns nothing.')
part_fig('197_sec_sqli__as_rahul', [0, 1, 2], 'Injection through the unsafe procedure', 'sqli_attack1')
part_fig('197_sec_sqli__as_rahul', [3, 4, 5], 'Stacked statement refused; the safe procedure is not injectable', 'sqli_attack2')
step_fig('198_sec_sqli_cleanup', 'The vulnerable procedure is dropped after the demonstration')
p('Defences, in order of importance: never build SQL from user text (use parameters or static SQL); give code only '
  'the rights it needs (an INVOKER procedure, or a low-privilege definer instead of root); validate input. GRANT '
  'cannot help, because the injected SQL runs with whatever rights the vulnerable code has.')

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
    b = b.split('\nFinal priority')[0].split('\n(rehearsal ran B')[0]
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
            'but the result is HIGH, not CRITICAL: B overwrote A\'s change. The audit trail proves it: the second row '
            'says old_priority HIGH, new_priority HIGH.'}])
conc_fig('6.1 Lost update (no locking)', 'Lost update: both sessions write HIGH', 'conc1')
table(['Who', 'old_priority', 'new_priority'], [['root', 'MEDIUM', 'HIGH'], ['ananya.rao', 'HIGH', 'HIGH']], [3120, 3120, 3120])
p([{'text': 'The fix: lock the row when you read it. ', 'b': True},
   {'text': 'With SELECT ... FOR UPDATE, B waits until A commits, then reads HIGH and sets CRITICAL. Other fixes are '
            'optimistic versioning (a version column checked in the UPDATE\'s WHERE clause) or an atomic UPDATE that '
            'computes the new value from the current one.'}])
conc_fig('6.2 With SELECT ... FOR UPDATE', 'FOR UPDATE: B waits, reads HIGH, writes CRITICAL', 'conc2')
p([{'text': 'Deadlock. ', 'b': True},
   {'text': 'A locks incident 3 then wants 6; B locks 6 then wants 3. InnoDB detects the cycle, rolls back B with '
            'ERROR 1213 and lets A finish. Prevention: lock rows in one fixed order (lowest incident_id first, as '
            'sp_escalate_incidents does) and retry on 1213.'}])
conc_fig('6.3 Deadlock', 'Deadlock detected; B is rolled back', 'conc3', upto=None)
p([{'text': 'Isolation levels. ', 'b': True},
   {'text': 'In READ COMMITTED, A read incident 6 as OPEN, B changed it to INVESTIGATING, and A\'s second read inside '
            'the same transaction said INVESTIGATING (a non-repeatable read). In REPEATABLE READ, MySQL\'s default, the '
            'second read still said OPEN, because the transaction reads from its own snapshot.'}])
table(['Isolation level', 'Dirty read', 'Non-repeatable read', 'Phantom read'], [
    ['READ UNCOMMITTED', 'possible', 'possible', 'possible'],
    ['READ COMMITTED', 'prevented', 'possible (shown)', 'possible'],
    ['REPEATABLE READ (default)', 'prevented', 'prevented (shown)', 'prevented for plain reads (snapshot); locking reads use next-key locks'],
    ['SERIALIZABLE', 'prevented', 'prevented', 'prevented'],
], [2600, 1700, 2100, 2960])
p([{'text': 'Our own triggers are safe under concurrency. ', 'b': True},
   {'text': 'When two sessions insert the same bad IP at the same moment, the second waits about 3 seconds and is then '
            'rejected by trg_ioc_no_overlap: the SELECT inside a trigger fired by an INSERT is a locking read, so it '
            'sees the first row once that commits. Two simultaneous severity-9 attacks on the same asset were grouped '
            'into one incident in the same way.'}])

# ================================================================= 14 indexes
h1('14. Indexing and Query Optimisation')
p(T(501))
step_fig('180_idx_list', 'Indexes on network_log and attack_event')
p(T(504))
step_fig('181_idx_explain_before', 'EXPLAIN without idx_src_time: full table scan')
step_fig('182_idx_explain_after', 'EXPLAIN with idx_src_time: range read of 8 rows')
table(ROWS(509)[0], ROWS(509)[1:], [3000, 3180, 3180])
p(T(511))
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
  'about 0.1 ms through idx_src_time.')
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
     '9 rows back; the post-backup attack and status change are present; triggers restored'],
], [1800, 4560, 3000])
pitr = open(os.path.join(ROOT, 'demo', 'evidence', 'pitr.txt'), encoding='utf-8').read()
ev = pitr.split('== binlog events')[1].split('\n', 1)[1].split('\n== replay.sql')[0]
ev_lines = [l for l in ev.split('\n') if l.startswith(('+', '|'))]
lines = [('prompt', "SHOW BINLOG EVENTS IN 'binlog.000002' FROM 16453827 LIMIT 19;")] + [('res', l) for l in ev_lines]
path = os.path.join(CUSTOM, 'pitr_events.png'); w, h = render(lines, path)
fig(path, 'The binary log after the backup: two good transactions, then the DELETE at 16454920', key='pitr', wpx=w, hpx=h)
p('Durability after a power failure is a different mechanism: InnoDB writes every change to its redo log and '
  'flushes it to disk at each COMMIT (innodb_flush_log_at_trx_commit = 1), the doublewrite buffer protects against '
  'half-written pages, and after a crash InnoDB replays the redo log. A committed DELETE is durable too; only a backup '
  'and the binary log can undo it. Users and grants live in the mysql schema and are re-created by 12_security.sql '
  'rather than by this dump.')

# ================================================================= 16 testing
h1('16. Testing')
p('13_tests.sql holds 49 automatic tests. Each one states a claim made in this report and checks it: either a value '
  '(sp_check) or the exact error number a statement must raise (sp_expect_error, which runs the statement as dynamic '
  'SQL and catches the error). Both helpers are SQL SECURITY INVOKER, so a test never runs with more rights than the '
  'user running it. The runner executes them as root and then logged in as the analyst, the viewer and the admin.')
user_of = {'200_tests': 'root', '201_tests__as_rahul': 'rahul (analyst)', '202_tests__as_divya': 'divya (viewer)',
           '203_tests__as_ananya': 'ananya (admin)'}
rows, summary = [], []
for step, user in user_of.items():
    txt = open(os.path.join(MO, step + '.txt'), encoding='utf-8').read()
    for m in re.finditer(r'^\| ([TSVA]\d\d)\s*\| (.*?)\s*\| (.*?)\s*\| (.*?)\s*\| (PASS|FAIL)\s*\|$', txt, re.M):
        rows.append([m.group(1), user, m.group(2), m.group(3), m.group(4), m.group(5)])
    s = re.findall(r'^\|\s+(\d+) \|\s+(\d+) \|$', txt, re.M)[-1]
    summary.append([user, s[0], s[1]])
rows.sort(key=lambda r: ('TSVA'.index(r[0][0]), int(r[0][1:])))
table(['ID', 'Run as', 'What it checks', 'Expected', 'Actual', 'Result'], rows, [600, 1350, 4110, 1200, 1200, 900])
p('Error numbers: 1062 duplicate key, 1142 privilege denied, 1265 ENUM value rejected, 1288 view not updatable, '
  '1369 CHECK OPTION failed, 1370 EXECUTE denied, 1451/1452 foreign key, 1644 SIGNAL from our triggers and procedures, '
  '3819 CHECK constraint; 0 means the statement had to succeed.')
table(['Run as', 'Passed', 'Failed'], summary + [['Total', str(sum(int(s[1]) for s in summary)),
                                                    str(sum(int(s[2]) for s in summary))]], [3120, 3120, 3120])
bl = load('200_tests')
part_fig('200_tests', [5, 7, 26, len(bl) - 1], 'Four of the root tests and the root summary', 'tests_root', blocks_=bl)
bl = load('201_tests__as_rahul')
part_fig('201_tests__as_rahul', [1, 6, len(bl) - 1], 'Analyst tests (two shown) and the analyst summary', 'tests_rahul', blocks_=bl)

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
crows.append(['27', 'Relational schema diagram redrawn from the DDL (tools/draw_relational_schema.py)',
              'The hand-drawn Review 2 version still showed event_time and log_time inside primary keys, removed in '
              'Review 2 (change 10), and the two ML columns.'])
table(['#', 'Change', 'Reason'], crows, [500, 3300, 5560])

# ================================================================= 18 checklist
h1('18. Review 3 Requirements Checklist', new_page=False)
table(['Requirement', 'Evidence', 'Where', 'Status'], [
    ['Complete database with all tables populated', '17 tables, 50,021 log lines, 30 attacks, row counts', '9, 10', 'Done'],
    ['Full scripts, re-runnable from scratch', '01_ddl.sql to 13_tests.sql run cleanly on an empty server; one-click runner; fixed ERROR 1046', '10, 17', 'Done'],
    ['Advanced SQL', '40 queries in 7 categories; 11 complex queries with expected and actual output', '11, 12.1', 'Done'],
    ['Views (2-3 minimum)', '6 views: 5-table join, aggregated, row-restricting, v_ioc, two Review 1 views', '12.2', 'Done'],
    ['Stored procedures (at least 2)', 'sp_assign_incident, sp_attack_report, sp_report_ioc, sp_whoami, sp_load_log_batch, search pair', '12.3, 12.7, 13', 'Done'],
    ['User-defined functions (at least 2)', 'fn_severity_label, fn_asset_risk', '12.4', 'Done'],
    ['Triggers (at least 2)', '8 triggers: auto-incident, retro-hunt, IOC rules, audit trail', '12.5', 'Done'],
    ['Cursors (at least 2)', 'sp_escalate_incidents, sp_asset_risk_report', '12.6', 'Done'],
    ['Transactions and concurrency', 'SAVEPOINT, ROLLBACK, exit-handler rollback; lost update, FOR UPDATE, deadlock, isolation levels', '13', 'Done'],
    ['Indexing and query optimisation', 'EXPLAIN before/after (50,163 rows to 8); leftmost prefix, skip scan, function on column, EXPLAIN ANALYZE', '14', 'Done'],
    ['Security implementation', '3 roles, 3 users, GRANT/REVOKE, least privilege, secure exposure, lockout, audit trail, SQL injection', '12.7', 'Done'],
    ['Testing (15 or more cases)', '49 tests run as four users, 49 pass', '16', 'Done'],
    ['Backup and recovery', 'mysqldump plus binary log, rehearsed to the position before a DELETE', '15', 'Done'],
    ['Final report', 'This document', '-', 'Done'],
    ['Live demonstration and viva', 'Run sheet and rerunnable segment files (demo/), viva map (docs/viva_map.md)', '19', 'Ready'],
], [2500, 4560, 1300, 1000])

# ================================================================= 19 demo plan
h1('19. Live Demonstration Plan', new_page=False)
p('The demonstration follows the order in the faculty template. Every segment is a separate file in demo/ that can '
  'be run again on its own if the examiner asks to see something twice.')
table(['Time', 'Step', 'What is shown', 'File'], [
    ['0:30', '1. Clean build', 'Runner drops and rebuilds everything; row counts; 49/49 tests', 'runner/RUN_ME.bat, demo/01_build_check.sql'],
    ['1:30', '2. Role-based access', 'Role matrix, REVOKE before/after, ERROR 1142 and 1369, the escalation fix, the audit trail, SQL injection', 'demo/02a to 02g'],
    ['5:30', '3. Transaction with failure', 'Half a batch kept by COMMIT; the handler rolls back the whole batch; savepoint', 'demo/03_transaction.sql'],
    ['6:30', '4. Triggers firing', 'Severity-9 attack opens an incident; a reported IP is retro-hunted; IOC rules refuse changes', 'demo/04_triggers.sql'],
    ['7:30', '5. Optimisation', 'EXPLAIN without and with idx_src_time; EXPLAIN ANALYZE; an index hidden by a function', 'demo/05_optimisation.sql'],
    ['8:30', '6. Concurrency', 'Lost update in two terminals, then the FOR UPDATE fix', 'demo/06_concurrency.md'],
], [700, 2000, 4360, 2300])

# ================================================================= 20-23
h1('20. Limitations and Future Scope', new_page=False)
lim = md.split('## 1.3 Limitations (replaces Review 2 section 17)')[1].split('# 2.')[0]
bullets([re.sub(r'`([^`]*)`', r'\1', l[2:].strip()) for l in lim.split('\n') if l.startswith('- ')] + [
    'Future: run the procedures under a dedicated low-privilege definer account instead of root, so that a mistake '
    'in one procedure cannot reach the whole database.',
    'Future: very high log volumes would need archive tables or partitioning for old logs, and a streaming loader.'])

h1('21. Conclusion', new_page=False)
p('Review 1 gave us a clean 3NF design and Review 2 showed it working. Review 3 made it defensible. Testing our own '
  'work found four real defects: a script that only ran because our runner hid its mistake, a stored procedure that '
  'let an analyst bypass the row-level security we were proud of, a rollback demonstration that relied on a manual '
  'ROLLBACK, and a trigger that made closed indicators permanent. Each is fixed and has a test. The database now '
  'enforces its own rules, limits every user to what they need, records who changed what, survives concurrent use '
  'and accidental deletes, and proves all of this with 49 tests that pass on a clean build. The biggest lesson was '
  'that a security feature is only as strong as the code that runs with more rights than its caller.')

h1('22. Work Break Down', new_page=False)
wb = [r[:] for r in ROWS(527)[1:]]
wb[0][2] = wb[0][2].replace(', FastAPI backend', '')
wb[2][1] = 'Yashneil Purkayastha'
wb[2][2] = wb[2][2].replace(', React dashboard', '')
for r, seg in zip(wb, ('Live demo: steps 1 and 4, introduction and close', 'Live demo: step 2 (role-based access) and concurrency terminal A',
                       'Live demo: SQL injection, steps 3 and 5, concurrency terminal B')):
    r.append(seg)
table(['Registration Number', 'Name', 'Work Assigned (Reviews 1 and 2)', 'Review 3 demonstration'], wb,
      [1700, 1700, 3460, 2500])

h1('23. Review Evaluation', new_page=False)
table(['COMPONENT', 'MARKS', 'SHLOK GUPTA', 'SHREYA BHUSHAN', 'YASHNEIL PURKAYASTHA'],
      [['Project work with screenshot', '5', '', '', ''], ['Viva', '5', '', '', ''], ['TOTAL', '10 MARKS', '', '', '']],
      [2560, 1300, 1800, 1850, 1850])

# ---------------------------------------------------------------- resolve figure references, write
def resolve(x):
    if isinstance(x, str):
        return re.sub(r'\{\{fig:([^}]+)\}\}', lambda m: str(figs[m.group(1)]), x)
    if isinstance(x, list):
        return [resolve(y) for y in x]
    if isinstance(x, dict):
        return {k: resolve(v) for k, v in x.items()}
    return x


spec = {'title': 'SentinelX Review 3 Report', 'author': 'Shlok Gupta, Shreya Bhushan, Yashneil Purkayastha',
        'blocks': resolve(blocks)}
json.dump(spec, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(blocks), 'blocks,', len(figs), 'figures,', len(rows), 'test rows')
