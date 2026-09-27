"""Studio photo render: the real garment photo, cleaned up like a product flat-lay.

photo -> cutout -> cast-shadow removal -> colour correction -> straighten ->
colour anchor to the piece hex -> centred on a square canvas with a contact shadow.

    python studio.py KEY [KEY ...] | all      writes images/photo/<key>.webp

Works best on flat-lay photos. Swatch pieces (group shots) have no photo of the whole
garment and are skipped; the app falls back to the illustrated render for those.
"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cutout, prod, hybrid

ROOT = os.path.normpath(os.path.join(HERE, '..'))
OUT = os.path.join(ROOT, 'images', 'photo')
SIZE = 900

def remove_shadow(img, log=print):
    """Even out the light: a per-channel illumination map (fabric blurred past its weave)
    is divided back to the lit level wherever it falls below it. Handles the soft edge of
    the photographer's shadow gradually, and the blue tint shadows get under warm light.
    The lift is capped on dark fabric, where a big gain would only amplify noise."""
    a = np.array(img.convert('RGBA')).astype(float)
    rgb, m = a[..., :3], a[..., 3] > 128
    if m.sum() < 1000: return img
    mf = m.astype(float)
    sig = max(m.shape)/90
    w = np.maximum(ndimage.gaussian_filter(mf, sig), 1e-3)
    illum = np.dstack([ndimage.gaussian_filter(rgb[..., c]*mf, sig)/w for c in range(3)])
    Lil = illum.mean(-1)
    lit = np.percentile(Lil[m], 75)
    target = np.array([np.median(illum[..., c][m & (Lil >= lit*0.92)]) for c in range(3)])
    cap = 1.6 if lit < 60 else 2.2          # dark fabric: modest lift only
    gain = np.clip(target/np.maximum(illum, 1), 1.0, cap)
    gain = 1+(gain-1)*np.clip((lit*0.95-Lil)/(lit*0.25), 0, 1)[..., None]   # only where darker than lit
    gain = np.dstack([ndimage.gaussian_filter(gain[..., c], sig/2) for c in range(3)])
    lifted = (gain.mean(-1) > 1.05) & m
    out = np.clip(rgb*gain, 0, 255)
    log(f'  light: evened {lifted.sum()/m.sum():.0%} of the garment (max x{gain.max():.2f})')
    return Image.fromarray(np.dstack([out, a[..., 3]]).astype(np.uint8), 'RGBA')

def straighten(img, max_deg=12):
    """Rotate so the garment's bounding box is tightest (a flat-lay photographed at a tilt)."""
    al = img.getchannel('A')
    small = al.copy(); small.thumbnail((300, 300))
    best = (None, 0)
    for deg in np.arange(-max_deg, max_deg+0.1, 1.0):
        bb = small.rotate(deg, expand=True).point(lambda v: 255 if v > 128 else 0).getbbox()
        if not bb: continue
        area = (bb[2]-bb[0])*(bb[3]-bb[1])
        if best[0] is None or area < best[0]: best = (area, deg)
    return img.rotate(best[1], resample=Image.BICUBIC, expand=True) if best[1] else img

def anchor(img, hexc, strength=0.75):
    """Shift the mean colour towards the piece hex, keep texture contrast."""
    a = np.array(img).astype(float)
    m = a[..., 3] > 200
    med = np.median(a[..., :3][m], 0)
    gain = np.clip(hybrid.hx(hexc)/np.maximum(med, 4), 0.35, 3.0)**strength
    rgb = a[..., :3]
    mean = rgb[m].mean(0)
    a[..., :3] = np.clip(mean*gain+(rgb-mean), 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

def compose(img, size=SIZE, margin=0.07):
    bb = img.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    img = img.crop(bb)
    s = size*(1-2*margin)/max(img.size)
    img = img.resize((max(1, int(img.width*s)), max(1, int(img.height*s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((size-img.width)//2, (size-img.height)//2))
    return hybrid.with_shadow(canvas)

def render(piece, log=print):
    photo = os.path.join(ROOT, piece['photo'])
    cut = cutout.cutout(photo, pair=(piece['cat'] == 'shoes'), log=log)
    if piece['cat'] != 'shoes':
        cut = remove_shadow(cut, log)
    cut = prod.correct(cut, *prod.strength_for(piece['template']))
    cut = straighten(cut)
    if piece['cat'] != 'shoes':
        cut = anchor(cut, piece['base'])
    return compose(cut)

def eligible(p):
    return p.get('photo') and not p.get('swatch') and os.path.exists(os.path.join(ROOT, p['photo']))

def main(keys):
    ps = json.load(open(os.path.join(ROOT, 'pieces.json')))
    todo = [p for p in ps if eligible(p) and (keys == ['all'] or p['key'] in keys)]
    os.makedirs(OUT, exist_ok=True)
    for p in todo:
        print(f"[{p['key']}] studio photo", flush=True)
        hybrid.export_webp(render(p), os.path.join(OUT, f"{p['key']}.webp"))

if __name__ == '__main__':
    main(sys.argv[1:] or ['all'])
