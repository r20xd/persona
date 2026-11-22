"""Real CAT01 game: keyboard, pause, wish change, persisted outfit and narrow layout."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


def screenshot(page, name):
    if (
        os.environ.get("UPDATE_CAT06_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT01_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT02_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT03_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT04_EVIDENCE") == "1"
    ):
        root = Path(
            "docs/evidence/CAT09"
            if os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
            else "docs/evidence/CAT07"
            if os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
            else "docs/evidence/CAT06"
            if os.environ.get("UPDATE_CAT06_EVIDENCE") == "1"
            else "docs/evidence/CAT04"
            if os.environ.get("UPDATE_CAT04_EVIDENCE") == "1"
            else "docs/evidence/CAT03"
            if os.environ.get("UPDATE_CAT03_EVIDENCE") == "1"
            else "docs/evidence/CAT02"
            if os.environ.get("UPDATE_CAT02_EVIDENCE") == "1"
            else "docs/evidence/CAT01"
        )
        root.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(root / name), full_page=True, animations="disabled")


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_cat_full_game(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_default_timeout(6000)
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    if width <= 850:
        page.locator("[data-workspace-menu] summary").click()
    page.get_by_role("link", name="Кот в рюкзаке", exact=True).filter(visible=True).click()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    expect(page.locator("[data-clock]")).to_have_text("20")
    expect(page.locator(".cat-portrait .cat-base")).to_be_visible()
    expect(page.locator(".cat-base")).to_have_attribute("data-render-ready", "true")
    assert page.locator(".cat-canvas").evaluate("e => e.width === 48 && e.height === 48")
    page.get_by_label("Имя кота", exact=True).fill("Кот Бублик")
    page.get_by_label("Характер", exact=True).select_option("scholar")
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    screenshot(page, f"cat-{width}.png")
    page.emulate_media(reduced_motion="reduce")
    page.reload()
    expect(page.get_by_label("Спокойный режим", exact=False)).to_be_checked()
    with page.expect_response("**/cat/start/") as response:
        page.get_by_role("button", name="Начать сборы", exact=True).click()
    attempt = response.value.json()
    assert page.locator("[data-item]").count() == 12
    columns = page.locator("[data-targets]").evaluate(
        "e => getComputedStyle(e).gridTemplateColumns.split(' ').length"
    )
    assert columns == (3 if width == 360 else 4)
    for target in page.locator("[data-item]").all():
        assert target.evaluate("e => getComputedStyle(e).animationName") == "none"
        box = target.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44
    page.get_by_role("button", name="Поставить на паузу", exact=True).click()
    paused = page.locator("[data-clock]").inner_text()
    page.wait_for_timeout(1100)
    expect(page.locator("[data-clock]")).to_have_text(paused)
    expect(page.locator("[data-pause-cover]")).to_be_visible()
    page.get_by_role("button", name="Продолжить сборы", exact=True).click()
    first = attempt["initial"][0]
    first_target = page.locator(f'[data-item="{first}"]')
    first_target.focus()
    page.keyboard.press("Enter")
    expect(page.locator("#cat-speech")).to_contain_text("Я передумал")
    screenshot(page, f"game-{width}.png")
    # The first uncollected wish is replaced once; the third wish remains.
    for item in (attempt["initial"][2], attempt["replacement"]):
        target = page.locator(f'[data-item="{item}"]')
        target.focus()
        page.keyboard.press("Space")
    expect(page.locator("[data-game-status]")).to_contain_text("Открыто: Клубок", timeout=10000)
    page.get_by_role("link", name="Выбрать игрушку", exact=True).click()
    page.get_by_role("checkbox", name="Клубок", exact=True).check()
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    expect(page.locator(".toy-yarn")).to_be_visible()
    page.goto(url + "/profile/")
    expect(page.locator(".cat-profile")).to_contain_text("Кот Бублик")
    expect(page.locator(".cat-profile")).to_contain_text("Теория мурчания")
    expect(page.locator(".cat-profile .toy-yarn")).to_be_visible()
    screenshot(page, f"profile-{width}.png")
    page.reload()
    expect(page.locator(".cat-profile .toy-yarn")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.two", password)
    page.goto(url + "/profile/")
    expect(page.locator(".cat-profile")).not_to_contain_text("Кот Бублик")


@pytest.mark.browser
def test_timeout_visibility_and_save_retry(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    page.set_default_timeout(6000)
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    page.clock.install()
    page.clock.pause_at(page.evaluate("Date.now()"))
    with page.expect_response("**/cat/start/") as response:
        page.get_by_role("button", name="Начать сборы", exact=True).click()
    requested = response.value.json()["initial"]
    wrong = next(
        item
        for item in ("notebook", "fish", "calculator", "slipper", "pen")
        if item not in requested
    )
    moving = page.locator(f'[data-item="{wrong}"]')
    box = moving.bounding_box()
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(page.locator("#cat-speech")).to_contain_text("попросил другую")
    page.get_by_label("Спокойный режим", exact=False).check()
    expect(page.locator("[data-pause]")).to_be_visible()
    page.evaluate("""() => {
      Object.defineProperty(document, 'hidden', {configurable:true, value:true});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    expect(page.locator("[data-pause-cover]")).to_be_visible()
    page.clock.fast_forward(25000)
    expect(page.locator("[data-clock]")).to_have_text("20")
    page.evaluate("Object.defineProperty(document, 'hidden', {configurable:true, value:false})")
    page.get_by_role("button", name="Продолжить сборы", exact=True).click()
    page.clock.fast_forward(19900)
    expect(page.locator("[data-clock]")).to_have_text("1")
    expect(page.locator("[data-pause]")).to_be_visible()
    expect(page.locator("[data-game-status]")).not_to_contain_text("Время вышло")
    page.clock.fast_forward(200)
    expect(page.locator("[data-clock]")).to_have_text("0")
    expect(page.locator("[data-game-status]")).to_contain_text("Время вышло")
    # New round with a transient lost response; saved state must not double reward on retry.
    with page.expect_response("**/cat/start/") as response:
        page.get_by_role("button", name="Начать новые сборы", exact=True).click()
    attempt = response.value.json()
    page.route("**/cat/finish/", lambda route: route.abort(), times=1)
    for item in (attempt["initial"][0], attempt["initial"][2], attempt["replacement"]):
        page.locator(f'[data-item="{item}"]').click()
    # Browser virtual time does not change the server's minimum issued duration.
    import time

    time.sleep(2.1)
    page.clock.fast_forward(2200)
    expect(page.locator("[data-retry]")).to_be_visible()
    page.locator("[data-retry]").click()
    expect(page.locator("[data-game-status]")).to_contain_text("Открыто: Клубок")


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_consecutive_rounds_without_reload(page, ui_site, width):  # noqa: F811
    url, password, _, _ = ui_site
    errors, failures = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("requestfailed", lambda request: failures.append(request.url))
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    page.get_by_label("Спокойный режим", exact=False).check()
    for number in (1, 2, 3):
        with page.expect_response("**/cat/start/") as response:
            page.locator("[data-start]").click()
        assert response.value.status == 200
        attempt = response.value.json()
        for item in (attempt["initial"][0], attempt["initial"][2], attempt["replacement"]):
            page.locator(f'[data-item="{item}"]').focus()
            page.keyboard.press("Enter")
        with page.expect_response("**/cat/finish/") as response:
            expect(page.locator("[data-game-status]")).to_contain_text("Застёгиваем")
        assert response.value.status == 200
        assert response.value.json()["completed"] == number
        if number == 2:
            screenshot(page, f"second-win-{width}.png")
        expect(page.locator("[data-start]")).to_be_enabled()
        if number == 2:
            page.locator("[data-reward-link]").click()
            page.get_by_label("Спокойный режим", exact=False).check()
    assert errors == [] and failures == []


@pytest.mark.browser
def test_shuffle_pause_focus_and_calm(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    page.locator("[data-start]").click()

    def positions():
        return page.locator("[data-item]").evaluate_all(
            "buttons => buttons.map(button => {const r = button.getBoundingClientRect(); "
            "return [r.x, r.y];})"
        )

    original = positions()
    page.wait_for_timeout(1250)
    assert positions() != original
    # A focused keyboard target retains its visual slot while its neighbours move.
    target = page.locator("[data-item]").first
    target.focus()
    position = target.bounding_box()
    others = positions()
    page.wait_for_timeout(1250)
    assert positions() != others
    assert target.bounding_box() == position
    expect(target).to_be_focused()
    page.locator("[data-pause]").click()
    paused = positions()
    page.wait_for_timeout(1250)
    assert positions() == paused
    page.locator("[data-pause]").click()
    page.get_by_label("Спокойный режим", exact=False).check()
    calm = positions()
    page.wait_for_timeout(1250)
    assert positions() == calm
    page.get_by_label("Спокойный режим", exact=False).uncheck()
    page.emulate_media(reduced_motion="reduce")
    reduced = positions()
    page.wait_for_timeout(1250)
    assert positions() == reduced


def cat_capture(page, character, route, width, suffix=""):
    if (
        os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT06_EVIDENCE") == "1"
    ):
        page.locator(".cat-portrait").screenshot(
            path=str(
                Path(
                    "docs/evidence/CAT09"
                    if os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
                    else "docs/evidence/CAT07"
                    if os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
                    else "docs/evidence/CAT06"
                )
                / f"{character}-{route}-{width}{suffix}.png"
            )
        )


@pytest.mark.browser
@pytest.mark.parametrize("width", [360, 1440])
def test_multiple_toys_persist_and_fit_all_characters(page, ui_site, width):  # noqa: F811
    import psycopg

    url, password, db_name, db = ui_site
    page.set_viewport_size({"width": width, "height": 1000})
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    with psycopg.connect(dbname=db_name, **db) as connection:
        connection.execute("UPDATE accounts_studentcat SET completed=4")
    page.reload()
    for thumb in page.locator(".cat-unlock-icon img").all():
        thumb.scroll_into_view_if_needed()
        assert thumb.evaluate("e => e.complete && e.naturalWidth===32 && e.width>=64")
    for character in ("sleepy", "scholar", "chaos"):
        page.get_by_label("Характер", exact=True).select_option(character)
        for checkbox in page.locator('[name="toys"]').all():
            checkbox.check()
        page.get_by_role("button", name="Сохранить кота", exact=True).click()
        page.reload()
        for path, route in (("/cat/", "game"), ("/profile/", "profile")):
            page.goto(url + path)
            expect(page.locator(".cat-portrait")).to_have_attribute("data-character", character)
            expect(page.locator(".cat-base")).to_have_attribute("data-render-ready", "true")
            assert page.locator(".cat-toy").count() == 4
            for toy in page.locator(".cat-toy").all():
                assert toy.evaluate("e => e.complete && e.naturalWidth===32")
                assert toy.get_attribute("alt") == ""
                assert toy.bounding_box()["width"] >= 64
            # Transparent image boxes may intersect; actual occupied logical pixels must not.
            assert page.locator(".pixel-scene").evaluate("""scene => {
              const occupied=new Set(), origin=scene.getBoundingClientRect();
              const unit=parseFloat(getComputedStyle(scene).getPropertyValue('--pixel'));
              const images=scene.querySelectorAll('.cat-canvas:not([hidden]),.cat-toy');
              return [...images].every(image => {
                const canvas=document.createElement('canvas');
                canvas.width=image instanceof HTMLCanvasElement ? image.width : image.naturalWidth;
                canvas.height=image instanceof HTMLCanvasElement
                  ? image.height : image.naturalHeight;
                const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
                const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
                const box=image.getBoundingClientRect();
                const ox=Math.round((box.left-origin.left)/unit);
                const oy=Math.round((box.top-origin.top)/unit);
                for(let y=0;y<canvas.height;y++) for(let x=0;x<canvas.width;x++) {
                  if(!data[(y*canvas.width+x)*4+3]) continue;
                  const key=`${x+ox},${y+oy}`;
                  if(occupied.has(key)) return false;
                  occupied.add(key);
                }
                return true;
              });
            }""")
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            cat_capture(page, character, route, width)
            if character == "sleepy" and route == "game":
                screenshot(page, f"full-game-{width}.png")
        page.goto(url + "/cat/")
    page.get_by_role("checkbox", name="Мячик", exact=True).uncheck()
    page.get_by_role("checkbox", name="Игрушечная мышка", exact=True).uncheck()
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    page.get_by_role("button", name="Выйти", exact=True).click()
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    expect(page.locator(".cat-portrait")).to_have_attribute("data-toys", "yarn,fish")
    for checkbox in page.locator('[name="toys"]').all():
        checkbox.uncheck()
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    assert page.locator(".cat-toy").count() == 0
    screenshot(page, f"cleared-{width}.png")


@pytest.mark.browser
@pytest.mark.parametrize("character", ["sleepy", "scholar", "chaos"])
def test_pixel_animation_game_only_and_reactions(page, ui_site, character):  # noqa: F811
    def signature(sprite):
        return sprite.locator("canvas").evaluate("e => e.toDataURL()")

    url, password, _, _ = ui_site
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    login(page, url, "student.one", password)
    page.goto(url + "/cat/")
    page.get_by_label("Характер", exact=True).select_option(character)
    page.get_by_role("button", name="Сохранить кота", exact=True).click()
    assert page.locator('script[src*="cat."]').count() == 1
    page.goto(url + "/profile/")
    sprite = page.locator(".cat-sprite")
    assert sprite.get_attribute("data-cat-animated") is None
    expect(sprite).to_have_attribute("data-render-ready", "true")
    initial = signature(sprite)
    page.wait_for_timeout(400)
    assert signature(sprite) == initial
    page.goto(url + "/cat/")
    sprite = page.locator(".cat-sprite")
    with page.expect_response("**/cat/start/") as response:
        page.locator("[data-start]").click()
    attempt = response.value.json()
    page.wait_for_function(
        "expected => document.querySelector('.cat-canvas').toDataURL() !== expected",
        arg=initial,
        timeout=1500,
    )
    assert signature(sprite) != initial
    assert sprite.locator("canvas").evaluate("e => e.width===48 && e.height===48")
    # URLs come from the actual WhiteNoise manifest, including all animation frames.
    frames = page.locator("#cat-sprite-frames").text_content()
    import json

    assert {pose: len(values) for pose, values in json.loads(frames).items()} == {
        "idle": 6,
        "blink": 6,
        "jump": 8,
        "joy": 8,
        "stretch": 8,
        "yawn": 8,
        "surprise": 6,
    }
    page.locator(f'[data-item="{attempt["initial"][0]}"]').focus()
    page.keyboard.press("Enter")
    expect(sprite).to_have_attribute("data-pose", "jump")
    cat_capture(page, character, "jump", page.viewport_size["width"])
    page.locator("[data-pause]").click()
    frozen = sprite.locator("canvas").evaluate("e => e.toDataURL()")
    page.wait_for_timeout(400)
    assert sprite.locator("canvas").evaluate("e => e.toDataURL()") == frozen
    page.locator("[data-pause]").click()
    for mode in ("calm", "reduced"):
        if mode == "calm":
            page.get_by_label("Спокойный режим", exact=False).check()
        else:
            page.get_by_label("Спокойный режим", exact=False).uncheck()
            page.emulate_media(reduced_motion="reduce")
        frozen = sprite.locator("canvas").evaluate("e => e.toDataURL()")
        page.wait_for_timeout(400)
        assert sprite.locator("canvas").evaluate("e => e.toDataURL()") == frozen
    page.emulate_media(reduced_motion="no-preference")
    for item in (attempt["initial"][2], attempt["replacement"]):
        page.locator(f'[data-item="{item}"]').focus()
        page.keyboard.press("Enter")
    expect(sprite).to_have_attribute("data-pose", "joy")
    cat_capture(page, character, "joy", page.viewport_size["width"])
    assert errors == []


@pytest.mark.browser
@pytest.mark.parametrize("dpr", [1, 1.25, 2])
def test_rendered_native_pixels_are_uniform_device_blocks(browser, ui_site, dpr):  # noqa: F811
    from tests.test_cat_pixels import screenshot_pixels

    url, password, _, _ = ui_site
    context = browser.new_context(viewport={"width": 360, "height": 1000}, device_scale_factor=dpr)
    page = context.new_page()
    try:
        login(page, url, "student.one", password)
        page.goto(url + "/cat/")
        sprite = page.locator(".cat-sprite")
        expect(sprite).to_be_visible()
        expect(sprite).to_have_attribute("data-render-ready", "true")
        marks = page.locator(".cat-portrait .companion-marks")
        expect(marks).to_be_visible()
        # Locator screenshot rounds its CSS clip outwards at fractional DPR (193px for192).
        # Decode the whole physical screenshot and sample the measured device-aligned box.
        box = sprite.bounding_box()
        # Decorations behind transparent sprite pixels are not native sprite colours.
        # Hide only that layer during capture; ordinary rendering keeps it visible.
        data = page.screenshot(
            scale="device", style=".cat-portrait .companion-marks { visibility: hidden; }"
        )
        expect(marks).to_be_visible()
        _, _, screen = screenshot_pixels(data)
        left, top = round(box["x"] * dpr), round(box["y"] * dpr)
        w, h = round(box["width"] * dpr), round(box["height"] * dpr)
        pixels = [row[left : left + w] for row in screen[top : top + h]]
        assert w == h and w % 48 == 0
        scale = w // 48
        assert scale >= 1
        # Actual screenshot pixels, not a second copy of the sizing formula.
        for y in range(48):
            for x in range(48):
                colours = {
                    pixels[yy][xx]
                    for yy in range(y * scale, (y + 1) * scale)
                    for xx in range(x * scale, (x + 1) * scale)
                }
                assert len(colours) == 1, (dpr, x, y, colours)
        assert len({pixel for row in pixels for pixel in row}) <= 16
        if (
            os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
            or os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
            or os.environ.get("UPDATE_CAT06_EVIDENCE") == "1"
        ):
            root = Path(
                "docs/evidence/CAT09"
                if os.environ.get("UPDATE_CAT09_EVIDENCE") == "1"
                else "docs/evidence/CAT07"
                if os.environ.get("UPDATE_CAT07_EVIDENCE") == "1"
                else "docs/evidence/CAT06"
            )
            (root / f"physical-pixels-dpr{dpr}.png").write_bytes(data)
    finally:
        context.close()


@pytest.mark.browser
def test_multi_toy_form_without_javascript(browser, ui_site):  # noqa: F811
    import psycopg

    url, password, db_name, db = ui_site
    context = browser.new_context(
        java_script_enabled=False, viewport={"width": 360, "height": 1000}
    )
    page = context.new_page()
    try:
        login(page, url, "student.one", password)
        page.goto(url + "/cat/")
        page.get_by_role("button", name="Сохранить кота", exact=True).click()
        with psycopg.connect(dbname=db_name, **db) as connection:
            connection.execute("UPDATE accounts_studentcat SET completed=4")
        page.reload()
        page.get_by_role("checkbox", name="Клубок", exact=True).check()
        page.get_by_role("checkbox", name="Игрушечная рыбка", exact=True).check()
        page.get_by_role("button", name="Сохранить кота", exact=True).click()
        page.reload()
        expect(page.get_by_role("checkbox", name="Клубок", exact=True)).to_be_checked()
        expect(page.get_by_role("checkbox", name="Игрушечная рыбка", exact=True)).to_be_checked()
        assert page.locator(".cat-toy").count() == 2
    finally:
        context.close()


@pytest.mark.browser
def test_ambient_poses_and_wrong_pick_reaction(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    page.clock.install()
    page.goto(url + "/cat/")
    page.clock.pause_at(page.evaluate("Date.now()"))
    sprite = page.locator(".cat-sprite")
    expect(sprite).to_have_attribute("data-render-ready", "true")
    before = sprite.locator("canvas").evaluate("e => e.toDataURL()")
    page.clock.fast_forward(3000)
    assert sprite.locator("canvas").evaluate("e => e.toDataURL()") == before
    with page.expect_response("**/cat/start/") as response:
        page.locator("[data-start]").click()
    attempt = response.value.json()
    page.clock.run_for(1900)
    expect(sprite).to_have_attribute("data-pose", "blink")
    page.clock.run_for(3000)
    expect(sprite).to_have_attribute("data-pose", "stretch")
    page.clock.run_for(3400)
    expect(sprite).to_have_attribute("data-pose", "yawn")
    wrong = next(
        item for item in ("notebook", "fish", "pen", "slipper") if item not in attempt["initial"]
    )
    page.locator(f'[data-item="{wrong}"]').focus()
    page.keyboard.press("Enter")
    expect(sprite).to_have_attribute("data-pose", "surprise")
    page.clock.run_for(240)
    expect(sprite).to_have_attribute("data-pose", "surprise")
    page.locator(f'[data-item="{attempt["initial"][0]}"]').focus()
    page.keyboard.press("Enter")
    expect(sprite).to_have_attribute("data-pose", "jump")
    page.clock.run_for(240)
    expect(sprite).to_have_attribute("data-pose", "jump")
    page.locator("[data-pause]").click()
    frozen = sprite.locator("canvas").evaluate("e => e.toDataURL()")
    page.clock.fast_forward(5000)
    assert sprite.locator("canvas").evaluate("e => e.toDataURL()") == frozen
    page.locator("[data-pause]").click()
    page.evaluate("""() => {
      Object.defineProperty(document,'hidden',{configurable:true,value:true});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    frozen = sprite.locator("canvas").evaluate("e => e.toDataURL()")
    page.clock.run_for(2000)
    assert sprite.locator("canvas").evaluate("e => e.toDataURL()") == frozen
