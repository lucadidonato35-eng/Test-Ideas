"""SVG garment templates.

A template is addressed by a spec string: "name" or "name:opt,opt=value", e.g.
    crew            crew:rib        crew:sweat      mock:rib
    polo:rib        zip:rib         zip:half        cardigan:speck
    coat            coat:herringbone,buttons=3      coat:check
    puffer          trousers        chinos          denim
    loafer:penny    loafer          chelsea
    sneaker:stripe=#f4f2ee,sole=#f4f2ee             runner:accent=#7fa6c9,sole=#5a5c60

render(spec, hex) returns an SVG string on a 400x400 canvas.
surface=False drops woven/knitted surface patterns (rib, speck, herringbone, check,
denim twill) but keeps structure (seams, collar, pockets, hardware); used when the
fabric source already carries its own pattern.
"""
import base64, json

VIEW = 400

def hx(c): c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def sh(c, f):
    r, g, b = hx(c)
    if f >= 0: r, g, b = [int(v+(255-v)*f) for v in (r, g, b)]
    else: r, g, b = [int(v*(1+f)) for v in (r, g, b)]
    return '#%02x%02x%02x' % (r, g, b)

def wrap(inner, defs=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW} {VIEW}"><defs>{defs}</defs>{inner}</svg>'

def grad(id, c):
    return f'<linearGradient id="{id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{sh(c,.10)}"/><stop offset=".55" stop-color="{c}"/><stop offset="1" stop-color="{sh(c,-.14)}"/></linearGradient>'

# ---------------- knitwear / tops ----------------
# Flat lay with arms down: the cuff sits at hem level, where the wrist falls.
LONG_BODY = ('M130 84 L76 104 Q58 190 40 332 L92 342 L114 196 L112 340 Q200 352 288 340 L286 196 '
             'L308 342 L360 332 Q342 190 324 104 L270 84 Q200 118 130 84 Z')

