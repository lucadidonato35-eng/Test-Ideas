"""Outfit rules engine (Python twin of app/rules.js; tests/test_rules.py keeps them in step).

    python rules.py                 check every saved look against the rules
    python rules.py suggest KEY     propose looks that use piece KEY and pass every rule
"""
import json, os, sys, itertools

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SLOTS = ('outer', 'top', 'bottom', 'shoes')

def load():
    pieces = {p['key']: p for p in json.load(open(os.path.join(ROOT, 'pieces.json')))}
    rules = json.load(open(os.path.join(ROOT, 'rules.json')))
    looks = json.load(open(os.path.join(ROOT, 'looks.json')))
    return pieces, rules, looks

def match(p, sel):
    return all(p.get(f) in vals for f, vals in sel.items() if not f.startswith('_'))

def check(pcs, P, R, occasion=None, cold=True):
    o, t, b, s = [P[k] if k else None for k in pcs]
    out = []
    if b and s:
        rule = next((r for r in R['shoes']['pairs'] if match(s, r['shoes'])), None)
        if rule is None:
            out.append(dict(id='shoes', lvl='warn', short='Shoes ?', msg=f"No shoe rule covers {s['name']}"))
        elif any(match(b, w) for w in rule['with']):
            out.append(dict(id='shoes', lvl='ok', short='Shoes ✓', msg=f"{s['name']} suit {b['name'].lower()}"))
        elif s.get('style') == 'sneaker' and b.get('kind') == 'trouser':
            out.append(dict(id='shoes', lvl='no', short='Shoes ✗', msg='Sneakers undercut tailored trousers'))
        else:
            out.append(dict(id='shoes', lvl='no', short='Shoes ✗', msg=rule['say']))
    cols = {x['colour'] for x in (o, t, b, s) if x}
    hit = next((pr for pr in R['clash']['pairs'] if pr[0] in cols and pr[1] in cols), None)
    out.append(dict(id='clash', lvl='warn', short=f'{hit[0].title()} + {hit[1]}', msg=R['clash']['say']) if hit
               else dict(id='clash', lvl='ok', short='Palette ✓', msg='Colours sit in one family'))
    busy = o and t and o.get('tex') in R['texture']['outer'] and t.get('tex') in R['texture']['top']
    out.append(dict(id='texture', lvl='warn', short='Two textures', msg=R['texture']['say']) if busy
               else dict(id='texture', lvl='ok', short='Texture ✓', msg='One texture hero'))
    if cold:
        W = R['warmth']
        if t and not o and t.get('w', 0) <= W['light']:
            out.append(dict(id='warmth', lvl='warn', short='Too light', msg=W['say_light']))
        elif (o.get('w', 0) if o else 0)+(t.get('w', 0) if t else 0) < W['min']:
            out.append(dict(id='warmth', lvl='warn', short='Too light', msg=W['say_low']))
        else:
            out.append(dict(id='warmth', lvl='ok', short='Warm ✓', msg=f"Warm enough for {W['place']}"))
    if occasion:
        off = [x for x in (o, t, b, s) if x and occasion not in x.get('occasions', [])]
        if off:
            msg = R['occasion']['say'].format(names=', '.join(x['name'] for x in off),
                                             verb='are' if len(off) > 1 else 'is', occasion=occasion.lower())
            out.append(dict(id='occasion', lvl='warn', short='Off-occasion', msg=msg))
        else:
            out.append(dict(id='occasion', lvl='ok', short=f'{occasion} ✓', msg=f'Right for {occasion.lower()}'))
    D = R['dress_down']
    if o and t and b and s and match(o, D['outer']) and match(b, D['bottom']) \
            and s.get('style') != 'sneaker' and not t.get('casual'):
        out.append(dict(id='dress_down', lvl='warn', short='Puffer + tailoring', msg=D['say']))
    return out

def verdict(res, R):
    V = R['verdict']
    if any(r['lvl'] == 'no' for r in res): return 'no', V['rethink']
    w = sum(r['lvl'] == 'warn' for r in res)
    return ('ok', V['strong']) if w == 0 else ('warn', V['tweak']) if w == 1 else ('no', V['rethink'])

def options(P, cat, occasion):
    return [k for k, p in P.items() if p['cat'] == cat and occasion in p.get('occasions', [])]

def suggest(key, n=3, P=None, R=None, looks=None):
    """Looks that use `key`, pass every rule for one of its occasions, and differ from the
    saved looks and from each other. Prefers a coat (autumn) and spreads occasions."""
    if P is None: P, R, looks = load()
    piece = P[key]
    saved = {tuple(L['pcs']) for L in looks['looks']}
    cands = []
    for occ in piece.get('occasions', []):
        pools = [[None]+options(P, 'outer', occ)] + [options(P, c, occ) for c in SLOTS[1:]]
        pools[SLOTS.index(piece['cat'])] = [key]
        for pcs in itertools.product(*pools):
            if pcs in saved: continue
            if verdict(check(pcs, P, R, occ), R)[0] != 'ok': continue
            cands.append((occ, pcs))
    picked = []
    while cands and len(picked) < n:
        def score(c):
            occ, pcs = c
            shared = max((sum(a == b for a, b in zip(pcs, q)) for _, q in picked), default=0)
            near_saved = max(sum(a == b for a, b in zip(pcs, q)) for q in saved) if saved else 0
            return (sum(o == occ for o, _ in picked), shared, near_saved, pcs[0] is None)
        best = min(cands, key=score)
        picked.append(best); cands.remove(best)
    return picked

if __name__ == '__main__':
    P, R, looks = load()
    if len(sys.argv) > 2 and sys.argv[1] == 'suggest':
        for occ, pcs in suggest(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3, P, R, looks):
            print(json.dumps({'occ': occ, 'pcs': list(pcs), 'names': [P[k]['name'] if k else None for k in pcs]}))
    else:
        for i, L in enumerate(looks['looks'], 1):
            res = check(L['pcs'], P, R, L['occ'])
            lvl, txt = verdict(res, R)
            flags = ', '.join(r['short'] for r in res if r['lvl'] != 'ok')
            print(f"{i:2}. {L['name']:24} {L['occ']:8} {txt:22} {flags}")
