"""CAT10 real travel, interaction and local owner-scoped scheduling."""

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


def setup(page, ui_site, random="0.1", legacy=False, disabled=False):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    keys = walk_keys(page)
    page.evaluate(
        """({keys,legacy,disabled}) => {
          localStorage.removeItem(keys.next);localStorage.removeItem(keys.enabled);
          localStorage.removeItem(keys.legacy);
          if(legacy) localStorage.setItem(keys.legacy,Date.now()+180000);
          if(disabled) localStorage.setItem(keys.enabled,'false');
          localStorage.setItem('qa-unrelated-preference','keep');
        }""",
        {"keys": keys, "legacy": legacy, "disabled": disabled},
    )
    page.add_init_script(f"Math.random=()=>{random};")
    page.clock.install()
    page.clock.pause_at(page.evaluate("new Date().toISOString()"))
    page.goto(url + "/")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
    return url


def walk_keys(page):
    owner = page.locator("#cat-walk-preference").evaluate("e=>JSON.parse(e.textContent).owner")
    prefix = f"persona.cat.walk.{owner}"
    return {"next": prefix + ".v2.next", "enabled": prefix + ".enabled", "legacy": prefix + ".next"}


def walk_deadline(page):
    return page.evaluate("key=>Number(localStorage.getItem(key))", walk_keys(page)["next"])


def advance_to_walk(page):
    delay = max(0, walk_deadline(page) - page.evaluate("Date.now()"))
    page.clock.fast_forward(int(delay) + 1)
    page.clock.run_for(100)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()


def capture(page, name):
    if (
        os.environ.get("UPDATE_CAT11_EVIDENCE") == "1"
        or os.environ.get("UPDATE_CAT10_EVIDENCE") == "1"
    ):
        root = Path(
            "docs/evidence/CAT11"
            if os.environ.get("UPDATE_CAT11_EVIDENCE") == "1"
            else "docs/evidence/CAT10"
        )
        root.mkdir(exist_ok=True)
        page.screenshot(path=str(root / f"{name}.png"), full_page=True)
        if name == "clicked-360" and os.environ.get("UPDATE_CAT11_EVIDENCE") != "1":
            html = re.sub(
                r'(name="csrfmiddlewaretoken" value=")[^"]+',
                r"\1snapshot-not-a-live-token",
                page.content(),
            )
            (root / "rendered-home.html").write_text(html)