def top(c, neck='crew', zip=None, buttons=False, rib=False, cable=False, sweat=False,
        sleeves='long', speck=False, surface=True):
    dk = sh(c, -.28)
    defs = grad('g', c)
    pat = surface and (rib or cable or speck)
    if rib and surface:
        defs += f'<pattern id="rib" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="14" height="14" fill="url(#g)"/><rect x="5" width="2.5" height="14" fill="{sh(c,-.09)}"/><rect x="0" width="1.2" height="14" fill="{sh(c,.10)}"/></pattern>'
    if cable and surface:
        defs += f'<pattern id="rib" width="18" height="24" patternUnits="userSpaceOnUse"><rect width="18" height="24" fill="url(#g)"/><path d="M4 0c6 6 6 18 0 24M14 0c-6 6-6 18 0 24" fill="none" stroke="{sh(c,-.14)}" stroke-width="2"/></pattern>'
    if speck and surface:
        defs += f'<pattern id="rib" width="20" height="20" patternUnits="userSpaceOnUse"><rect width="20" height="20" fill="url(#g)"/><circle cx="4" cy="6" r="1" fill="{sh(c,.55)}"/><circle cx="14" cy="15" r=".8" fill="{sh(c,.5)}"/><circle cx="9" cy="1" r=".7" fill="{sh(c,.5)}"/></pattern>'
    fill = 'url(#rib)' if pat else 'url(#g)'
    if sleeves == 'long':
        body = LONG_BODY
    else:
        # short sleeves end mid upper arm; body keeps the long-sleeve width down to the hem
        body = ('M130 84 L76 104 L56 200 L108 212 L114 196 L112 340 Q200 352 288 340 L286 196 '
                'L292 212 L344 200 L324 104 L270 84 Q200 118 130 84 Z')
    o = f'<path d="{body}" fill="{fill}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    if sleeves == 'long':
        # armhole seams (raglan for sweatshirts), inner sleeve fold
        if sweat:
            o += f'<path d="M150 92 L114 196 M250 92 L286 196" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".6"/>'
        else:
            o += f'<path d="M114 196 L130 84 M286 196 L270 84" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".6"/>'
        o += f'<path d="M80 150 Q74 240 70 318 M320 150 Q326 240 330 318" fill="none" stroke="{dk}" stroke-width="1" opacity=".25"/>'
        # ribbed cuffs, level with the hem band
        o += f'<path d="M40 332 L92 342 L90 364 L37 354 Z M360 332 L308 342 L310 364 L363 354 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
        o += cuffrib(40, 334, 52, 20, dk) + cuffrib(308, 334, 52, 20, dk)
    else:
        o += f'<path d="M114 196 L130 84 M286 196 L270 84" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".6"/>'
        o += f'<path d="M56 200 L108 212 L105 230 L52 218 Z M344 200 L292 212 L295 230 L348 218 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
        o += cuffrib(56, 202, 50, 16, dk) + cuffrib(294, 202, 50, 16, dk)
    # hem band
    o += f'<path d="M112 340 Q200 352 288 340 L288 364 Q200 376 112 364 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="2"/>'
    o += ''.join(f'<line x1="{x}" y1="{343+(x-200)**2/1900:.0f}" x2="{x}" y2="{365+(x-200)**2/1900:.0f}" stroke="{dk}" stroke-width="1" opacity=".45"/>' for x in range(120, 288, 9))
    if neck == 'crew':
        o += f'<path d="M130 84 Q200 118 270 84 Q270 140 200 146 Q130 140 130 84 Z" fill="{sh(c,-.30)}"/>'
        o += f'<path d="M138 82 Q200 108 262 82 Q260 128 200 134 Q140 128 138 82 Z" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="2"/>'
        o += ''.join(f'<path d="M{x} {84+abs(x-200)*0.06:.0f} L{x} {96+abs(x-200)*0.06:.0f}" stroke="{dk}" stroke-width="1" opacity=".35"/>' for x in range(150, 252, 8))
    elif neck == 'mock':
        o += f'<path d="M132 86 L136 58 Q200 80 264 58 L268 86 Q200 116 132 86 Z" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="2"/>'
        o += f'<path d="M140 62 Q200 82 260 62" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".5"/>'
    elif neck == 'v':
        o += f'<path d="M130 84 L200 196 L270 84 L256 80 L200 172 L144 80 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
        o += f'<path d="M144 80 Q200 100 256 80 L200 172 Z" fill="{sh(c,-.32)}"/>'
    elif neck == 'polo':
        o += polo_collar(c, dk)
    if zip:
        y1 = 92 if neck != 'mock' else 60; y2 = 172 if zip == 'half' else 352
        o += f'<rect x="196" y="{y1}" width="8" height="{y2-y1}" fill="{sh(c,-.35)}"/>'
        o += ''.join(f'<rect x="197" y="{y}" width="6" height="2" fill="#c9c6bd"/>' for y in range(y1+2, y2-2, 5))
        o += f'<rect x="195" y="{y1+8}" width="10" height="16" rx="2" fill="#a8a59e" stroke="#6d6a64"/>'
    if buttons:
        y0 = 70 if neck == 'mock' else 196 if neck == 'v' else 100
        o += f'<line x1="200" y1="{y0}" x2="200" y2="362" stroke="{dk}" stroke-width="1.5"/>'
        o += f'<path d="M206 {y0} L206 362" stroke="{dk}" stroke-width="1" opacity=".4"/>'
        o += ''.join(f'<circle cx="200" cy="{y}" r="7" fill="#221f1e" stroke="#0e0d0c"/><circle cx="200" cy="{y}" r="2.5" fill="none" stroke="#444" stroke-width=".8"/>' for y in range(y0+26, 350, 46))
    return wrap(o, defs)

def polo_collar(c, dk):
    """Open knit-polo collar: back band round the neck, two spread leaves lying on the
    chest with pointed tips, and an open placket V between them."""
    inside = sh(c, -.40)
    leaf = sh(c, .10)
    o = ''
    # inside of the neck (back lining) and the open V down to the placket
    o += f'<path d="M140 80 Q200 64 260 80 L262 88 L200 178 L138 88 Z" fill="{inside}"/>'
    # back collar band: a low arc round the back of the neck
    o += f'<path d="M140 82 Q200 58 260 82 L252 90 Q200 72 148 90 Z" fill="{leaf}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    # short placket closing the bottom of the V
    o += f'<path d="M191 160 L191 200 L209 200 L209 160" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="1.5"/>'
    o += f'<circle cx="200" cy="189" r="3.4" fill="{sh(c,-.22)}" stroke="{dk}" stroke-width=".8"/>'
    # a soft shadow the leaves cast on the chest
    o += f'<path d="M124 150 L170 156 L198 184 L178 186 L160 166 L126 160 Z M276 150 L230 156 L202 184 L222 186 L240 166 L274 160 Z" fill="{dk}" opacity=".45"/>'
    # leaves: from the neck point, spread out over the chest, points aimed down and out
    o += f'<path d="M140 80 Q134 112 120 152 L168 152 Q186 162 198 180 L176 106 Q168 92 150 88 Z" fill="{leaf}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M260 80 Q266 112 280 152 L232 152 Q214 162 202 180 L224 106 Q232 92 250 88 Z" fill="{leaf}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    # roll line (where the collar folds) and knitted tipping along the edge
    o += f'<path d="M148 90 Q160 120 186 168 M252 90 Q240 120 214 168" fill="none" stroke="{sh(c,.22)}" stroke-width="1.5" opacity=".55"/>'
    o += f'<path d="M125 146 L166 146 Q182 156 192 170 M275 146 L234 146 Q218 156 208 170" fill="none" stroke="{dk}" stroke-width="1" opacity=".45"/>'
    return o

