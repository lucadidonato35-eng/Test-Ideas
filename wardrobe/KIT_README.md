# Digital Wardrobe starter kit

Working code from the first build. Everything runs offline in Python + one HTML file.

pipeline/
  prod.py    colour-correct and de-shadow a cutout (expects cut/<key>.png with alpha, from rembg)
  draw.py    SVG garment templates (top, coat, puffer, trousers, loafer, chelsea, sneaker) keyed by piece
  hybrid.py  fills the SVG silhouette with real fabric quilted from the photo cutout, adds studio shading and shadow
app/
  app_template.html   the app; the string __IMGS__ is replaced by a JSON map {key: dataURI}
  imgs_hybrid.json    current 23 pieces, ready to inject

Flow for a new piece: photo -> rembg cutout -> prod.py -> add template + colour in draw.py -> hybrid.py -> add entry in P (and OCC rules) in app_template.html -> rebuild -> publish.
