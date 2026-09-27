"""Add a piece to the wardrobe in one command.

    python add_piece.py photo.jpg --key navy_cardigan --name "Navy cardigan" --cat top \\
        --colour navy --template cardigan --hex "#252a3c" --occasions office,evening

Runs cutout -> colour correction -> template + fabric (or photo cutout for shoes) ->
images/<key>.webp -> pieces.json -> images/_sheet.jpg -> app/index.html, then prints
looks that would use the new piece.

Only --name and --occasions are needed; the rest is inferred:
    --key       slug of the name
    --cat       from the template (top|outer|bottom|shoes)
    --template  a sensible default per category (crew, coat, trousers, loafer)
    --hex       median colour of the corrected cutout
    --colour    nearest named colour to the hex

Other modes:
    python add_piece.py --rerender KEY [KEY ...]   rebuild images from sources/ (or: all)
    python add_piece.py --reprocess KEY [KEY ...]  redo cutout + correction from photos/ (or: all)
    python add_piece.py --build                    rebuild contact sheet and app only

Group photo (several garments touching)? Crop a patch of plain fabric from inside the
garment and pass --swatch: the template gives the shape, the photo only gives fabric.
"""
import argparse, json, os, re, shutil, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw, cutout, prod, hybrid, rules

ROOT = os.path.normpath(os.path.join(HERE, '..'))
PJ = os.path.join(ROOT, 'pieces.json')
IMG = os.path.join(ROOT, 'images')

DEFAULT_TEMPLATE = {'top': 'crew', 'outer': 'coat', 'bottom': 'trousers', 'shoes': 'loafer'}
SHORT = {'crew': 'Knit', 'mock': 'Mock neck', 'polo': 'Knit polo', 'zip': 'Zip knit', 'cardigan': 'Cardigan',
         'coat': 'Coat', 'puffer': 'Puffer', 'bomber': 'Bomber', 'shirt': 'Shirt', 'overshirt': 'Overshirt', 'trousers': 'Trousers', 'chinos': 'Chinos', 'denim': 'Jeans',
         'loafer': 'Loafers', 'chelsea': 'Boots', 'sneaker': 'Sneakers', 'runner': 'Sneakers'}
# names the rules understand; hex values are reference points for --colour inference
NAMED = {'black': '#1b1b1c', 'charcoal': '#2e2f33', 'grey': '#80807e', 'white': '#f1efe9', 'cream': '#e6dfd1',
         'beige': '#c8b8a2', 'brown': '#5a3f30', 'navy': '#1f2638', 'blue': '#6b86a6', 'olive': '#5a5e4c',
         'green': '#3f5a45', 'burgundy': '#5c2430', 'camel': '#b08a5a', 'taupe': '#7a6e62', 'rust': '#8a4a2c', 'dark': '#3f3a38'}

def log(*a): print(*a, flush=True)

def load_pieces(): return json.load(open(PJ))
def save_pieces(ps): json.dump(ps, open(PJ, 'w'), indent=1, ensure_ascii=False)

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def median_hex(img):
    a = np.array(img.convert('RGBA')).astype(float)
    m = a[..., 3] > 200
    rgb = np.median(a[..., :3][m], 0) if m.any() else np.array([128, 128, 128])
    return '#%02x%02x%02x' % tuple(int(v) for v in rgb)

def nearest_colour(hexc):
    c = hybrid.hx(hexc)
    return min(NAMED, key=lambda n: ((hybrid.hx(NAMED[n])-c)**2*np.array([0.3, 0.59, 0.11])).sum())

def build_outputs(highlight=None):
    ps = load_pieces()
    sheet = hybrid.contact_sheet(ps, IMG, os.path.join(IMG, '_sheet.jpg'), highlight=highlight)
    log(f'contact sheet: {os.path.relpath(sheet, ROOT)}')
    import build_app
    out = build_app.build()
    log(f'app: {os.path.relpath(out, ROOT)}')

def render(piece, src):
    im = hybrid.render_piece(piece, src, log)
    path = os.path.join(IMG, f"{piece['key']}.webp")
    hybrid.export_webp(im, path)
    log(f'  image: {os.path.relpath(path, ROOT)}')

