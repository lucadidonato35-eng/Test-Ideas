"""Step 1: phone photo -> garment cutout (RGBA).

rembg (isnet-general-use, falling back to u2net when the mask looks wrong), then
remove leftover pink-ottoman pixels and keep only the garment's connected component
(both shoes of a pair for footwear).
"""
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

MAX_SIDE = 1600
MODELS = ('isnet-general-use', 'u2net')
_sessions = {}

def _session(name):
    if name not in _sessions:
        from rembg import new_session
        _sessions[name] = new_session(name)
    return _sessions[name]

def load_photo(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return im

def mask_problems(m, pair=False):
    """Why a rembg mask looks wrong, or [] if it looks fine."""
    frac = m.mean()
    probs = []
    if frac < 0.03: probs.append(f'mask covers only {frac:.0%} of the photo')
    if frac > 0.85: probs.append(f'mask covers {frac:.0%} of the photo (background kept)')
    lab, n = ndimage.label(m)
    if n:
        sizes = np.sort(ndimage.sum(m, lab, range(1, n+1)))[::-1]
        main = sizes[:2].sum() if pair else sizes[0]
        if main < 0.6*sizes.sum(): probs.append('mask is fragmented')
    edges = [m[0].mean(), m[-1].mean(), m[:, 0].mean(), m[:, -1].mean()]
    if sum(e > 0.5 for e in edges) >= 3: probs.append('mask touches three or more photo edges')
    return probs

def rembg_mask(im, pair=False, log=print):
    from rembg import remove
    best = None
    for name in MODELS:
        m = np.array(remove(im, session=_session(name), only_mask=True).convert('L')).astype(float)/255
        probs = mask_problems(m > 0.5, pair)
        if not probs:
            log(f'  mask: {name} ok')
            return m, name
        log(f'  mask: {name} rejected ({"; ".join(probs)})')
        if best is None or len(probs) < len(best[2]): best = (m, name, probs)
    log(f'  mask: using {best[1]} anyway, check the result')
    return best[0], best[1]

def remove_pink(rgb, alpha, log=print):
    """Leftover pink velvet: r-b > 20 and r-g > 10.

    Brown and beige cloth also passes that test (warm, red above blue), so two guards:
    velvet pink keeps blue close to green (b >= g-8, brown has b well below g), and if
    the candidates cover over a third of the garment we only clean a thin edge band."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    on = alpha > 0.5
    cand = (r-b > 20) & (r-g > 10) & (b >= g-8) & on
    if cand.sum() > 0.35*on.sum():
        band = ndimage.distance_transform_edt(on) < 12
        cand &= band
        log('  pink: garment itself is warm-toned, cleaning edge band only')
    log(f'  pink: removed {cand.sum()/max(on.sum(),1):.1%} of mask pixels')
    alpha = alpha.copy(); alpha[cand] = 0
    return alpha

def keep_main(alpha, pair=False, log=print):
    """Largest connected component; for a pair of shoes, the two largest if both are big.
    A small opening first snaps thin bridges such as a hanger hook or rail."""
    m = alpha > 0.5
    r = max(2, int(0.004*max(m.shape)))
    opened = ndimage.binary_opening(m, structure=np.ones((3, 3)), iterations=r)
    lab, n = ndimage.label(opened)
    if n == 0: return alpha
    sizes = ndimage.sum(opened, lab, range(1, n+1))
    order = np.argsort(sizes)[::-1]
    keep = [order[0]+1]
    if pair and n > 1 and sizes[order[1]] > 0.25*sizes[order[0]]:
        keep.append(order[1]+1)
    km = np.isin(lab, keep)
    km = ndimage.binary_dilation(km, iterations=r+1) & m        # restore edges lost to the opening
    km = ndimage.binary_fill_holes(km)
    log(f'  components: {n} found, kept {len(keep)}')
    return alpha*km

def cutout(path, pair=False, log=print):
    im = load_photo(path)
    rgb = np.array(im).astype(float)
    alpha, model = rembg_mask(im, pair, log)
    alpha = remove_pink(rgb, alpha, log)
    alpha = keep_main(alpha, pair, log)
    ys, xs = np.where(alpha > 0.5)
    if not len(ys): raise RuntimeError('cutout is empty: the garment was not found in the photo')
    pad = int(0.02*max(alpha.shape))
    y0, y1 = max(ys.min()-pad, 0), min(ys.max()+pad+1, alpha.shape[0])
    x0, x1 = max(xs.min()-pad, 0), min(xs.max()+pad+1, alpha.shape[1])
    out = np.dstack([rgb, alpha*255])[y0:y1, x0:x1]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