@pytest.mark.browser
@pytest.mark.parametrize("width,random,kind", [(360, "0.1", "run"), (1440, "0.9", "hop")])
def test_real_walk_click_keyboard_and_cooldown(page, ui_site, width, random, kind):  # noqa: F811
    page.set_viewport_size({"width": width, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    url = setup(page, ui_site, random)
    root = page.locator("[data-cat-cameo]")
    expect(root).to_be_hidden()
    advance_to_walk(page)
    expect(root).to_be_visible()
    expect(root).to_have_attribute("data-walk", kind)
    pet = page.locator("[data-cameo-pet]")
    first = pet.bounding_box()
    page.clock.run_for(500)
    second = pet.bounding_box()
    assert abs(second["x"] - first["x"]) > 5
    assert second["x"] >= 0 and second["x"] + second["width"] <= width
    if width == 1440:
        sidebar = page.locator(".workspace-sidebar").bounding_box()
        assert second["x"] >= sidebar["x"] + sidebar["width"]
    if width == 360:
        nav = page.locator(".campus-nav").bounding_box()
        assert second["y"] + second["height"] < nav["y"]
    assert page.locator(".cat-cameo").evaluate("e=>getComputedStyle(e).pointerEvents") == "none"
    capture(page, f"{kind}-{width}")
    pet.focus()
    held = pet.bounding_box()
    page.clock.run_for(350)
    assert pet.bounding_box() == held
    page.keyboard.press("Enter")
    page.clock.run_for(30)
    expect(page.locator("[data-cameo-bubble]")).to_be_visible()
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-pose", "joy")
    menu = page.locator("[data-cameo-bubble]")
    question = menu.inner_text()
    deadline = walk_deadline(page)
    pet.click()
    expect(menu).to_be_hidden()
    expect(root).to_be_visible()
    expect(pet).to_have_attribute("aria-expanded", "false")
    expect(pet).to_be_focused()
    assert walk_deadline(page) == deadline
    page.keyboard.press("Enter")
    expect(menu).to_be_visible()
    expect(pet).to_have_attribute("aria-expanded", "true")
    assert menu.inner_text() == question
    bubble = page.locator("[data-cameo-bubble]").bounding_box()
    assert bubble["x"] >= 0 and bubble["y"] >= 0
    assert bubble["x"] + bubble["width"] <= width
    for control in page.locator("[data-cameo-bubble] a,[data-cameo-bubble] button").all():
        assert control.bounding_box()["height"] >= 44
    capture(page, f"clicked-{width}")
    page.keyboard.press("Escape")
    expect(root).to_be_hidden()
    assert page.locator("#main").evaluate("e=>e===document.activeElement")
    due = walk_deadline(page)
    assert 20000 <= due - page.evaluate("Date.now()") <= 40000
    page.goto(url + "/schedule/")
    assert walk_deadline(page) == due
    remaining = due - page.evaluate("Date.now()")
    page.clock.run_for(int(remaining) - 100)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.clock.run_for(200)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()
    assert errors == []


@pytest.mark.browser
def test_disable_reenable_and_suppression(page, ui_site):  # noqa: F811
    page.set_default_timeout(6000)
    url = setup(page, ui_site)
    advance_to_walk(page)
    pet = page.locator("[data-cameo-pet]")
    pet.focus()
    expect(pet).to_be_focused()
    page.keyboard.press("Space")
    page.clock.run_for(30)
    expect(page.locator("[data-cameo-bubble]")).to_be_visible()
    page.get_by_role("button", name="Отключить прогулки", exact=True).click()
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.goto(url + "/cat/")
    toggle = page.get_by_label("Разрешить коту гулять по кабинету", exact=True)
    expect(toggle).not_to_be_checked()
    assert page.locator("[data-cat-cameo]").count() == 0
    toggle.check()
    expect(toggle).to_be_checked()
    page.goto(url + "/requests/")
    page.clock.fast_forward(180000)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()
    page.emulate_media(reduced_motion="reduce")
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.emulate_media(reduced_motion="no-preference")
    page.evaluate("""() => {
      const field=document.createElement('input');field.id='qa-input';
      document.querySelector('main').append(field);field.focus();
    }""")
    page.clock.fast_forward(180000)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.locator("#qa-input").blur()
    page.clock.run_for(5200)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()
    page.evaluate("""() => {
      Object.defineProperty(document,'hidden',{configurable:true,value:true});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.evaluate("""() => {
      Object.defineProperty(document,'hidden',{configurable:true,value:false});
      document.dispatchEvent(new Event('visibilitychange'));
    }""")
    page.clock.fast_forward(180000)
    page.set_viewport_size({"width": 320, "height": 700})
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    page.evaluate("dispatchEvent(new PageTransitionEvent('pagehide')); ")
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.clock.fast_forward(200000)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    # The existing privacy guard reloads BFcache pages before restoring personal UI.
    with page.expect_navigation(wait_until="load"):
        page.evaluate("dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
    if not page.locator("[data-cat-cameo]").is_visible():
        delay = max(0, walk_deadline(page) - page.evaluate("Date.now()"))
        page.clock.fast_forward(int(delay) + 100)
        page.clock.run_for(30)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()


@pytest.mark.browser
def test_storage_failure_does_not_break_navigation(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    page.evaluate(
        "Object.keys(localStorage).filter(k=>k.startsWith('persona.cat.walk.')).forEach(k=>localStorage.removeItem(k));"
    )
    page.add_init_script("""Math.random=()=>.1;
      Storage.prototype.getItem=()=>{throw new Error('blocked')};
      Storage.prototype.setItem=()=>{throw new Error('blocked')};""")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.clock.install()
    page.goto(url + "/")
    page.clock.run_for(3400)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()
    page.locator("[data-cameo-pet]").focus()
    page.keyboard.press("Enter")
    page.get_by_role("link", name="К коту", exact=True).click()
    expect(page).to_have_url(url + "/cat/")
    expect(page.locator("[data-walk-preference-status]")).to_contain_text("недоступно")
    assert errors == []


@pytest.mark.browser
def test_cameo_fractional_dpr_pixels_and_resize(browser, ui_site):  # noqa: F811
    from tests.test_cat_pixels import screenshot_pixels

    context = browser.new_context(viewport={"width": 360, "height": 900}, device_scale_factor=1.25)
    page = context.new_page()
    try:
        setup(page, ui_site)
        advance_to_walk(page)
        page.locator("[data-cameo-pet]").focus()
        canvas = page.locator("[data-cat-renderer] canvas")
        box = canvas.bounding_box()
        dpr = 1.25
        width = round(box["width"] * dpr)
        assert width % 48 == 0
        assert abs(box["x"] * dpr - round(box["x"] * dpr)) < 0.001
        assert abs(box["y"] * dpr - round(box["y"] * dpr)) < 0.001
        mirrored = canvas.locator("..").evaluate("e=>getComputedStyle(e).transform !== 'none'")
        rgba = canvas.evaluate('e=>Array.from(e.getContext("2d").getImageData(0,0,48,48).data)')
        _, _, screen = screenshot_pixels(page.screenshot(scale="device"))
        left, top = round(box["x"] * dpr), round(box["y"] * dpr)
        scale = width // 48
        for y in range(48):
            for x in range(48):
                source_x = 47 - x if mirrored else x
                if rgba[(y * 48 + source_x) * 4 + 3] != 255:
                    continue
                colours = {
                    screen[top + yy][left + xx]
                    for yy in range(y * scale, (y + 1) * scale)
                    for xx in range(x * scale, (x + 1) * scale)
                }
                assert len(colours) == 1
        page.keyboard.press("Enter")
        page.clock.resume()
        page.evaluate("""() => {
          window.__qaResizeSeen=false;
          addEventListener('resize',()=>{window.__qaResizeSeen=true;},{once:true});
        }""")
        page.set_viewport_size({"width": 320, "height": 400})
        page.wait_for_function("window.__qaResizeSeen === true")
        bubble = page.locator("[data-cameo-bubble]").bounding_box()
        assert bubble["x"] >= 0 and bubble["y"] >= 0
        assert bubble["x"] + bubble["width"] <= 320
        pet = page.locator("[data-cameo-pet]").bounding_box()
        assert pet["y"] + pet["height"] < page.locator(".campus-nav").bounding_box()["y"]
        capture(page, "dpr1.25-low-320")
    finally:
        context.close()


@pytest.mark.browser
@pytest.mark.parametrize(
    "width,random,first_ms,repeat_ms", [(360, "0.1", 3300, 22000), (1440, "0.9", 5700, 38000)]
)
def test_new_cadence_ignores_old_deadline_and_keeps_natural_cooldown(
    page,
    ui_site,  # noqa: F811
    width,
    random,
    first_ms,
    repeat_ms,
):  # noqa: F811
    page.set_viewport_size({"width": width, "height": 900})
    url = setup(page, ui_site, random, legacy=True)
    keys = walk_keys(page)
    now = page.evaluate("Date.now()")
    first = walk_deadline(page)
    assert first - now == first_ms
    assert 3000 <= first - now <= 6000
    old = page.evaluate("key=>Number(localStorage.getItem(key))", keys["legacy"])
    assert old > first + 100000
    page.clock.run_for(first_ms - 100)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.clock.run_for(200)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()
    repeat = walk_deadline(page)
    assert abs((repeat - first) - repeat_ms) <= 1
    assert 20000 <= repeat - first <= 40000
    page.clock.run_for(9500)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    assert walk_deadline(page) == repeat
    page.goto(url + "/grades/")
    assert walk_deadline(page) == repeat
    advance_to_walk(page)
    assert page.evaluate("key=>Number(localStorage.getItem(key))", keys["legacy"]) == old
    assert page.evaluate("localStorage.getItem('qa-unrelated-preference')") == "keep"


@pytest.mark.browser
def test_old_optout_survives_cadence_version_change(page, ui_site):  # noqa: F811
    url = setup(page, ui_site, legacy=True, disabled=True)
    keys = walk_keys(page)
    page.clock.fast_forward(200000)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    assert page.evaluate("key=>localStorage.getItem(key)", keys["enabled"]) == "false"
    assert walk_deadline(page) == 0
    page.goto(url + "/cat/")
    toggle = page.get_by_label("Разрешить коту гулять по кабинету", exact=True)
    expect(toggle).not_to_be_checked()
    toggle.check()
    page.goto(url + "/notifications/")
    assert 3000 <= walk_deadline(page) - page.evaluate("Date.now()") <= 6000
    advance_to_walk(page)
    assert page.evaluate("localStorage.getItem('qa-unrelated-preference')") == "keep"


@pytest.mark.browser
@pytest.mark.parametrize("dismiss", ["close", "escape"])
def test_dismiss_long_open_bubble_starts_new_pause(page, ui_site, dismiss):  # noqa: F811
    setup(page, ui_site)
    advance_to_walk(page)
    page.locator("[data-cameo-pet]").focus()
    page.keyboard.press("Enter")
    old = walk_deadline(page)
    page.clock.fast_forward(50000)
    expect(page.locator("[data-cameo-bubble]")).to_be_visible()
    assert page.evaluate("Date.now()") > old
    if dismiss == "close":
        page.get_by_role("button", name="Скрыть кота", exact=True).click()
    else:
        page.keyboard.press("Escape")
    due = walk_deadline(page)
    assert 20000 <= due - page.evaluate("Date.now()") <= 40000
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.clock.run_for(int(due - page.evaluate("Date.now()")) - 100)
    expect(page.locator("[data-cat-cameo]")).to_be_hidden()
    page.clock.run_for(200)
    expect(page.locator("[data-cat-cameo]")).to_be_visible()


@pytest.mark.browser
@pytest.mark.parametrize("width", [320, 360, 600, 850, 1440])
def test_assistant_cameo_flows_after_composer_and_resizes(page, ui_site, width):  # noqa: F811
    page.set_viewport_size({"width": width, "height": 700})
    url = setup(page, ui_site)
    page.goto(url + "/assistant/")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
    before = page.evaluate("({y:scrollY,active:document.activeElement.tagName})")
    advance_to_walk(page)
    assert page.evaluate("({y:scrollY,active:document.activeElement.tagName})") == before
    root = page.locator("[data-cat-cameo]")
    pet = page.locator("[data-cameo-pet]")
    pet.focus()
    page.keyboard.press("Enter")
    bubble = page.locator("[data-cameo-bubble]")
    expect(bubble).to_be_visible()
    assert root.count() == page.locator("[data-cameo-rating]").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    if width <= 850:
        assert bubble.bounding_box()["y"] >= page.locator(".assistant-composer").evaluate(
            "e=>e.getBoundingClientRect().bottom"
        )
        for selector in [".assistant-composer textarea", "[data-send]"]:
            field = page.locator(selector)
            field.scroll_into_view_if_needed()
            assert field.evaluate("""e=>{const r=e.getBoundingClientRect();
                const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                return e===hit || e.contains(hit)}""")
        assert root.evaluate("e=>getComputedStyle(e).position") == "relative"
    else:
        assert root.evaluate("e=>getComputedStyle(e).position") == "fixed"
    for star in page.locator("[data-rating-value]").all():
        box = star.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44
    star = page.locator('[data-rating-value="5"]')
    star.focus()
    page.clock.resume()
    page.set_viewport_size({"width": 1440 if width <= 850 else 360, "height": 700})
    expect(star).to_be_focused()
    expect(bubble).to_be_visible()
    if width <= 850:
        for control in [star, page.locator("[data-cameo-close]")]:
            expect(control).to_be_in_viewport()
            assert control.evaluate("""e=>{const r=e.getBoundingClientRect();
                const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                return e===hit || e.contains(hit)}""")
    assert root.count() == 1
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    star.click()
    expect(page.locator("[data-rating-status]")).to_contain_text("Сохранено: 5 из 5")
    question = page.locator("[data-rating-question]").inner_text()
    pet.click()
    expect(bubble).to_be_hidden()
    expect(root).to_be_visible()
    expect(pet).to_have_attribute("aria-expanded", "false")
    expect(pet).to_be_focused()
    pet.click()
    expect(bubble).to_be_visible()
    expect(star).to_have_attribute("aria-pressed", "true")
    expect(page.locator("[data-rating-status]")).to_contain_text("Сохранено: 5 из 5")
    assert page.locator("[data-rating-question]").inner_text() == question
    page.keyboard.press("Escape")
    expect(root).to_be_hidden()
    expect(page.locator("#main")).to_be_focused()
    assert page.locator("[data-assistant-cameo-slot]").evaluate("e=>e.offsetHeight") == 0


@pytest.mark.browser
def test_assistant_inline_suppression_and_no_script(browser, page, ui_site):  # noqa: F811
    page.set_viewport_size({"width": 360, "height": 640})
    url = setup(page, ui_site)
    page.goto(url + "/assistant/")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
    advance_to_walk(page)
    root = page.locator("[data-cat-cameo]")
    field = page.get_by_label("Ваш вопрос", exact=True)
    field.fill("Черновик учебного вопроса")
    expect(root).to_be_hidden()
    page.clock.fast_forward(50000)
    expect(root).to_be_hidden()
    field.blur()
    page.clock.run_for(50)
    expect(root).to_be_visible()
    page.locator("[data-workspace-menu] summary").click()
    expect(root).to_be_hidden()
    page.keyboard.press("Escape")
    advance_to_walk(page)
    page.emulate_media(reduced_motion="reduce")
    expect(root).to_be_hidden()
    expect(field).to_have_value("Черновик учебного вопроса")
    context = browser.new_context(java_script_enabled=False, viewport={"width": 360, "height": 640})
    try:
        nojs = context.new_page()
        login(nojs, url, "student.one", ui_site[1])
        nojs.goto(url + "/assistant/")
        expect(nojs.locator("[data-cat-cameo]")).to_be_hidden()
        assert nojs.locator("[data-assistant-cameo-slot]").evaluate("e=>e.offsetHeight") == 0
        expect(nojs.get_by_label("Ваш вопрос", exact=True)).to_be_editable()
        assert nojs.evaluate("document.documentElement.scrollWidth<=innerWidth")
    finally:
        context.close()
