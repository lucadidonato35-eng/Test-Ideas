"""Python and JS rules engines must agree on every outfit, and saved looks must hold.
Run: python tests/test_rules.py   (needs node)"""
import itertools, json, os, subprocess, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import rules

def main():
    P, R, looks = rules.load()
    cat = lambda c: [k for k, p in P.items() if p['cat'] == c]
    combos = [list(c) for c in itertools.product([None]+cat('outer'), cat('top'), cat('bottom'), cat('shoes'))]
    cases = [(c, o, cold) for c in combos for o in [None]+R['occasions'] for cold in (True, False)]
    py = [[rules.check(c, P, R, o, cold), rules.verdict(rules.check(c, P, R, o, cold), R)[1]] for c, o, cold in cases]
    js_src = f"""
      const E = require({json.dumps(os.path.join(ROOT, 'app', 'rules.js'))});
      const {{P, R, cases}} = JSON.parse(require('fs').readFileSync(0, 'utf8'));
      console.log(JSON.stringify(cases.map(([c,o,cold]) => {{ const r = E.check(c, P, R, o, cold); return [r, E.verdict(r, R).txt]; }})));"""
    js = json.loads(subprocess.run(['node', '-e', js_src], input=json.dumps({'P': P, 'R': R, 'cases': cases}),
                                   capture_output=True, text=True, check=True).stdout)
    bad = [(cases[i], py[i], js[i]) for i in range(len(cases)) if py[i] != js[i]]
    assert not bad, f'{len(bad)} mismatches, first: {bad[0]}'
    print(f'rules parity: {len(cases)} cases identical')
    for L in looks['looks']:
        v = rules.verdict(rules.check(L['pcs'], P, R, L['occ']), R)[1]
        assert v != R['verdict']['rethink'], f"saved look {L['name']!r} scores {v}"
    print(f"saved looks: {len(looks['looks'])} pass")

if __name__ == '__main__':
    main()