def add(a):
    ps = load_pieces()
    template = a.template or DEFAULT_TEMPLATE.get(a.cat or 'top')
    tcat, attrs = draw.implied(template)
    cat = a.cat or tcat
    if cat != tcat:
        sys.exit(f'template {template!r} draws a {tcat}, but --cat is {cat!r}')
    key = a.key or slug(a.name)
    existing = next((p for p in ps if p['key'] == key), None)
    if existing and not a.replace:
        sys.exit(f'{key!r} already exists; pass --replace to re-shoot it or pick another --key')
    occ = [o.strip().title() for o in a.occasions.split(',') if o.strip()]
    known = json.load(open(os.path.join(ROOT, 'rules.json')))['occasions']
    bad = [o for o in occ if o not in known]
    if bad: sys.exit(f'unknown occasion {bad}; use {known}')

    if a.swatch:
        if cat == 'shoes': sys.exit('--swatch is for garments; shoes need a real cutout')
        log(f'[{key}] 1/4 swatch (no cutout: the photo is plain fabric from inside the garment)')
        cut = cutout.load_photo(a.photo).convert('RGBA')
    else:
        log(f'[{key}] 1/4 cutout')
        cut = cutout.cutout(a.photo, pair=(cat == 'shoes'), log=log)
    log(f'[{key}] 2/4 colour correction')
    strength, flat = prod.strength_for(template)
    src = prod.correct(cut, strength, flat)
    os.makedirs(os.path.join(ROOT, 'sources'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'photos'), exist_ok=True)
    src.save(os.path.join(ROOT, 'sources', f'{key}.png'), optimize=True)
    ph = cutout.load_photo(a.photo); ph.thumbnail((1600, 1600))
    ph.save(os.path.join(ROOT, 'photos', f'{key}.jpg'), quality=88)

    hexc = a.hex or median_hex(src)
    colour = a.colour or nearest_colour(hexc)
    piece = {'key': key, 'name': a.name, 'short': a.short or SHORT[draw.parse(template)[0]], 'cat': cat,
             'colour': colour.lower(), 'hex': hexc.upper(), 'template': template, 'base': hexc.lower(),
             'occasions': occ}
    piece.update(attrs)
    if cat == 'shoes': piece.pop('w', None)
    if a.weight is not None: piece['w'] = a.weight
    if a.texture: piece['tex'] = a.texture
    if a.texture == 'none': piece.pop('tex', None)
    if a.casual: piece['casual'] = 1
    piece.update({'source': f'sources/{key}.png', 'source_kind': 'photo', 'photo': f'photos/{key}.jpg'})
    if a.swatch: piece['swatch'] = True
    log(f'[{key}] 3/4 render ({"photo cutout" if cat == "shoes" else template})')
    render(piece, src)

    if existing: ps[ps.index(existing)] = piece
    else: ps.append(piece)
    save_pieces(ps)
    log(f'[{key}] 4/4 pieces.json, contact sheet, app')
    log('  piece: ' + json.dumps(piece, ensure_ascii=False))
    build_outputs(highlight=key)
    log('\nlooks that could use it (all rules pass):')
    for occ_, pcs in rules.suggest(key):
        log(f'  {occ_:8} ' + ' + '.join(str(k) for k in pcs))

def reprocess(keys):
    """Whole chain again from the stored photo, keeping every setting in pieces.json."""
    ps = load_pieces()
    todo = [p for p in ps if p.get('photo') and (keys == ['all'] or p['key'] in keys)]
    missing = set(keys)-{p['key'] for p in todo}-{'all'}
    if missing: sys.exit(f'no stored photo for: {sorted(missing)}')
    for p in todo:
        log(f"[{p['key']}] reprocess {p['photo']}")
        path = os.path.join(ROOT, p['photo'])
        cut = cutout.load_photo(path).convert('RGBA') if p.get('swatch') else \
            cutout.cutout(path, pair=(p['cat'] == 'shoes'), log=log)
        src = prod.correct(cut, *prod.strength_for(p['template']))
        src.save(os.path.join(ROOT, p['source']), optimize=True)
        render(p, src)
    build_outputs()

def rerender(keys):
    ps = load_pieces()
    todo = ps if keys == ['all'] else [p for p in ps if p['key'] in keys]
    missing = set(keys)-{p['key'] for p in ps}-{'all'}
    if missing: sys.exit(f'unknown keys: {sorted(missing)}')
    for p in todo:
        log(f"[{p['key']}] render from {p['source']}")
        render(p, Image.open(os.path.join(ROOT, p['source'])).convert('RGBA'))
    build_outputs()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('photo', nargs='?')
    ap.add_argument('--name'); ap.add_argument('--key'); ap.add_argument('--short')
    ap.add_argument('--cat', choices=['outer', 'top', 'bottom', 'shoes'])
    ap.add_argument('--template', help='draw.py spec, e.g. crew, polo:rib, coat:check, denim, chelsea')
    ap.add_argument('--hex'); ap.add_argument('--colour')
    ap.add_argument('--occasions', help='comma list: office,evening,weekend')
    ap.add_argument('--weight', type=int, help='warmth weight (light knit 1, knit 2, chunky/coat 3)')
    ap.add_argument('--texture', choices=['pattern', 'chunky', 'none'])
    ap.add_argument('--casual', action='store_true')
    ap.add_argument('--replace', action='store_true', help='overwrite an existing key (re-shoot)')
    ap.add_argument('--swatch', action='store_true',
                    help='photo is a crop of plain fabric from inside the garment (group shots): skip the cutout')
    ap.add_argument('--rerender', nargs='+', metavar='KEY')
    ap.add_argument('--reprocess', nargs='+', metavar='KEY')
    ap.add_argument('--build', action='store_true')
    a = ap.parse_args()
    if a.rerender: return rerender(a.rerender)
    if a.reprocess: return reprocess(a.reprocess)
    if a.build: return build_outputs()
    if not (a.photo and a.name and a.occasions):
        ap.error('adding a piece needs a photo, --name and --occasions')
    add(a)

if __name__ == '__main__':
    main()