def cuffrib(x, y, w, h, dk):
    return ''.join(f'<line x1="{x+i}" y1="{y+i*0.19:.0f}" x2="{x+i-2}" y2="{y+h+i*0.19:.0f}" stroke="{dk}" stroke-width="1" opacity=".5"/>' for i in range(4, w, 6))

# ---------------- coats ----------------
COAT_BODY = ('M150 70 L92 90 Q70 200 50 344 L100 354 L114 190 L100 374 L300 374 L286 190 '
             'L300 354 L350 344 Q330 200 308 90 L250 70 L200 92 Z')

def coat(c, pattern=None, lapel=True, buttons=2, surface=True):
    dk = sh(c, -.35); defs = grad('g', c)
    pattern = pattern if surface else None
    if pattern == 'herringbone':
        defs += f'<pattern id="pt" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="{c}"/><path d="M0 8 L8 0 L16 8 M0 16 L8 8 L16 16" fill="none" stroke="{sh(c,.42)}" stroke-width="2.2"/></pattern>'
    elif pattern == 'check':
        defs += f'<pattern id="pt" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="{c}"/><rect width="40" height="40" fill="{sh(c,.30)}" opacity=".35"/><rect x="0" y="0" width="20" height="20" fill="{sh(c,.30)}" opacity=".35"/><rect x="20" y="20" width="20" height="20" fill="{sh(c,.30)}" opacity=".35"/><path d="M0 10 H40 M10 0 V40 M0 30 H40 M30 0 V40" stroke="{sh(c,-.4)}" stroke-width="1.2" opacity=".6"/><path d="M0 20 H40 M20 0 V40" stroke="{sh(c,.6)}" stroke-width="1" opacity=".5"/></pattern>'
    fill = 'url(#pt)' if pattern else 'url(#g)'
    o = f'<path d="{COAT_BODY}" fill="{fill}" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
    o += f'<path d="{COAT_BODY}" fill="url(#g)" opacity="{0.22 if pattern else 0}"/>'
    o += f'<path d="M200 92 L206 372" stroke="{dk}" stroke-width="2"/>'
    lap = sh(c, -.12) if not pattern else sh(c, -.05)
    o += f'<path d="M150 70 L200 92 L200 176 L176 138 L142 108 Z" fill="{lap}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M250 70 L200 92 L200 176 L224 138 L258 108 Z" fill="{lap}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M150 70 L142 108 L124 94 L150 58 L200 76 L250 58 L276 94 L258 108 L250 70 L200 92 Z" fill="{sh(c,-.18)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    # flap pockets
    o += f'<path d="M118 262 L172 266 M228 266 L282 262" stroke="{dk}" stroke-width="3"/>'
    o += f'<path d="M118 262 L172 266 L170 278 L116 274 Z M228 266 L282 262 L284 274 L230 278 Z" fill="{sh(c,-.1)}" opacity=".6"/>'
    # armhole seams, sleeve fold, cuff turn-back at the wrist
    o += f'<path d="M114 190 L150 70 M286 190 L250 70" stroke="{dk}" stroke-width="1.5" opacity=".6" fill="none"/>'
    o += f'<path d="M94 150 Q82 250 76 330 M306 150 Q318 250 324 330" fill="none" stroke="{dk}" stroke-width="1" opacity=".25"/>'
    o += f'<path d="M53 322 L102 332 M347 322 L298 332" stroke="{dk}" stroke-width="1.6" opacity=".7"/>'
    o += ''.join(f'<circle cx="{x}" cy="{y}" r="3" fill="#1a1716"/>' for x, y in ((90, 336), (310, 336)))
    for i in range(buttons):
        o += f'<circle cx="212" cy="{200+i*56}" r="7" fill="#1a1716" stroke="#0a0908"/>'
    return wrap(o, defs)

