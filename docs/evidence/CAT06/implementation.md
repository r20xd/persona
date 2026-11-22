# CAT06 — true pixel sprites and multiple toys

Executor: explicitly spawned gpt-6.1-sol / low, single writer. Read current TASK/AGENTS, architecture27/UI20, plan, agent task/review/workflow templates, CAT05 implementation/review and current Taste2.5.1. Viewed both ignored personal reference sheets. They supplied shape/identity references only; generator never reads a raster. No existing raster, personal file, dependency or authentication module changed. User `.gitignore` and old CAT04/versioning report untouched.

## Native pixel assets

`scripts/generate_cat_pixel32.py` draws new original integer-grid primitives with a deterministic standard-library indexed PNG encoder. Shared palette12entries, transparentindex0 and all other alpha255. No antialiasing, interpolation, gradient, blend mode or random generation. Lavender cheek/chin clusters added after parent's first art review to distinguish head/body. Root approved enlarged preview before implementation continued.

- `static/images/cat-pixel32/{sleepy,scholar,chaos}.png`: exact32×32 base images.
- `{character}-{idle,jump,joy}-{0,1,2,3}.png`:36exact32×32 animation frames. Base image bytes equal idle0.
- `toy-{yarn,ball,mouse,fish}.png`:4exact16×16 matching toys.
- `preview-{character}.png`:8×integer nearest preview generated from the same grid; `contact-sheet.png`:4×nearest,3character rows, each idle4/jump4/joy4. `pixel-properties.json` records decoded dimensions/palette/alpha for all43runtimefiles.

Runtime uses real PNG frames, with every URL resolved through Django static storage before JSONscript output; WhiteNoise hashed URLs are fetched in browser tests. No SVGviewBox crop, old1536sheets, mix-blend or bitmap transform remains. Original sheets and historical evidence are preserved.

## Scene and data

Scene logical64×48: cat32×32, four fixed16×16toy slots near/below paws. No toy covers the face or another toy. Mobile companion/profile stack into full-width portraits; desktop profile column256px. Toys now display at least64px in tested360/1440 scenes; thumbnails80pxfallback.

Local ResizeObserver scales and positions the whole scene and thumbnails to integer physical device pixels. DPR1.25 may use fractional CSSpx, explicitly approved by parent, so the physical pixel blocks stay equal. Scroll/resize realign global origins. Basic CSS4×fallback supports JSoff. Profile loads sizing code but returns before game setup; only one script inclusion per page. Existing idle/jump/joy, pause/hidden/calm/reduced-motion and BFCache ticker cleanup retained,20second game/reward receipt untouched.

`StudentCat.toys` JSONField(default=list), additive0006: transfers each legacy selected toy to a singleton list. Name/character/completed/last_attempt retained. Legacy accessory remains for compatibility and is synchronized to the first canonical chosen toy ornone on every service save; app reads only toys. Canonical orderyarn/ball/mouse/fish. MultipleChoice field limits values to earned toys, rejects unknown/locked/type-invalid input, deduplicates, supports empty clear. Owner/role checks and parent locking remain unchanged. Native checkbox group has legend/visible labels, explanatory clear instruction and first-reward empty state; saving works without JavaScript.

## Actual verification

- `tests/test_cat_pixels.py`:2passed0.08s. Independent PNG decode checks CRC/grid/indexed palette/binary alpha, identity/motion differences and regeneration byte equality in an empty temporary folder, without source rasters.
- `TEST_DB_PORT=55446 TEST_DB_USER=deanery TEST_DB_NAME=test_cat06_executor .venv/bin/pytest tests/test_cat.py -q --tb=short`:14passed4.88s. Includes persistence, earned/unknown/type validation, duplicate canonicalization, clearing, roles/CSRF/cross-account isolation,0005→0006 preservation/reverse compatibility and prior reward protocol.
- Targeted browser initialrun:8passed1failed48.33s. Failure atDPR1.25 was193px locator screenshot clipping versus actual192px image: Playwright rounds fractional CSSclip outwards. No pass claimed for that run. Corrected verification decodes a whole device viewport screenshot and samples measured physical sprite bounds, then checks every pixel in all32×32logical blocks is exactly uniform and palette remains≤16colours.
- Corrected targeted pixel/multitoys run:5passed,10deselected,1existing fixture warning,27.37s. DPR1/1.25/2 actual screenshots pass pixel-block equality. Multi toys all3characters×360/1440, game/profile,4toys,2toys refresh/relogin and clearing passed. Final captures `*-game-{360,1440}.png`, `*-profile-{360,1440}.png`, `full-game-{360,1440}.png`, `physical-pixels-dpr*.png`.
- Initial8successful targeted browser cases also covered all3character idle/jump/joy, profile static, pause/calm/reduced-motion, manifest12frameURLs200, and JSoff2checkboxPOST. A missing old temporary browser plugin caused one initial startup error; new external `/tmp/cat06_browser.py` points at installed Chromium1234 rather than absent Playwright1248. No project/dependency workaround.
- Separate core-game compatibility run was terminated with exit143 after3dots, without failure summary. Not claimed passed. Parent independent frozen suite owns final core-game acceptance.
- Ruff changed Python files passed; `makemigrations --check --dry-run --settings=config.settings.build` reports no changes; diffcheck passed. PostgreSQL17.11 is parent's disposablecat06-qa,55446; fixture creates/drops test databases. No real database used.

## Taste and visual review

Taste2.5.1 applied to the existing workspace, retaining approved navy/teal/beige UI, labeled native controls, mobile accessibility and motion controls. Parent reviewed initial enlarged art and later live3character crops; executor viewed all3previews/contact sheet, sleepy game360, scholar profile360, chaos game1440 and both whole-page360/1440 final captures. Root requested full-width mobile scenes rather than tiny32px cats in old120px columns, implemented accordingly.

An actual Taste shoot on `rendered-cat.html` (real Django template rendered with fictional context, review-only CSRF placeholder) is recorded in `taste-output.txt` / `taste-rendered-360.png`. Snapshot is visual evidence only, no livePOST proof. Full marketing gate deliberately not repeated per parent direction; no GATEPASS or site-wide marketing compliance claimed. Taste shoot exited0, saved360×2833/4screens; executor viewed the result: art, large toys, checkbox group and game layout render. Parent independent suite remains pending.

Code frozen after corrected targeted run; parent owns review/architecture/process docs and independent acceptance. No commit/push/deployment. Limits: Chromium local checks, not all browsers/real phones or public hosting. Original reference licensing is not independently asserted. HistoricalCAT04/CAT05 evidence not overwritten.
