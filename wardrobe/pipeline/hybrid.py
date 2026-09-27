"""Steps 3-6: fill the SVG silhouette with real fabric from the cutout, add studio
shading, export 560 px webp and the contact sheet.

Garments: quilt 30-40 clean high-passed fabric windows from the cutout into the
template, multiplied by the SVG's own shading. Shoes: the corrected cutout as is.
"""
import io, base64
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage
import draw

CANVAS = 800          # render size before export
OUT = 560             # exported webp size
CREAM = (237, 232, 225)

def hx(c): c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)

# ---------------- fabric sampling ----------------
def texture_windows(src, size=110, n=36, log=print):
    """Pick n clean fabric windows: mean brightness closest to the garment median,
    low gradient (no folds or seams), spread over the garment, then high-pass each so
    shading goes but weave and pattern stay."""
    a = np.array(src.convert('RGBA')).astype(float)
    rgb, al = a[..., :3], a[..., 3] > 200
    h, w = al.shape
    s = int(min(size, h//3, w//3))
    L = rgb.mean(-1)
    med = np.median(L[al])
    mad = np.median(np.abs(L[al]-med))+1
    # gradient at crease scale (folds, seams, shadows), not at weave scale
    gy, gx = np.gradient(ndimage.gaussian_filter(L, max(2, s/10)))
    grad = np.hypot(gx, gy)
    # outliers in brightness (buttons, labels) or in colour (ottoman strips the mask kept)
    medc = np.median(rgb[al], 0)
    cd = np.abs(rgb-medc).sum(-1)
    cmad = np.median(cd[al])+1
    outlier = ((np.abs(L-med) > 4*mad) | (cd > 5*cmad)).astype(float)
    # crease-scale contrast: a fold or shadow edge shows as a big swing of the blurred image
    Lb = ndimage.gaussian_filter(L, max(2, s/14))
    swing = ndimage.maximum_filter(Lb, size=s//3)-ndimage.minimum_filter(Lb, size=s//3)
    er = ndimage.binary_erosion(al, iterations=s//2+2)
    if er.sum() < 50: er = ndimage.binary_erosion(al, iterations=max(2, s//6))
    ys, xs = np.where(er)
    step = max(1, len(ys)//6000)
    cands = []
    for y, x in zip(ys[::step], xs[::step]):
        y0, x0 = y-s//2, x-s//2
        if y0 < 0 or x0 < 0 or y0+s > h or x0+s > w: continue
        win = L[y0:y0+s, x0:x0+s]
        score = (abs(win.mean()-med)
                 + 0.8*abs(win[:s//2].mean()-win[s//2:].mean())
                 + 0.8*abs(win[:, :s//2].mean()-win[:, s//2:].mean())
                 + 4*grad[y0:y0+s, x0:x0+s].mean()
                 + 60*outlier[y0:y0+s, x0:x0+s].mean()
                 + 0.5*swing[y0:y0+s:4, x0:x0+s:4].max())
        cands.append((score, y0, x0))
    cands.sort()
    # greedy spread: skip windows overlapping an already chosen one by more than half
    chosen = []
    for sc, y0, x0 in cands:
        if all(abs(y0-cy) > s*0.5 or abs(x0-cx) > s*0.5 for _, cy, cx in chosen):
            chosen.append((sc, y0, x0))
        if len(chosen) == n: break
    for c in cands:                     # small garments: top up with overlapping windows
        if len(chosen) >= 30: break
        if c not in chosen: chosen.append(c)
    log(f'  fabric: {len(chosen)} windows of {s}px')
    sig = max(4, s*0.065)     # strips creases and shadow edges, keeps rib and weave
    out = []
    for _, y0, x0 in chosen:
        p = rgb[y0:y0+s, x0:x0+s]
        lo = ndimage.gaussian_filter(p, (sig, sig, 0))
        out.append(p-lo+medc)      # every window on the garment's median colour: no patchwork
    return out

def quilt(wins, H, W, scale, seed=7):
    """Feathered random placement of the windows over an H x W canvas."""
    rng = np.random.default_rng(seed)
    s = max(16, int(wins[0].shape[0]*scale))
    rs = [np.array(Image.fromarray(np.clip(p, 0, 255).astype(np.uint8)).resize((s, s), Image.LANCZOS)).astype(float) for p in wins]
    acc = np.zeros((H, W, 3)); wgt = np.zeros((H, W))
    yy, xx = np.mgrid[0:s, 0:s]
    f = np.minimum.reduce([yy, xx, s-1-yy, s-1-xx]).astype(float)
    feather = np.clip(f/(s*0.22), 0, 1)**1.5
    step = int(s*0.5)
    jit = max(2, s//6)
    for y in range(-s//2, H, step):
        for x in range(-s//2, W, step):
            p = rs[rng.integers(len(rs))]
            if rng.random() < 0.5: p = p[:, ::-1]
            dy, dx = y+rng.integers(-jit, jit+1), x+rng.integers(-jit, jit+1)
            y0, x0 = max(dy, 0), max(dx, 0); y1, x1 = min(dy+s, H), min(dx+s, W)
            if y1 <= y0 or x1 <= x0: continue
            py, px = y0-dy, x0-dx
            fw = feather[py:py+(y1-y0), px:px+(x1-x0)]
            acc[y0:y1, x0:x1] += p[py:py+(y1-y0), px:px+(x1-x0)]*fw[..., None]
            wgt[y0:y1, x0:x1] += fw
    return acc/np.maximum(wgt, 1e-3)[..., None]

def garment_width(mask):
    cols = np.where(mask.any(0))[0]
    return cols.max()-cols.min()+1 if len(cols) else mask.shape[1]

# ---------------- studio finish ----------------
def finish(rgb, alpha, fold=0.05):
    """Edge darkening, top-left key light, faint fold variation, unsharp, drop shadow."""
    H, W = alpha.shape
    m = alpha > 0.5
    dt = ndimage.distance_transform_edt(m)
    edge = 0.74+0.26*np.clip(dt/(0.033*W), 0, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    light = 1.06-0.14*((xx/W)*0.6+(yy/H)*0.4)
    out = rgb*(edge*light)[..., None]
    if fold:
        n = ndimage.gaussian_filter(np.random.default_rng(3).standard_normal((H, W)), W/20)
        out = out*(1+fold*n/np.abs(n).max())[..., None]
    out = np.clip(out, 0, 255)
    im = Image.fromarray(np.dstack([out, alpha*255]).astype(np.uint8), 'RGBA')
    rgbim = im.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1.5, percent=40, threshold=2))
    rgbim.putalpha(im.getchannel('A'))
    return with_shadow(rgbim)

def with_shadow(im):
    W, H = im.size
    a = np.array(im.getchannel('A')).astype(float)/255
    sh = Image.new('RGBA', (W, H), (40, 30, 20, 0))
    sh.putalpha(Image.fromarray((a*120).astype(np.uint8)))
    sh = sh.filter(ImageFilter.GaussianBlur(W/57))
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(sh, (int(W*0.012), int(H*0.02)))
    canvas.alpha_composite(im)
    return canvas

# ---------------- the two render paths ----------------
def make_garment(src, spec, base, surface=True, win=110, anchor=None, log=print):
    """src: corrected cutout (RGBA). spec: draw.py template. base: template hex.
    anchor: hex the fabric colour is pulled towards (75%); phone exposure under warm
    light turns black to grey and cream to beige, the hex you give is the truth."""
    flat = np.array(draw.to_png(draw.render(spec, base, surface), CANVAS)).astype(float)
    frgb, fal = flat[..., :3], flat[..., 3]/255.
    H, W = fal.shape
    basec = hx(base)
    wins = texture_windows(src, size=win, log=log)
    # keep the weave at its real size: scale windows by template width / cutout width
    sm = np.array(src.getchannel('A')) > 200
    scale = float(np.clip(garment_width(fal > 0.5)/garment_width(sm), 0.5, 2.0))
    tex = quilt(wins, H, W, scale)
    if anchor:
        med = np.median(np.array(src)[..., :3][sm].astype(float), 0)
        gain = np.clip(hx(anchor)/np.maximum(med, 4), 0.35, 3.0)**0.75
        # move the mean colour, keep the weave contrast as it is (scaling would amplify wrinkles)
        tm = tex.reshape(-1, 3).mean(0)
        tex = tm*gain+(tex-tm)
        log(f'  colour: fabric median #{"".join("%02x" % int(v) for v in med)} pulled towards {anchor}')
    # SVG shading and detail relative to its base colour (ribbing, seams, collar, pockets)
    ratio = np.clip(frgb/np.maximum(basec, 8), 0, 3)
    out = tex*ratio
    # hardware far from the base colour (zips, buttons, soles, stitching): SVG pixel as is
    dist = np.abs(frgb-basec).sum(-1)
    hard = np.clip((dist-90)/60, 0, 1)
    second = draw.parse(spec)[1].get('sleeves')
    if isinstance(second, str) and second.startswith('#'):   # two-tone: sleeves are fabric too
        hard = hard*np.clip((np.abs(frgb-hx(second)).sum(-1)-60)/60, 0, 1)
    hard = hard[..., None]
    out = out*(1-hard)+frgb*hard
    return finish(out, fal)

def make_shoes(src):
    """Shoes: corrected photo cutout, centred on a square canvas with margin and shadow."""
    im = src.convert('RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    if bb: im = im.crop(bb)
    side = int(max(im.size)*1.12)
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.alpha_composite(im, ((side-im.width)//2, (side-im.height)//2))
    sq = sq.resize((CANVAS, CANVAS), Image.LANCZOS)
    return with_shadow(sq)

def render_piece(piece, src, log=print):
    if piece['cat'] == 'shoes':
        return make_shoes(src)
    # kit sources are 560 px renders, a third of a phone cutout's resolution: smaller windows
    win = 72 if piece.get('source_kind') == 'kit' else 110
    anchor = piece['base'] if piece.get('source_kind') == 'photo' else None
    return make_garment(src, piece['template'], piece['base'], piece.get('surface', True), win, anchor, log)

# ---------------- outputs ----------------
def export_webp(im, path):
    im = im.copy(); im.thumbnail((OUT, OUT), Image.LANCZOS)
    im.save(path, 'WEBP', quality=84, method=6)

def data_uri(path):
    return 'data:image/webp;base64,'+base64.b64encode(open(path, 'rb').read()).decode()

def _font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/System/Library/Fonts/Helvetica.ttc',
              'C:/Windows/Fonts/arial.ttf'):
        try: return ImageFont.truetype(f, size)
        except OSError: pass
    return ImageFont.load_default()

def contact_sheet(pieces, img_dir, out_path, highlight=None, cols=6):
    """All pieces on cream, grouped by category, key and name under each."""
    cell, lab = 250, 40
    order = [p for c in ('outer', 'top', 'bottom', 'shoes') for p in pieces if p['cat'] == c]
    rows = (len(order)+cols-1)//cols
    sheet = Image.new('RGB', (cols*cell, rows*(cell+lab)), CREAM)
    d = ImageDraw.Draw(sheet); f1, f2 = _font(15), _font(12)
    for i, p in enumerate(order):
        x, y = (i % cols)*cell, (i//cols)*(cell+lab)
        if p['key'] == highlight:
            d.rectangle([x+2, y+2, x+cell-3, y+cell+lab-3], outline=(31, 42, 68), width=3)
        try:
            t = Image.open(f"{img_dir}/{p['key']}.webp").convert('RGBA')
            t.thumbnail((cell-16, cell-16)); sheet.paste(t, (x+(cell-t.width)//2, y+8), t)
        except FileNotFoundError:
            d.text((x+20, y+100), 'missing image', fill=(150, 56, 56), font=f1)
        d.text((x+10, y+cell-4), p['name'][:30], fill=(29, 27, 25), font=f1)
        d.text((x+10, y+cell+14), f"{p['key']} · {p['cat']}", fill=(121, 114, 106), font=f2)
    sheet.save(out_path, quality=88)
    return out_path