def puffer(c, surface=True):
    dk = sh(c, -.35); defs = grad('g', c)
    body = ('M150 82 L96 100 Q76 200 62 318 L106 326 L112 200 L104 332 L296 332 L288 200 '
            'L294 326 L338 318 Q324 200 304 100 L250 82 Z')
    o = f'<path d="{body}" fill="url(#g)" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
    for y in range(126, 330, 44):
        o += f'<path d="M108 {y} Q200 {y+16} 292 {y}" fill="none" stroke="{dk}" stroke-width="2" opacity=".65"/>'
        o += f'<path d="M108 {y-8} Q200 {y+8} 292 {y-8}" fill="none" stroke="{sh(c,.2)}" stroke-width="2" opacity=".35"/>'
    for y in range(136, 300, 38):
        # sleeve baffles
        o += f'<path d="M{96-(y-100)*0.17:.0f} {y} L{110-(y-100)*0.02:.0f} {y+8}" stroke="{dk}" stroke-width="1.6" opacity=".45"/>'
        o += f'<path d="M{304+(y-100)*0.17:.0f} {y} L{290+(y-100)*0.02:.0f} {y+8}" stroke="{dk}" stroke-width="1.6" opacity=".45"/>'
    o += f'<rect x="196" y="100" width="8" height="232" fill="{sh(c,-.4)}"/>' + ''.join(f'<rect x="197" y="{y}" width="6" height="2" fill="#8a857e"/>' for y in range(104, 330, 6))
    o += f'<path d="M150 82 L156 52 Q200 66 244 52 L250 82 Q200 100 150 82 Z" fill="{sh(c,-.1)}" stroke="{dk}" stroke-width="2"/>'
    o += f'<rect x="118" y="256" width="58" height="34" rx="4" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="1.5"/><rect x="224" y="256" width="58" height="34" rx="4" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="1.5"/>'
    o += f'<path d="M62 318 L106 326 L104 344 L58 336 Z M338 318 L294 326 L296 344 L342 336 Z" fill="{sh(c,-.15)}" stroke="{dk}" stroke-width="2"/>'
    return wrap(o, defs)


# ---------------- shirt / overshirt ----------------
def shirt(c, pockets=2, snaps=False, surface=True):
    """Long-sleeve shirt: point collar, button placket, yoke, chest flap pockets, buttoned cuffs."""
    dk = sh(c, -.30); defs = grad('g', c)
    body = ('M130 80 L76 100 Q58 190 42 330 L92 340 L114 196 L110 356 Q200 368 290 356 L286 196 '
            'L308 340 L358 330 Q342 190 324 100 L270 80 Q200 100 130 80 Z')
    o = f'<path d="{body}" fill="url(#g)" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M114 196 L130 80 M286 196 L270 80" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".6"/>'
    o += f'<path d="M122 112 Q200 124 278 112" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".6"/>'
    # buttoned cuffs
    o += f'<path d="M42 330 L92 340 L88 366 L38 356 Z M358 330 L308 340 L312 366 L362 356 Z" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    # placket and buttons
    o += f'<path d="M192 100 L192 362 M208 100 L208 362" stroke="{dk}" stroke-width="1.3" opacity=".7"/>'
    btn = '#1a1817' if snaps else sh(c, -.4)
    o += ''.join(f'<circle cx="200" cy="{y}" r="{5 if snaps else 4}" fill="{btn}" stroke="#0e0d0c" stroke-width=".8"/>' for y in range(128, 350, 44))
    # chest pockets with flaps
    for x in ([126, 222] if pockets == 2 else [126])[:pockets]:
        o += f'<path d="M{x} 150 L{x+52} 150 L{x+52} 212 L{x+26} 220 L{x} 212 Z" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".7"/>'
        o += f'<path d="M{x-2} 146 L{x+54} 146 L{x+54} 164 L{x+26} 172 L{x-2} 164 Z" fill="{sh(c,-.05)}" stroke="{dk}" stroke-width="1.5"/>'
        o += f'<circle cx="{x+26}" cy="162" r="3.5" fill="{btn}"/>'
    # collar: inside of the neck, band plus two points
    o += f'<path d="M130 80 Q200 60 270 80 Q200 104 130 80 Z" fill="{sh(c,-.35)}"/>'
    o += f'<path d="M136 80 Q200 64 264 80 L262 90 Q200 76 138 90 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="1.5"/>'
    o += f'<path d="M138 84 L150 132 L194 104 L200 92 Z" fill="{sh(c,.05)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M262 84 L250 132 L206 104 L200 92 Z" fill="{sh(c,.05)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/>'
    return wrap(o, defs)

