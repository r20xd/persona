# CAT03 implementation — executor

User asks faster swaps, more cards and matching generated clothing. Read project instructions/TASK/architecture27/plan16 and current Taste Skill2.5.1. Retained approved navy/teal/sky/beige workspace, native labeled controls and game layout (architecture20); this is an authenticated game, not a marketing landing page.

## Implemented code

- Twelve unique server-authoritative item IDs. Added headphones, classroom key, thermos, alarm clock and yarn with purpose-drawn local SVG symbols; no new external icons/library. Server samples the larger catalog using unchanged attempt/reward ownership, timing and CSRF rules.
- Active cards swap slots every1000ms with180ms transition; pointer grace500ms and focus grace300ms. Existing focused-card pinning, pointer capture, generation guards, pause/visibility/calm/reduced-motion semantics remain.
- Four columns by three rows desktop and three columns by four rows mobile. Uniform row heights keep keyboard focus from moving due to neighbours' different labels. Native targets remain larger than44px.
- Replaced flat SVG clothing with generated transparent PNG image overlays; textual labels preserved and decorative clothing alt empty. Thumbnails use the same generated assets. Existing outfit-scarf/glasses/gown/mug selectors remain.
- Introduced square .cat-art coordinate canvas inside portrait: the base and accessory stay registered in mobile/profile letterboxed portrait frames. Parent owns generating/optimizing4assets and their evidence; executor owns template/CSS fit. No dependency/model/migration changes.

## Verification

- ruff relevant Python files passed; git diff --check clean.
- Server suite:11passed3.30sec against isolated PostgreSQL55439 / test_cat03_executor. Includes twelve unique items, all four selectable wardrobe assets, four sequential rewards, isolation, CSRF, invalid payloads and repeated-game receipts.
- Full narrow suite completed19passed,1existing pytest fixture warning,71.09sec. Tests assert12cards, desktop/mobile column counts and44px targets; actual rectangle change before1.5seconds, focused-card stability, pause/calm/reduced-motion stability, three consecutive rounds/reload, timeout/retry. Clothing tests verify thumbnails load, selected overlay fits canvas, and selection is also visible in own profile.
- After that run, expanded the clothing browser test to all3characters×4accessories at1440 and sleepy×4at360; targeted2tests passed17.23sec, one existing fixture warning. Saved portrait-only screenshots for16combinations and full game/clothing/profile screenshots. Viewed scholar glasses/gown and chaos scarf/mug portraits, plus full sleepy gown: clothing matches shiny source style, leaves faces readable, and stays within the canvas. Parent independently reviewed initial sleepy scarf/glasses/gown fit as good.
- Used parent-provided alpha opaque bounding boxes to fit transparent full canvases without cropping or stretching: scarf60% width/24%left/28%top; glasses45/29/11; gown70/20/30; mug33/55/52. Height auto preserves native PNG aspect ratio, including non-square gown. No CSS changes after successful runs.

No raw Django source was fed to a visual checker; no Taste gate PASS claimed. No commits/push/deployment or user database mutations performed by executor. Art generation process belongs to parent's imagegen report.
