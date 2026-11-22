"""CAT09: real canvas pixels from CAT08 artwork, not historical frame URL markers."""

import base64
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.test_requests_browser import login
from tests.ui_qa import ui_site  # noqa: F401


@pytest.mark.browser
def test_master_renderer_pose_pixels_and_contact(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    rows = []
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for character in ("sleepy", "scholar", "chaos"):
        page.goto(url + "/cat/")
        page.get_by_label("Характер", exact=True).select_option(character)
        page.get_by_role("button", name="Сохранить кота", exact=True).click()
        node = page.locator("[data-cat-renderer]")
        expect(node).to_have_attribute("data-render-ready", "true")
        assert f"cat-assistant-style48/{character}." in page.locator(".cat-fallback").get_attribute(
            "src"
        )
        rendered = page.evaluate("""() => {
          const node=document.querySelector('[data-cat-renderer]');
          const config=JSON.parse(document.getElementById('cat-renderer-config').textContent);
          return Object.entries(config.counts).flatMap(([pose,count]) => {
            return Array.from({length:count},(_,frame) => {
              window.PersonaCat.render(node,pose,frame,count);
              const canvas=node.querySelector('canvas');
              const pixels=Array.from(canvas.getContext('2d').getImageData(0,0,48,48).data);
              return {pose,frame,count,pixels,png:canvas.toDataURL()};
            });
          });
        }""")
        signatures = []
        for frame in rendered:
            pixels = frame["pixels"]
            assert set(pixels[3::4]) == {0, 255}
            colours = {tuple(pixels[index : index + 4]) for index in range(0, len(pixels), 4)}
            assert len(colours) <= 13
            alpha = pixels[3::4]
            assert not any(alpha[:48] + alpha[-48:])
            assert not any(alpha[y * 48] or alpha[y * 48 + 47] for y in range(48))
            remaining = {(x, y) for y in range(48) for x in range(48) if alpha[y * 48 + x]}
            components = []
            component_boxes = []
            while remaining:
                pending = [remaining.pop()]
                count = 0
                points = []
                while pending:
                    x, y = pending.pop()
                    count += 1
                    points.append((x, y))
                    neighbours = {
                        (x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    } & remaining
                    remaining -= neighbours
                    pending.extend(neighbours)
                components.append(count)
                component_boxes.append(
                    (
                        count,
                        min(x for x, y in points),
                        min(y for x, y in points),
                        max(x for x, y in points),
                        max(y for x, y in points),
                    )
                )
            assert len([count for count in components if count >= 8]) == 1, (
                character,
                frame["pose"],
                frame["frame"],
                component_boxes,
            )
            if frame["frame"] == frame["count"] // 2:
                signatures.append(bytes(pixels))
        assert len(set(signatures)) == 7
        rows.append([frame["png"] for frame in rendered if frame["frame"] == frame["count"] // 2])
    assert errors == []
    if os.environ.get("UPDATE_CAT09_EVIDENCE") == "1":
        data = page.evaluate(
            """async rows => {
          const canvas=document.createElement('canvas');canvas.width=7*48*5;canvas.height=3*48*5;
          const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
          for(let y=0;y<rows.length;y++)for(let x=0;x<rows[y].length;x++) {
            const image=new Image();image.src=rows[y][x];await image.decode();
            ctx.drawImage(image,x*240,y*240,240,240);
          }
          return canvas.toDataURL().split(',')[1];
        }""",
            rows,
        )
        root = Path("docs/evidence/CAT09")
        root.mkdir(parents=True, exist_ok=True)
        (root / "renderer-contact.png").write_bytes(base64.b64decode(data))


@pytest.mark.browser
def test_master_load_pending_and_failed_do_not_block_game(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    login(page, url, "student.one", password)
    pending = []
    page.route("**/cat-assistant-style48/*", lambda route: pending.append(route))
    page.goto(url + "/cat/", wait_until="domcontentloaded")
    expect(page.locator(".cat-fallback")).to_be_visible()
    with page.expect_response("**/cat/start/") as response:
        page.locator("[data-start]").click()
    assert response.value.status == 200
    for route in pending:
        route.continue_()
    page.unroute("**/cat-assistant-style48/*")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
    page.route("**/cat-assistant-style48/*", lambda route: route.abort())
    page.goto(url + "/cat/")
    expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "error")
    expect(page.locator(".cat-fallback")).to_be_visible()
    with page.expect_response("**/cat/start/") as response:
        page.locator("[data-start]").click()
    assert response.value.status == 200
    assert errors == []


@pytest.mark.browser
def test_native_assets_avoid_large_master_and_logo_downloads(page, ui_site):  # noqa: F811
    url, password, _, _ = ui_site
    login(page, url, "student.one", password)
    requested = []
    page.on("request", lambda request: requested.append(request.url))
    for path in ("/cat/", "/profile/"):
        page.goto(url + path)
        expect(page.locator("[data-cat-renderer]")).to_have_attribute("data-render-ready", "true")
        source = page.locator(".cat-fallback").get_attribute("src")
        assert "/cat-assistant-style48/" in source
        assert len(page.request.get(url + source).body()) < 2048
        logo = page.locator(".sidebar-brand img").get_attribute("src")
        assert "persona-mark-small." in logo
        assert len(page.request.get(url + logo).body()) < 16000
    assert not any(
        "/cat-assistant-style/" in request or "/persona-mark." in request for request in requested
    )