# ---------------- bomber ----------------
def bomber(c, sleeves=None, surface=True):
    """Bomber: ribbed collar, cuffs and hem band, zip, welt pockets. sleeves= a second colour
    for two-tone jackets (e.g. suede body with knit sleeves)."""
    dk = sh(c, -.35); defs = grad('g', c)
    sc = sleeves or c; sdk = sh(sc, -.3)
    rib = sh(sleeves or c, -.06)
    arm_l = 'M150 84 L94 102 Q72 200 56 320 L104 330 L114 196 Z'
    arm_r = 'M250 84 L306 102 Q328 200 344 320 L296 330 L286 196 Z'
    o = f'<path d="{arm_l}" fill="{sc}" stroke="{sdk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="{arm_r}" fill="{sc}" stroke="{sdk}" stroke-width="2" stroke-linejoin="round"/>'
    o += f'<path d="M150 84 L114 196 L110 328 L290 328 L286 196 L250 84 Q200 104 150 84 Z" fill="url(#g)" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
    # rib bands
    o += f'<path d="M56 320 L104 330 L101 354 L52 344 Z M344 320 L296 330 L299 354 L348 344 Z" fill="{rib}" stroke="{sdk}" stroke-width="2"/>'
    o += cuffrib(56, 322, 46, 22, sdk) + cuffrib(298, 322, 46, 22, sdk)
    o += f'<path d="M110 328 L290 328 L292 358 L108 358 Z" fill="{rib}" stroke="{sdk}" stroke-width="2"/>'
    o += ''.join(f'<line x1="{x}" y1="330" x2="{x}" y2="356" stroke="{sdk}" stroke-width="1" opacity=".45"/>' for x in range(116, 290, 8))
    o += f'<path d="M150 84 L156 56 Q200 70 244 56 L250 84 Q200 104 150 84 Z" fill="{rib}" stroke="{sdk}" stroke-width="2"/>'
    o += ''.join(f'<line x1="{x}" y1="{60+abs(x-200)*0.02:.0f}" x2="{x}" y2="{86+ (1-abs(x-200)/50)*8:.0f}" stroke="{sdk}" stroke-width="1" opacity=".4"/>' for x in range(160, 242, 7))
    # zip, welt pockets, seams
    o += f'<rect x="197" y="96" width="6" height="262" fill="{sh(c,-.4)}"/>' + ''.join(f'<rect x="198" y="{y}" width="4" height="2" fill="#c9c6bd"/>' for y in range(98, 356, 5))
    o += f'<path d="M126 238 L140 300 M274 238 L260 300" stroke="{dk}" stroke-width="3" stroke-linecap="round"/>'
    o += f'<path d="M114 196 L150 84 M286 196 L250 84" stroke="{dk}" stroke-width="1.5" opacity=".6" fill="none"/>'
    return wrap(o, defs)

# ---------------- trousers ----------------
# Straight legs, no taper: outseam vertical from hip to hem, 86 px per leg at the hem.
TROUSER_BODY = 'M122 40 L278 40 L290 140 L293 374 L207 374 L200 178 L193 374 L107 374 L110 140 Z'

