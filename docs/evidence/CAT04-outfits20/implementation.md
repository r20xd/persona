# CAT04 — implementation

**GATE: FAIL 31 (round 1 of 3), 35 WARN.** Actual Taste2.5.1 gate ran against `rendered-cat.html`, an HTML snapshot produced by the real Django template with fictional cat/context and a review-only CSRF placeholder. No source-template check, waiver, hidden finding or marketing PASS is claimed. The snapshot has no functioning authenticated server endpoints; browser tests separately check the working application. Full findings: `gate-output.txt`, `.taste-skill/gate.json`, `.taste-skill/gate/consistency/report.json` and checker screenshots. Following parent's scope decision, unchanged marketing findings were not rerun.

## Scope and implementation

Executor explicitly spawned as gpt-6.1-sol/low, one writer. Read project rules, TASK, architecture/plan, workflow/templates and CAT03 reports. Applied the newly available `taste-skill:design-taste-frontend`2.5.1 and its system/layout/section/copy/gate guidance within the existing authenticated workspace and approved navy/teal/beige palette. No new landing page, dependencies or migration.

- Server start response now20seconds, JS initial remaining20000ms, intro/idle clock20seconds. Minimum elapsed validation,7200s receipt validity, pause, calm/reduced-motion and idempotent rewards remain unchanged.
- Portrait declares `data-character`. Glasses use individual position/rotation: sleepy32%left/6%top/−13deg, scholar31/10.5/0deg, chaos32.5/4/−13deg. Scarf sits at the neck, with a scholar adjustment. Mug touches the right forepaw, with a scholar adjustment.
- Shared square canvas preserves proportional placement in desktop, mobile and compact profile. Decorative foreground duplicates of the original cat restore separate clipped left/right paws over scarf/gown, right paw over mug, and chin/head over gown. Separate polygons avoid a diagonal bridge between paws.
- Original gown PNG could not match both sleeve openings to the cat's forward paws while retaining proportions. Parent generated and supplied `static/images/cat-gown-fitted.png`; executor copied it without raster editing, inspected it, fitted87%width/10.5%left/−2%top (scholar−1.5%), and updated portrait/thumbnail references. Original assets preserved. Parent owns generation provenance.
- API helper verifies20seconds. Browser virtual clock freezes before start;25000ms paused consumes no time, active19900ms remains playable and20100ms expires. Clothing test covers all3characters×4accessories at both360/1440 and compact profiles; checks loading/decorative alt, selected art, square registration and no horizontal overflow. Asset selection test expects the new fitted gown.

## Verification and evidence

Initial sandbox environment had no PostgreSQL access and Docker shim was unavailable; first server attempt failed at fixture setup. Parent subsequently started isolated PostgreSQL17.11 `cat04-qa`,127.0.0.1:55444, userdeanery. No real/local application database used.

- Executor server suite:11passed3.40s on `TEST_DB_NAME=test_cat04_executor` before final visual asset reference update.
- Intermediate executor browser suite:8passed,1existing fixture warning,76.49s. Initial launch attempts failed because installed Playwright searched for absent Chromium1248; a temporary external plugin `/tmp/cat04_browser.py` supplied existing `/home/local-user/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`. No dependency changes.
- Parent independently reported final frozen `tests/test_cat.py tests/test_cat_browser.py tests/test_design_browser.py`:24passed,1existingwarning,100.89s. Parent owns independent review; this is explicitly attributed, not an executor-run claim.
- Final executor screenshot run: `PYTHONPATH=/tmp:. TEST_DB_PORT=55444 TEST_DB_USER=deanery TEST_DB_NAME=test_cat04_executor UPDATE_CAT04_EVIDENCE=1 .venv/bin/pytest -p cat04_browser tests/test_cat_browser.py -k generated_clothing -q --tb=short`:2passed,6deselected,1existingwarning,20.02s. Uses temporary databases created/dropped by fixture. `portrait-{character}-{accessory}-{width}.png` and `profile-{character}-{accessory}-{width}.png`:48 final screenshots; `clothing-{accessory}-{width}.png`:8 final whole-page views. All12combinations viewed in final Taste matrices, plus selected actual narrow/compact/full-page captures.
- Final Taste shoot matrices: `matrix-fitted-1440.png`, `matrix-fitted-360.png`. Earlier proposed/revision matrices retained as real iterations. `matrix.html` uses the actual portrait template/CSS. Game screenshots from intermediate successful gameplay suite show the20second running game; final changes only affect accessory rendering.
- Ruff relevant Python files and `git diff --check` passed. No tests claim internet deployment or Russia accessibility.

## Open Taste findings and risk assessment

All31 findings remain visible in the full log; no waivers were added. Categories:

- `hero-fill`, `hero-screen`, `section-height`, `section-air`, `one-section`, `one-heading`, `moment-none`, `cta`, `container`, `container-edges`, `card-layout`: marketing page structure/dealt-moment rules conflict with the approved compact workspace/sidebar/game/wardrobe layout. Outside this narrowly authorized fitting task.
- `spill`: checker treats the gown image rectangle as the containing panel of subsequent foreground images. The actual containing coordinate canvas is `.cat-art`; clipped foreground paws/head deliberately layer above the garment. Final matrices and actual portrait/profile captures show no visible overflow or clipping defect. Transparent image margins may extend outside their visible content; parent portrait clips at its square frame.
- `empty-visual`: scarf/glasses thumbnails flagged at390. Actual final full-page360 screenshots show both loaded, visible thumbnails; all4assets are also required loaded/visible by passing browser tests. The gate's static snapshot/fixed-mobile-nav view can cover a sampled region. No broken-image or empty-frame issue observed.
- `nav`: two-line brand text flagged as wrapped nav. This is the existing deliberate logo/subtitle composition. No navigation touch obstruction introduced by this change.
- `no-visual`: idle game panel is functional UI with its backpack symbol, rather than marketing key art. The running game contains12cards and is tested independently.
- `focus-ring`: existing `main:focus` removes outline for the programmatically focused main landmark. Existing interactive keyboard focus is unchanged; keyboard collection tests pass. No global workspace focus redesign made under CAT04.
-35WARN retained, including `flush`, `copy-headline`, `heading-scale`, `section-gaps`, `visual-caption`; details/screenshots in gate artifacts. No new touch-target, image-load or physical overlap regression found in final browser tests/review. This is not a declaration that all broader site accessibility issues are resolved.

Code/visual frozen for independent review. No commit/push/deployment performed. Pre-existing untracked `colors.jpg` untouched. Root owns final acceptance, process documents and versioning authorization.
