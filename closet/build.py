"""Build closet/index.html: one self-contained file (pieces, rules, looks, both renders of
every piece inlined). Data comes from ../wardrobe; edits made in the app live on the phone
(IndexedDB) and can be exported as a backup file.

    python closet/build.py
"""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, '..', 'wardrobe')

# Pieces whose studio photo beats the illustration (flat-lay shots with clean light).
# Everything else defaults to the illustration; each can be switched in the app.
PHOTO_DEFAULT = {'zip', 'cardigan', 'white_rib', 'si', 'navy_zip_polo', 'navy_half_zip', 'ecru_jeans'}

# "What to buy next": typical pieces, scored in the app by how many new Strong matches
# each would unlock with what is already in the closet.
ARCHETYPES = [
    {'key': 'x_grey_flannel', 'name': 'Grey flannel trousers', 'cat': 'bottom', 'colour': 'grey', 'kind': 'trouser', 'hex': '#8C8A87', 'occasions': ['Office', 'Evening']},
    {'key': 'x_charcoal_chino', 'name': 'Charcoal chinos', 'cat': 'bottom', 'colour': 'charcoal', 'kind': 'chino', 'hex': '#3A3B3E', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_brown_cord', 'name': 'Brown corduroy trousers', 'cat': 'bottom', 'colour': 'brown', 'kind': 'trouser', 'hex': '#6B4A35', 'occasions': ['Evening', 'Weekend']},
    {'key': 'x_camel_coat', 'name': 'Camel overcoat', 'cat': 'outer', 'colour': 'camel', 'w': 3, 'hex': '#B08A5A', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_navy_coat', 'name': 'Navy overcoat', 'cat': 'outer', 'colour': 'navy', 'w': 3, 'hex': '#1F2638', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_oxford', 'name': 'Light blue oxford shirt', 'cat': 'top', 'colour': 'blue', 'w': 1, 'hex': '#A9BCD6', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_grey_merino', 'name': 'Grey merino crew', 'cat': 'top', 'colour': 'grey', 'w': 2, 'hex': '#8E8C88', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_cream_cable', 'name': 'Cream cable knit', 'cat': 'top', 'colour': 'cream', 'w': 3, 'tex': 'chunky', 'hex': '#E6DFD1', 'occasions': ['Evening', 'Weekend']},
    {'key': 'x_suede_loafer', 'name': 'Dark brown suede loafers', 'cat': 'shoes', 'colour': 'brown', 'style': 'loafer', 'hex': '#4A3226', 'occasions': ['Office', 'Evening', 'Weekend']},
    {'key': 'x_white_sneaker', 'name': 'White leather sneakers', 'cat': 'shoes', 'colour': 'white', 'style': 'sneaker', 'hex': '#F2F0EA', 'occasions': ['Weekend']},
]

def uri(path):
    return 'data:image/webp;base64,'+base64.b64encode(open(path, 'rb').read()).decode()

def build():
    pieces = json.load(open(os.path.join(W, 'pieces.json')))
    rules = json.load(open(os.path.join(W, 'rules.json')))
    looks = json.load(open(os.path.join(W, 'looks.json')))
    images, defaults = {}, {}
    for p in pieces:
        k = p['key']
        im = {'ill': uri(os.path.join(W, 'images', f'{k}.webp'))}
        ph = os.path.join(W, 'images', 'photo', f'{k}.webp')
        if os.path.exists(ph): im['photo'] = uri(ph)
        images[k] = im
        defaults[k] = 'photo' if (p['cat'] == 'shoes' or k in PHOTO_DEFAULT) and 'photo' in im else 'ill'
    keep = ('key', 'name', 'short', 'cat', 'colour', 'hex', 'occasions', 'w', 'tex', 'kind', 'style', 'casual')
    slim = [{k: v for k, v in p.items() if k in keep} for p in pieces]
    data = {'pieces': slim, 'rules': rules, 'looks': looks, 'images': images, 'defaults': defaults,
            'archetypes': ARCHETYPES}
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = open(os.path.join(HERE, 'app.html')).read()
    rules_js = open(os.path.join(W, 'app', 'rules.js')).read()
    html = html.replace('/*__RULES_JS__*/', rules_js).replace('/*__DATA__*/null', blob)
    out = os.path.join(HERE, 'index.html')
    open(out, 'w').write(html)
    # web-page build for publishing: no document skeleton (the host adds it), hosted flag set
    import re
    head = re.search(r'<head>(.*?)</head>', html, re.S).group(1)
    head = re.sub(r'<meta[^>]*>\s*', '', head)
    body = re.search(r'<body>(.*)</body>', html, re.S).group(1)
    page = head.strip()+'\n<script>window.CLOSET_HOSTED = true;</script>\n'+body.strip()+'\n'
    open(os.path.join(HERE, 'artifact.html'), 'w').write(page)
    return out

if __name__ == '__main__':
    out = build()
    print(out, f'{os.path.getsize(out)//1024} KB')