def trousers(c, kind='trouser', surface=True):
    dk = sh(c, -.30); defs = grad('g', c)
    twill = kind == 'denim' and surface
    if twill:
        defs += f'<pattern id="dn" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="url(#g)"/><path d="M0 4 L4 0" stroke="{sh(c,.12)}" stroke-width=".7" opacity=".6"/></pattern>'
    fill = 'url(#dn)' if twill else 'url(#g)'
    o = f'<path d="{TROUSER_BODY}" fill="{fill}" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
    if kind != 'denim':
        o += f'<path d="M152 128 L151 374 M248 128 L249 374" stroke="{sh(c,.22)}" stroke-width="2" opacity=".55"/>'
        o += f'<path d="M155 128 L154 374 M245 128 L246 374" stroke="{dk}" stroke-width="1" opacity=".4"/>'
    else:
        o += f'<path d="M150 180 Q152 280 150 374 M250 180 Q248 280 250 374" stroke="{sh(c,.18)}" stroke-width="3" opacity=".25" fill="none"/>'
    o += f'<path d="M122 40 L278 40 L280 62 L120 62 Z" fill="{sh(c,-.08)}" stroke="{dk}" stroke-width="2"/>'
    o += f'<path d="M200 62 L200 176 M212 62 Q216 122 200 176" fill="none" stroke="{dk}" stroke-width="1.5"/>'
    for x in (138, 196, 260):
        o += f'<rect x="{x}" y="36" width="8" height="30" rx="2" fill="{sh(c,-.15)}" stroke="{dk}" stroke-width="1"/>'
    if kind == 'denim':
        st = '#c99a5b'
        o += f'<path d="M122 62 Q150 100 176 66 M278 62 Q250 100 224 66" fill="none" stroke="{st}" stroke-width="1.5"/>'
        o += f'<circle cx="126" cy="66" r="3" fill="#b08a4a"/><circle cx="274" cy="66" r="3" fill="#b08a4a"/><circle cx="176" cy="66" r="3" fill="#b08a4a"/>'
        o += f'<circle cx="200" cy="52" r="6" fill="#a8843f" stroke="#6b5227"/>'
        o += f'<path d="M200 66 L202 174 M206 66 Q212 122 202 174" fill="none" stroke="{st}" stroke-width="1"/>'
        o += f'<path d="M107 368 L193 368 M207 368 L293 368" stroke="{st}" stroke-width="1.5"/>'
    elif kind == 'chino':
        o += f'<path d="M122 62 Q156 96 178 68 M278 62 Q244 96 222 68" fill="none" stroke="{dk}" stroke-width="1.5"/>'
        o += f'<circle cx="200" cy="52" r="5" fill="{sh(c,-.2)}" stroke="{dk}"/>'
    else:
        o += f'<path d="M130 62 L148 96 M270 62 L252 96" stroke="{dk}" stroke-width="1.5"/>'
        o += f'<rect x="192" y="48" width="18" height="8" rx="2" fill="{sh(c,-.25)}"/>'
        o += f'<path d="M107 374 L193 374 L193 358 L107 358 Z M207 374 L293 374 L293 358 L207 358 Z" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="1.5"/>'
    return wrap(o, defs)

# ---------------- shoes ----------------
# Shoes use the photo cutout directly; these silhouettes are a fallback preview only.
def shoe_pair(inner_fn):
    return f'<g transform="translate(14 -70) scale(.9)" opacity=".95">{inner_fn()}</g><g transform="translate(20 40) scale(.9)">{inner_fn()}</g>'

def loafer(c, penny=False, surface=True):
    dk = sh(c, -.4); lt = sh(c, .22); defs = grad('g', c)
    def one():
        return (f'<path d="M40 250 Q60 278 130 282 L330 282 Q372 282 372 262 Q372 246 340 238 L250 216 Q200 196 168 186 Q110 174 76 210 Q40 232 40 250 Z" fill="url(#g)" stroke="{dk}" stroke-width="2.2"/>'
                f'<path d="M92 214 Q140 196 210 214 Q250 226 252 236 Q200 246 148 236 Q108 230 92 214 Z" fill="{sh(c,-.22)}" stroke="{dk}" stroke-width="1.5"/>'
                f'<path d="M100 232 Q160 246 240 238" fill="none" stroke="{lt}" stroke-width="1.5" opacity=".7"/>'
                + (f'<path d="M156 232 L170 252 L232 246 L246 226" fill="{sh(c,-.05)}" stroke="{dk}" stroke-width="2" stroke-linejoin="round"/><path d="M190 238 L214 236 L212 246 L192 248 Z" fill="{dk}"/>' if penny else '')
                + f'<path d="M40 250 Q60 278 130 282 L330 282 Q372 282 372 262 L372 270 Q372 292 330 292 L130 292 Q56 290 36 258 Z" fill="#1d1a18" stroke="#0e0c0b" stroke-width="1.5"/>'
                f'<path d="M262 226 Q300 224 340 238" fill="none" stroke="{lt}" stroke-width="2" opacity=".5"/>')
    return wrap(shoe_pair(one), defs)

