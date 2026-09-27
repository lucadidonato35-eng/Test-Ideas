# Closet

The digital wardrobe app. One HTML file, phone-first, works offline once loaded.

Build: `python closet/build.py` (also run by `wardrobe/pipeline/add_piece.py`). Data comes from
`../wardrobe` (pieces, rules, looks, illustrated renders in `images/`, studio photos in `images/photo/`).

## What it does

- **Today**: local weather (Open-Meteo, Copenhagen or your location) decides whether the
  warmth rule applies; suggests a look for the occasion, least recently worn first; logs what you wear.
- **Mix**: swipe each row, tap to pick. Lock pieces, Shuffle the rest (only Strong matches).
  **Fix it** finds the smallest swap (one piece, else two) that turns the look into a Strong match.
  Save, edit or save-as-new.
- **Looks**: all looks, your own, and Good vs Better. Share any look or pair as an Instagram-sized image.
- **Closet**: every piece; switch each between studio photo and illustration (or all at once).
  Edit name, category, type, colour, occasions. **Add a piece**: photo -> background removed on the
  phone (@imgly/background-removal, model downloaded once, ~55 MB) -> fill in the details -> three
  looks it makes with what you own.
- **Insights**: how many Strong matches the closet makes, **what to buy next** (the piece that
  unlocks the most new matches), work horses, hard-to-wear pieces, unworn in a month, palette.

Edits, added pieces, saved looks and the wear log stay on the phone (IndexedDB). Export makes
a backup file; send it to Claude to bring new pieces into the repo at studio quality.

## Studio photos

`wardrobe/pipeline/studio.py` renders the real photo as a product flat-lay: cutout, background-edge
cleanup, cast-shadow evening, colour correction, straightening, colour anchor, contact shadow.
Crumpled or hanging shots still look better as illustrations, so `PHOTO_DEFAULT` in `build.py`
lists the pieces that default to the photo.
