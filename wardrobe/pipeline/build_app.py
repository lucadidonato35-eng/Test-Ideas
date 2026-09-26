"""Build app/index.html: one self-contained file with pieces, rules, looks and every
image inlined as a data URI.  python build_app.py"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from hybrid import data_uri

def build():
    pieces = json.load(open(os.path.join(ROOT, 'pieces.json')))
    rules = json.load(open(os.path.join(ROOT, 'rules.json')))
    looks = json.load(open(os.path.join(ROOT, 'looks.json')))
    keys = {p['key'] for p in pieces}
    for L in looks['looks']:
        bad = [k for k in L['pcs'] if k and k not in keys]
        if bad: raise SystemExit(f"look {L['name']!r} uses unknown pieces {bad}")
    for g in looks['gb']:
        bad = [k for k in g['good']+g['better'] if k not in keys]
        if bad: raise SystemExit(f'good-vs-better pair uses unknown pieces {bad}')
    images = {}
    for p in pieces:
        path = os.path.join(ROOT, 'images', f"{p['key']}.webp")
        if not os.path.exists(path): raise SystemExit(f"missing image for {p['key']}: run add_piece.py --rerender {p['key']}")
        images[p['key']] = data_uri(path)
    slim = [{k: v for k, v in p.items() if k not in ('source', 'source_kind', 'photo', 'template', 'base', 'surface')} for p in pieces]
    data = json.dumps({'pieces': slim, 'rules': rules, 'looks': looks, 'images': images},
                      ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = open(os.path.join(ROOT, 'app', 'app_template.html')).read()
    rules_js = open(os.path.join(ROOT, 'app', 'rules.js')).read()
    html = html.replace('/*__RULES_JS__*/', rules_js).replace('/*__DATA__*/null', data)
    out = os.path.join(ROOT, 'app', 'index.html')
    open(out, 'w').write(html)
    return out

if __name__ == '__main__':
    out = build()
    print(out, f'{os.path.getsize(out)//1024} KB')
