# Digital wardrobe

Phone photos of clothes → consistent catalogue images → one-file outfit app.

```
pieces.json      every piece: name, category, colour, template, occasions, rule attributes
rules.json       matching rules (shoes vs trousers, black+brown, texture hero, warmth, occasion)
looks.json       saved looks and Good vs Better pairs
images/          <key>.webp (560 px, transparent, for the app) and _sheet.jpg (contact sheet)
sources/         colour-corrected cutouts the images are rendered from
photos/          the original photos (downscaled)
pipeline/        add_piece.py and the steps it runs
app/             app_template.html + rules.js → index.html (self-contained, open on a phone)
tests/           test_rules.py
```

## Add a piece

```
cd pipeline
python add_piece.py photo.jpg --key navy_cardigan --name "Navy cardigan" --cat top \
    --colour navy --template cardigan --hex "#252a3c" --occasions office,evening
```

Only `--name` and `--occasions` are required; the rest is inferred (key from name, category
from template, hex from the photo, colour name from hex). Re-shoot with `--replace`.
Rebuild images from sources: `--rerender KEY|all`. Rebuild sheet and app only: `--build`.

## Pipeline

1. `cutout.py` rembg `isnet-general-use` (falls back to `u2net` when the mask is empty,
   fragmented or swallows the background); removes pink ottoman pixels (r-b>20, r-g>10, with
   a hue guard so brown and beige cloth survive); keeps the largest component (both shoes of a pair).
2. `prod.py` warm-cast correction (×0.96/1.04/1.18), large-radius shadow flattening, alpha tightening.
3. `draw.py` SVG templates: crew, mock, polo (open collar), zip, cardigan, coat
   (herringbone/check), puffer, trousers/chinos/denim, loafer, chelsea, sneaker, runner;
   long or short sleeves.
4. `hybrid.py` quilts 30–40 clean high-passed fabric windows from the cutout into the
   silhouette, multiplies by the SVG shading, keeps hardware from the SVG, pulls the fabric
   colour towards the piece's hex (photos under warm light misjudge black and cream), adds edge
   darkening, key light and drop shadow. Shoes use the corrected cutout directly.
5. 560 px webp per piece plus `_sheet.jpg`.

Pieces marked `"source_kind": "kit"` come from the first build's images (no photo yet) and
render with template surface patterns off; replace them with `--replace` as photos arrive.

`KIT_README.md` is the first build's readme.
