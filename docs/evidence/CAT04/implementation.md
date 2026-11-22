# CAT04 implementation — executor

Read project instructions, TASK/architecture27/plan16 and Taste Skill2.5.1 references. User explicitly replaces prior generated 3D cats with exact provided pixel sheets, animation only in game, clothes removed and toys alongside. Existing workspace palette, keyboard controls,12items/1sec shuffle and45sec round remain.

## Exact source art and animation

Inspected both supplied1536×1024PNG files and copied byte-for-byte into static/images/pixel-chaos-sheet.png and pixel-duo-sheet.png. No redraw, imagegen edit, recoloring or destructive crop. Inline SVG viewBox clips the source image at runtime, excluding labels, borders and palette panels. Four idle, jump and joy frames: chaos x220/400/580/760 with idle y470/h142, jump y636/h155, joy y824/h142, width180; sleepy x170/306/440/580 and scholar x940/1074/1208/1344 with idle y380/h104, jump y498/h118, joy y630/h112, width130. Explicit SVG clipPath rect matches the current viewBox. This matters: viewBox alone leaves letterbox padding where adjacent sheet pixels can paint. xMidYMax keeps the floor baseline, clip rect excludes source dividers/labels even in letterboxing, and runtime lighten blending suppresses dark sheet background against approved navy stage. Shared sprite viewport stays stable; source pixels render with image-rendering:pixelated.

Only /cat/ includes data-cat-animated and the game JS. Profile SVG contains only first idle frame and no animated marker. Active game cycles at160ms/frame, correct item triggers jump, completing3triggers a brief joy response. Pause, hidden tab, calm mode and prefers-reduced-motion paint stable idle; idle only runs during an active round. Existing generation/timer cleanup remains; profile has no cat animation script or CSS loop.

## Toys and data

Runtime clothing templates/labels/references replaced by toy-yarn/ball/mouse/fish PNG paths and textual labels Клубок/Мячик/Игрушечная мышка/Игрушечная рыбка. Parent owns four new transparent pixel toy assets. Toy is in a separate floor slot right of the cat; decorative image alt empty; no toy overlays the cat body. Thumbnails use same local assets.

Internal accessory field retained. Migration0005 removes old check constraint before mapping scarf→yarn, glasses→ball, gown→mouse, mug→fish, then adds allowed none/yarn/ball/mouse/fish constraint. Reverse removes new constraint, reverses mapping, restores old constraint. Name, character, completed count and completion receipt untouched. No new dependency or field.

## Verification

Server tests12passed5.52sec isolated PostgreSQL55439/test_cat04_executor. Added historical-model migration forward/reverse preservation test across all four old selections and progress/receipt fields. Other ownership, token replay, CSRF and sequential rewards retained. Browser tests adapted for SVG/toys and new3character checks verify static own profile, active frame change, jump/joy, pause/calm/reduced-motion. Toy tests verify all selections, generated images, profile persistence and non-overlap with cat sprite box. Initial full suite23passed111.10sec with one existing fixture warning; visual review then found source divider lines despite functional tests passing. Tightened crops and added explicit clipPath (viewBox alone was insufficient), increased toy slot to36% alongside62%cat slot without overlap. Post-fix targeted5browser tests passed39.17sec, one existing fixture warning. Viewed border-free scholar/fish, chaos/yarn1440 and sleepy/mouse360 portraits: no labels/borders, toys distinct and beside body. Added clip/window geometry sync assertions at profile/idle/jump/joy and optional close-up state screenshots for parent independent final run. Refactored static initial viewBox to derive from same server frame tuple. Full page game/profile images from initial run require parent refresh; final portrait-*.png files are post-fix.

No raw Django template checker run and no Taste gate PASS asserted. No deployment, user database mutation, commit or push by executor.
