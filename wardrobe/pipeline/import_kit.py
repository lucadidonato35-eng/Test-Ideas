"""One-off: seed sources/ from the first build's imgs_hybrid.json (no original photos).

    python import_kit.py path/to/imgs_hybrid.json

Those images are already colour-corrected, so they go straight to sources/<key>.png and
the piece is marked "source_kind": "kit". Their fabric already carries the old
template's surface pattern, so they render with surface patterns off (no double rib).
Re-shoot any piece with add_piece.py --replace to move it onto a real photo.
"""
import sys, os, json, base64, io
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def main(path):
    imgs = json.load(open(path))
    pj = os.path.join(ROOT, 'pieces.json')
    pieces = json.load(open(pj))
    os.makedirs(os.path.join(ROOT, 'sources'), exist_ok=True)
    for p in pieces:
        uri = imgs.get(p['key'])
        if not uri: continue
        im = Image.open(io.BytesIO(base64.b64decode(uri.split(',', 1)[1]))).convert('RGBA')
        im.save(os.path.join(ROOT, 'sources', f"{p['key']}.png"), optimize=True)
        p['source'] = f"sources/{p['key']}.png"
        p['source_kind'] = 'kit'
        p['surface'] = False
        print('imported', p['key'])
    json.dump(pieces, open(pj, 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main(sys.argv[1])
