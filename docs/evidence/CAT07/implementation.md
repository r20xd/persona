# CAT07 — true48pixel cats,32pixel toys and expressive state animation

Read project instructions/TASK/architecture28 and CAT07note/PLAN plus Taste2.5.1 and core references. Code-native asset generation follows the user's exact-grid request; no imagegen or raster upscaling. Parent owns final independent acceptance and optional marketing-checker findings.

## Asset work

New standalone scripts/generate_cat_pixel48.py draws directly onto a48×48 index grid with integer primitives and polygon/raster contours; it does not read source rasters. It reuses only the existing standard-library indexed PNG encoder/palette from generate_cat_pixel32. Script-local import path allows execution from an empty temporary directory. Original32assets remain unchanged.

There are157new runtime PNGs under static/images/cat-pixel48:150animation frames,3static aliases and4toys. Seven variable-length states: idle6, blink6, jump8, joy8, stretch8, yawn8, surprise6. New head/ear/body geometry, larger glasses/eye highlights, blush/whiskers/nose/mouth, discrete lavender shadow clusters and pink toe pads use extra resolution. Tail articulation, crouch/air tuck/landing, raised paws, long stretch, closing eyelids and mouth-open yawn/surprise change silhouettes and expressions. Each non-idle sequence begins/ends at exact idle0 for coherent transitions. Character identities remain dozy closed eyes, scholar glasses and chaos grin.

Toys are freshly drawn32×32: yarn has winding threads and loose strand; ball stitched panels/highlights; mouse pink inner ear, stitched body and curled tail; fish fins/eye/scales. No16→32 scaling. All sprites share12palette entries, binary alpha and no intermediate colors. Viewed3idle previews plus pose-overview and toys-preview: distinct expressive states and readable toy details.

## Runtime

Server presentation includes7pose URL arrays with variable lengths plus per-pose timing. Runtime selects frames by elapsed pose time and actual array length. Ambient blink/stretch/yawn cycle only during an active round; input reactions replace ambient poses, while ambient cannot interrupt jump/surprise/joy. Wrong item triggers surprise, correct item jump, win joy; no autoplay before Start. Pause/hidden/calm/reduced reset to staticidle. Profile remains first idle frame with layout fitting only, no animation.

Logical scene104×104 keeps the48cat at28/28 (exact center). Four32toys occupy0/48,20/72,52/72,72/48. Their transparent image boxes may overlap, but unit checks prove occupied pixels never intersect each other or any frame of all3cats. Mobile portraits are square to retain3×physical scale/cat144px; desktop profile width208 retains2×/cat96px. Whole physical pixels and globally device-aligned scene origins preserved for DPR1/1.25/2; thumbnails fit native32pixels at integer device scale.

No changes to20second gameplay, sessions/tokens, rewards, ownership or toy persistence. No dependencies/models/migrations/AI chat or user environment edits.

## Verification and evidence

-4independent pixel tests passed1.36sec: decode157PNG bytes, exact48/32dimensions, palette/binary alpha, deterministic reproduction in empty tmp cwd, aliases, distinct poses/endpoints, uncropped bounds, non-resize comparison to historical32/16assets, and actual logical ink separation for every frame with all4toys.
- Ruff relevant code/tests and git diff --check passed. Source frozen before parent browser suite; executor deliberately did not repeat broad browser tests.
- Browser tests adapted to48/32dimensions and actual occupied-pixel collision checks. Existing game/repeat/persistence/pause/reduced and screenshot physical-block tests retained. Added one virtual-clock ambient/reaction test for blink/stretch/yawn, surprise, jump priority, pause and hidden. Clock installed before navigation and run_for fires every scheduled animation tick.
- Previews/contact-sheet/pose-overview/toys-preview are derived directly from generator grids, not separately approximated drawings.
- Sanitized actual Django render: docs/evidence/CAT07/rendered-cat.html and /tmp/cat07-snapshot/rendered-cat.html. Fictional cat/context, review-only CSRF placeholder, complete local assets including accounts JS. No live sessions, secrets or student data. Snapshot proves rendering only, not POST behavior.
- Actual Taste shoot360 exited0; taste-output.txt records command/result, taste-rendered-360.png saved360×2915. Executor viewed it: centered cat,4distinct toys, form and checkbox layout render without source labels or clipping. Temporary snapshot HTTP server8767 stopped after shoot. Root can run gate directly on temp snapshot file; executor did not run gate or claim GATEPASS. No kit files changed.

Parent owns independent live browser/server results, final review, commit and push. No commit/push/deployment by executor.
