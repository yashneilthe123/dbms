"""Turn mysql -vvv batch output into black-and-white 'mysql>' session screenshots."""
import re, os, json
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = '/usr/share/fonts/truetype/dejavu'
if not os.path.exists(FONT_DIR):  # Windows/macOS: matplotlib ships the same DejaVu fonts
    import matplotlib
    FONT_DIR = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
MONO = ImageFont.truetype(os.path.join(FONT_DIR, 'DejaVuSansMono.ttf'), 24)
MONOB = ImageFont.truetype(os.path.join(FONT_DIR, 'DejaVuSansMono-Bold.ttf'), 24)
CW = MONO.getlength('M')
CWB = MONOB.getlength('M')
LH = 31
SEP = '--------------'


def parse(stdout, stderr):
    """Return list of blocks: {'sql': [lines], 'result': [lines]}"""
    lines = stdout.replace('\r', '').split('\n')
    errors = [re.sub(r' at line \d+', '', l) for l in stderr.replace('\r', '').split('\n')
              if l.startswith('ERROR')]
    blocks, i = [], 0
    while i < len(lines):
        if lines[i] == SEP:
            j = i + 1
            while j < len(lines) and lines[j] != SEP:
                j += 1
            sql = lines[i + 1:j]
            k = j + 1
            res = []
            while k < len(lines) and lines[k] != SEP and lines[k] != 'Bye':
                res.append(lines[k])
                k += 1
            while res and not res[-1].strip():
                res.pop()
            while res and not res[0].strip():
                res.pop(0)
            blocks.append({'sql': sql, 'result': res})
            i = k
        else:
            i += 1
    # a statement with no result text failed: attach errors in order
    for b in blocks:
        if not b['result'] and errors:
            b['result'] = [errors.pop(0)]
            b['error'] = True
    for e in errors:  # anything left over (e.g. connection errors)
        blocks.append({'sql': [], 'result': [e], 'error': True})
    return blocks


def is_noise(b):
    s = ' '.join(b['sql']).strip().upper()
    return s.startswith('SET SESSION CTE_MAX') is False and False


def session_lines(blocks):
    out = []
    for b in blocks:
        sql = [l.rstrip() for l in b['sql']]
        while sql and not sql[-1].strip():
            sql.pop()
        if sql:
            # add terminator the way you would type it
            last = sql[-1]
            if not last.rstrip().endswith((';', '\\G')):
                g = b['result'] and b['result'][0].startswith('*****')
                sql[-1] = last + ('\\G' if g else ';')
            for n, l in enumerate(sql):
                out.append(('prompt' if n == 0 else 'cont', l))
        for r in b['result']:
            r = r.rstrip()
            if b.get('error') and len(r) > 105:
                import textwrap
                for k, part in enumerate(textwrap.wrap(r, 105)):
                    out.append(('err', part if k == 0 else '  ' + part))
            else:
                out.append(('err' if b.get('error') else 'res', r))
        out.append(('res', ''))
    while out and out[-1][1] == '':
        out.pop()
    return out


def render(lines, path, max_chars=None):
    pre = {'prompt': 'mysql> ', 'cont': '    -> ', 'res': '', 'err': ''}
    texts = [(k, pre[k] + t) for k, t in lines]
    width_chars = max(len(t) for _, t in texts) if texts else 40
    W = int(max(60, width_chars) * CWB) + 48
    H = len(texts) * LH + 40
    im = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=0, width=2)
    y = 20
    for k, t in texts:
        if k in ('prompt', 'cont'):
            p = pre[k]
            d.text((24, y), p, font=MONOB, fill=0)
            d.text((24 + MONOB.getlength(p), y), t[len(p):], font=MONO, fill=0)
        else:
            d.text((24, y), t, font=MONOB if k == 'err' else MONO, fill=0)
        y += LH
    im.save(path)
    return im.size


def render_step(out_dir, name, img_dir, select=None, split_at=None):
    so = open(os.path.join(out_dir, name + '.txt'), encoding='utf-8', errors='replace').read()
    ep = os.path.join(out_dir, name + '.err.txt')
    se = open(ep, encoding='utf-8', errors='replace').read() if os.path.exists(ep) else ''
    blocks = parse(so, se)
    if select is not None:
        blocks = [blocks[i] for i in select]
    path = os.path.join(img_dir, name + '.png')
    size = render(session_lines(blocks), path)
    return path, size, blocks
