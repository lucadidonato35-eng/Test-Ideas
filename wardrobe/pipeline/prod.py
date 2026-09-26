"""Step 2: colour-correct and de-shadow a cutout.

Neutralises the warm indoor cast, flattens the phone shadow with a large-radius
local brightness normalisation, and tightens the alpha edge to kill halos.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from scipy import ndimage

CAST = np.array([0.962, 1.037, 1.18])     # multiply R, G, B

def correct(img, strength=0.85, flatten_max=1.9):
    """strength scales the cast correction (1 = full multiply). Patterned or quilted
    pieces use a weaker correction and flattening so the pattern's own contrast survives."""
    a = np.array(img.convert('RGBA')).astype(float)
    rgb, al = a[..., :3], a[..., 3]/255.
    rgb = rgb*(1+(CAST-1)*strength)
    m = (al > 0.5).astype(float)
    L = rgb.mean(-1)
    sig = max(a.shape[:2])/9
    bl = ndimage.gaussian_filter(L*m, sig)/np.maximum(ndimage.gaussian_filter(m, sig), 1e-3)
    tgt = np.percentile(bl[m > 0], 65)
    fac = np.clip(tgt/np.maximum(bl, 1), 0.8, flatten_max)**0.8
    rgb = np.clip(rgb*fac[..., None], 0, 255)
    am = ndimage.binary_erosion(al > 0.45, iterations=2)
    na = ndimage.gaussian_filter(am.astype(float), 0.9)*255
    out = Image.fromarray(np.dstack([rgb, na]).astype(np.uint8), 'RGBA')
    rgbim = ImageEnhance.Contrast(out.convert('RGB')).enhance(1.08)
    rgbim = rgbim.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    rgbim.putalpha(out.getchannel('A'))
    return rgbim

def strength_for(template):
    """The kit used half strength for the patterned coats and the puffer."""
    busy = template.startswith(('coat:herringbone', 'coat:check', 'puffer')) or 'pattern' in template
    return (0.45, 1.15) if busy else (0.85, 1.9)
