# Digital wardrobe

Everything lives in `wardrobe/`. See `wardrobe/README.md` for the layout.

Setup in a fresh container: `pip install -r wardrobe/requirements.txt` (rembg downloads its models on first use).

## "New piece" + photo

When the user says "new piece" and attaches a photo (uploads land in `/root/.claude/uploads/...`):

1. Look at the photo and infer what you can: template (`python -c "import sys;sys.path.insert(0,'wardrobe/pipeline');import draw;print(list(draw.TEMPLATES))"`, options like `polo:zip=half,sleeves=short`, `coat:check`, `crew:rib`), colour name, hex, weight (short sleeves / thin knit = 1, knit = 2, chunky or coat = 3), texture (`pattern` for patterned coats, `chunky` for heavy knits), casual.
   Do not add a template surface pattern (rib, cable) when the photo already shows that knit clearly.
2. Ask the user only for what the photo cannot tell you: **category** (if ambiguous), **occasions** (Office / Evening / Weekend) and a **name**. Propose defaults so they can just say yes.
3. Run from `wardrobe/pipeline/`:
   `python add_piece.py PHOTO --name "..." --occasions office,evening [--template ... --hex ... --colour ... --weight N --texture ... --casual]`
   Add `--replace --key KEY` to re-shoot an existing piece (pass its existing occasions and flags again).
   After changing the pipeline: `--reprocess all` (photo pieces, from `photos/`) and `--rerender all` (everything, from `sources/`).
   This writes `images/<key>.webp`, `sources/`, `photos/`, updates `pieces.json`, rebuilds `images/_sheet.jpg` and `app/index.html`, and prints looks that pass every rule.
4. Pick 2–3 of the printed suggestions (or better ones), give each a name and a one-line "why", append them to `looks.json` → `looks`, then `python add_piece.py --build`.
5. `python tests/test_rules.py` (from `wardrobe/`) must pass.
6. Show the user `images/_sheet.jpg` (new piece is outlined) and the new looks; commit and push.

## Photo guidance to pass on

Flat on the pink ottoman, one garment per photo, nothing crossing it, arms laid down. Hanging shots with a rail pole in front or a hand on the hanger cut out badly. Shoes as a pair from above.

## Rules

Matching rules are data in `wardrobe/rules.json`, read by `app/rules.js` (app) and `pipeline/rules.py` (suggestions, checks). If you change the logic, change both; `tests/test_rules.py` compares them on every combination.