def chelsea(c, surface=True):
    dk = sh(c, -.4); lt = sh(c, .2); defs = grad('g', c)
    def one():
        return (f'<path d="M40 258 Q60 286 130 290 L330 290 Q372 290 372 270 Q372 254 340 246 L262 226 L262 110 Q262 92 240 92 L150 92 Q126 92 126 112 L124 200 Q70 216 40 258 Z" fill="url(#g)" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
                f'<path d="M180 108 L188 200 L226 200 L232 108 Z" fill="#2a2523" stroke="{dk}" stroke-width="1.5"/>'
                + ''.join(f'<line x1="{x}" y1="112" x2="{x}" y2="198" stroke="#444" stroke-width="1" opacity=".5"/>' for x in range(188, 228, 6))
                + f'<path d="M124 200 Q190 214 262 226" fill="none" stroke="{dk}" stroke-width="1.5" opacity=".7"/>'
                f'<path d="M150 92 L152 74 L240 74 L240 92" fill="none" stroke="{dk}" stroke-width="2"/><rect x="150" y="72" width="90" height="10" rx="3" fill="{sh(c,-.1)}" stroke="{dk}"/>'
                f'<path d="M40 258 Q60 286 130 290 L330 290 Q372 290 372 270 L372 284 Q372 304 330 304 L130 304 Q56 302 34 266 Z" fill="#1a1715" stroke="#0e0c0b" stroke-width="1.5"/>'
                f'<path d="M60 262 Q120 300 330 296" fill="none" stroke="#3a3533" stroke-width="2"/>'
                f'<path d="M262 228 Q300 232 340 246" fill="none" stroke="{lt}" stroke-width="2" opacity=".5"/>')
    return wrap(shoe_pair(one), defs)

def sneaker(c, sole='#f2f0eb', stripe=None, runner=False, accent=None, surface=True):
    dk = sh(c, -.4); defs = grad('g', c)
    def one():
        s = (f'<path d="M36 252 Q56 280 130 284 L340 284 Q376 284 376 262 Q376 244 340 236 L270 222 Q220 196 178 176 Q120 156 82 196 Q40 226 36 252 Z" fill="url(#g)" stroke="{dk}" stroke-width="2.2" stroke-linejoin="round"/>'
             f'<path d="M36 252 Q56 280 130 284 L340 284 Q376 284 376 262 L378 276 Q378 300 336 300 L128 300 Q52 298 32 262 Z" fill="{sole}" stroke="{sh(sole,-.35)}" stroke-width="1.8"/>'
             f'<path d="M50 268 Q120 292 340 290" fill="none" stroke="{sh(sole,-.2)}" stroke-width="1.5"/>')
        s += f'<path d="M270 222 Q320 232 340 236 Q376 244 376 262 L340 284 L280 284 Q296 250 270 222 Z" fill="{sh(c,.08)}" stroke="{dk}" stroke-width="1.5" opacity=".9"/>'
        s += f'<path d="M120 196 Q170 190 226 222 L212 240 Q160 216 118 222 Z" fill="{sh(c,-.06)}" stroke="{dk}" stroke-width="1.5"/>'
        for i in range(5):
            x = 132+i*20; s += f'<path d="M{x} {202+i*4} L{x+14} {214+i*5}" stroke="{sole}" stroke-width="4" stroke-linecap="round"/>'
        s += f'<path d="M82 196 Q100 170 130 168 L128 200 Q100 206 82 196 Z" fill="{sh(c,-.15)}" stroke="{dk}" stroke-width="1.5"/>'
        if stripe:
            for i in range(3):
                s += f'<path d="M{140+i*26} 232 L{168+i*26} 284 L{156+i*26} 284 L{128+i*26} 232 Z" fill="{stripe}" stroke="{sh(stripe,-.3)}" stroke-width="1"/>'
        if runner:
            s += f'<path d="M150 236 L200 284 L184 284 L134 236 Z" fill="{accent or "#9aa3ad"}" stroke="{dk}" stroke-width="1"/>'
            s += f'<path d="M172 236 L222 284 L206 284 L156 236 Z" fill="{sh(c,.35)}" stroke="{dk}" stroke-width="1"/>'
            s += f'<path d="M96 220 Q140 250 260 262" fill="none" stroke="{sh(c,.4)}" stroke-width="3" opacity=".7"/>'
            s += f'<path d="M40 258 Q60 262 130 266 L340 268" fill="none" stroke="{sh(sole,-.45)}" stroke-width="3"/>'
        return s
    return wrap(shoe_pair(one), defs)

