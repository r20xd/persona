# CAT09 — CAT08 artwork in the live game renderer

Same assigned executor/model continued; no delegation/model substitution. Read project instructions/TASK/architecture31/PLAN and current Taste2.5.1/core references. Three immutable CAT08 PNG masters are the actual source; no new image generation, PNG editing, dependency/model/migration or AI-chat change.

## Rendering and behavior

New local cat-renderer.js loads the selected1254×1254master, finds opaque bounds, samples nearest pixels onto a padded48×48grid and maps them to12fixed brand/source colors (navy/teal/sky/cream with small pink/lilac accents), binary alpha. It does not load historical CAT07 cat frames. Source master stays visible as ordinary alt-bearing img until canvas is ready; no-JS/error retains that fallback. Canvas has48×48backing dimensions, roleimg/name. Async loading stores the latest desired pose and never blocks Start/repeat.

Rig divides actual quantized artwork into overlapping head/body/tail layers; head/body use separate integer transforms for breathing, crouch/air/landing and stretch. Tail tip bends by source scanlines while its base stays anchored, with source-pixel overlap at bend steps. Face masks change actual eye/mouth pixels for blink/yawn/surprise/joy; default identity comes from source. Fixed cream neck bridge removed after visual review because it obscured the collar. Surprise changed from block eyes to rounded3pixel pupils with white glint and small rounded mouth. Profile prepares only one idle canvas; renderer has no animation interval. Existing profile fitting returns before game timers.

Existing seven-state timing/priority engine remains. Presentation has one counts model, numerical frame IDs and renderer source/palette/rig configuration via json_script. Game paints through renderer rather than changing old PNG URLs.20seconds,12cards,4existing32pixel toys, requests/rewards/persistence/CSRF/ownership unchanged. Integer physical scaling/aligned origin retained, no canvas smoothing.

## Verification and corrections

- Initial diagnostic3characters×7middle poses passed and showed recognizable CAT08 identities. Parent reviewed contact and requested neck/surprise refinements; updated diagnostic passed6.52sec.
- Focused existing game reaction/static profile, actual DPR1 screenshot blocks, and pending/failed-image game path:3passed16.04sec,1existing fixture warning. Historical PNG preservation tests:4passed0.77sec. Historical tests explicitly describe CAT07; current rendering is proved by canvas data and screenshots.
- Expanded renderer test to every one of150pose frames: alpha0/255, <=13RGBAvalues, transparent boundaries,7distinct middle poses and8-connected-component check. It caught a9pixel detached curl piece in chaos joy and then a94pixel tail separation during jump. Fixed complete chaos-tail region and kept its horizontal body width during airborne phase (crouch still expands, vertical/body/head movement retained); no threshold weakening. Final all150-frame smoke passed6.89sec,1existing warning. At most tiny reference fragments under8pixels allowed; all major parts form one connected component in every frame.
- Replaced fixed220ms idle expectation with waiting for actual canvas pixel change within1500ms. Existing freeze/pause/calm/reduced/hidden checks now compare canvas data, not obsolete src markers. New pending load test starts a round before artwork resolves, then releases source; failed source also leaves gameplay usable with no pageerror.
- Both JS syntax checks, Ruff/format and git diff --check passed. Source frozen before parent broad suite. Parent independently completed the frozen full suite:36passed/1existing warning,120.13sec;17source/master hashes unchanged, Ruff/format/JSsyntax/Django checks passed. Parent noticed DPR evidence helper guard omitted UPDATE_CAT09_EVIDENCE while pixel tests themselves executed. After that frozen run, made the single authorized helper-only change:09/07/06guard and corresponding directory selection. Ruff/format/diff passed; parent runs only3DPRparams to refresh CAT09evidence. No runtime source changed after full acceptance checks.

## Visual evidence and limits

renderer-contact-before.png preserves initial diagnostic; renderer-contact.png is the corrected3×7matrix, rendered through actual browser canvas. Parent accepted visual direction and refinements before broad testing. No source PNG rewritten; only diagnostic canvas screenshots saved.

Sanitized actual Django snapshot: docs/evidence/CAT09/rendered-cat.html plus canonical /private/tmp/cat09-snapshot/rendered-cat.html with full local assets. Fictional cat and review-only CSRF placeholder, no live student/session data. Actual Taste shoot360 exited0 (taste-output.txt), saved360×2915; executor viewed the new source character centered with4toys/form. Snapshot is not proof of POST; live tests are separate. No raw template checker, no kit modification or GATEPASS claim by executor; parent owns final independent review/gate and versioning.

## Performance follow-up: native assets

Root's actual Taste perf first returned2FAIL/7WARN (large logo/master downloads); that result remains in taste-perf-before.txt. Follow-up exports the existing prepared grid, preserving artwork and every rig pose. New scripts/build_cat_art.py serves only copied masters/logo/renderer in a temporary localhost directory, uses existing Playwright, closes browser/server, and needs no database. It builds48×48PNG from renderer.grid/palette and96×96header/favicon logo. Original CAT08 masters and large login decoration remain unchanged.

Runtime config now uses images/cat-assistant-style48/{character}.png and native_grid=true. Native preparation validates48dimensions, binary alpha and exact palette then skips bounding-box crop, sampling and centering. The ordinary fallback img uses the same small source. Brand/favicon use persona-mark-small.png; login decorative artwork keeps its original. No game behavior or layout changes.

Reproduction: PLAYWRIGHT_BROWSERS_PATH=/tmp/persona-browsers UV_CACHE_DIR=/tmp/persona-uv-cache uv run python scripts/build_cat_art.py --check. Check compares decoded RGBA rather than PNG encoder bytes and compares SHA256 of all150 raw/native rendered frame RGBA buffers. All4assets and150frames matched. Logo downsampling uses Chromium canvas; use the project's installed Chromium for reproducible resize behavior. Builder test deliberately points TEST_DB_PORT at1, proving no PostgreSQL dependency.

| Asset | Original bytes | Shipped bytes | Saved bytes |
| --- | ---: | ---: | ---: |
| sleepy | 720444 | 1532 | 718912 |
| scholar | 812194 | 1280 | 810914 |
| chaos | 779392 | 1400 | 777992 |
| header/favicon logo | 956225 | 10385 | 945840 |

Focused smoke:3passed/1existingfixturewarning12.35sec (builder --check; all150frame pixel/component/contact checks; actual /cat/ and /profile/ network/size assertions rejecting heavy master/large-logo downloads). Ruff, JS syntax and diff checks passed. An earlier identical focused run completed with empty lastfailed cache but its terminal output was lost during context compaction; the recorded timed result is the observed repeat. Source frozen before parent independent broad/perf rerun. Updated canonical sanitized snapshot /private/tmp/cat09-snapshot/rendered-cat.html and durable rendered-cat.html use native assets and review-only CSRF placeholders. No user daemon, database, master PNG, dependency or schema modified.