# ---------------- registry ----------------
# name -> (function, fixed kwargs, category, rule attributes implied by the template)
TEMPLATES = {
    'crew':     (top,      {'neck': 'crew'},              'top',    {'w': 2}),
    'mock':     (top,      {'neck': 'mock'},              'top',    {'w': 2}),
    'polo':     (top,      {'neck': 'polo'},              'top',    {'w': 2}),
    'zip':      (top,      {'neck': 'mock', 'zip': 'full'}, 'top',  {'w': 3, 'tex': 'chunky'}),
    'cardigan': (top,      {'neck': 'mock', 'buttons': True}, 'top', {'w': 3, 'tex': 'chunky'}),
    'shirt':    (shirt,    {},                            'top',    {'w': 1}),
    'coat':     (coat,     {},                            'outer',  {'w': 3}),
    'puffer':   (puffer,   {},                            'outer',  {'w': 3, 'casual': 1}),
    'bomber':   (bomber,   {},                            'outer',  {'w': 2}),
    'trousers': (trousers, {'kind': 'trouser'},           'bottom', {'kind': 'trouser'}),
    'chinos':   (trousers, {'kind': 'chino'},             'bottom', {'kind': 'chino'}),
    'denim':    (trousers, {'kind': 'denim'},             'bottom', {'kind': 'denim'}),
    'loafer':   (loafer,   {},                            'shoes',  {'style': 'loafer'}),
    'chelsea':  (chelsea,  {},                            'shoes',  {'style': 'boot'}),
    'sneaker':  (sneaker,  {},                            'shoes',  {'style': 'sneaker'}),
    'runner':   (sneaker,  {'runner': True, 'sole': '#5a5c60'}, 'shoes', {'style': 'sneaker'}),
}

def parse(spec):
    """'coat:herringbone,buttons=3' -> ('coat', {'pattern':'herringbone','buttons':3})"""
    name, _, rest = spec.partition(':')
    if name not in TEMPLATES:
        raise ValueError(f'unknown template {name!r}; choose from {", ".join(TEMPLATES)}')
    kw = {}
    for tok in filter(None, (t.strip() for t in rest.split(','))):
        if '=' in tok:
            k, v = tok.split('=', 1)
            kw[k] = int(v) if v.isdigit() else v
        elif name == 'coat' and tok in ('herringbone', 'check'):
            kw['pattern'] = tok
        elif name == 'zip' and tok in ('half', 'full'):
            kw['zip'] = tok
        elif name == 'cardigan' and tok == 'v':
            kw['neck'] = 'v'
        else:
            kw[tok] = True
    return name, kw

def implied(spec):
    """category and rule attributes a template implies (weight, texture, trouser kind, shoe style)"""
    name, kw = parse(spec)
    fn, fixed, cat, attrs = TEMPLATES[name]
    attrs = dict(attrs)
    if name == 'coat' and kw.get('pattern'): attrs['tex'] = 'pattern'
    return cat, attrs

def render(spec, colour, surface=True):
    name, kw = parse(spec)
    fn, fixed, _, _ = TEMPLATES[name]
    return fn(colour, **{**fixed, **kw, 'surface': surface})

def to_png(svg, size=800):
    import cairosvg, io
    from PIL import Image
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert('RGBA')

if __name__ == '__main__':
    # preview every piece's template: python draw.py [pieces.json] -> _templates.jpg next to it
    import sys, os
    from PIL import Image
    pj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'pieces.json')
    pieces = json.load(open(pj))
    items = [(p['key'], render(p['template'], p['hex'])) for p in pieces]
    cols = 6; sheet = Image.new('RGB', (cols*250, ((len(items)+cols-1)//cols)*250), (237, 232, 225))
    for i, (k, s) in enumerate(items):
        im = to_png(s, 240); sheet.paste(im, ((i % cols)*250+5, (i//cols)*250+5), im)
    out = os.path.join(os.path.dirname(pj), 'images', '_templates.jpg')
    sheet.save(out, quality=88); print(out)
