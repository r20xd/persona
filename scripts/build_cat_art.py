"""Export the CAT09 renderer's exact grid and a96px logo. No DB or extra packages.

Run: uv run python scripts/build_cat_art.py [--check] [--browser-channel chrome]
--check compares decoded RGBA pixels, and all150raw/native rendered frame hashes.
Only explicitly copied inputs are served from an owned temporary directory.
"""

import argparse
import base64
import json
import os
import shutil
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def configurations():
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
    import django

    django.setup()
    from apps.accounts.cat import cat_card

    return {
        character: cat_card(
            SimpleNamespace(character=character, name="Preview", toys=[], completed=0)
        )["renderer"]
        for character in ("sleepy", "scholar", "chaos")
    }


def html(config):
    data = json.dumps(config).replace("<", "\\u003c")
    return (
        '<!doctype html><meta charset="utf-8">'
        f'<script id="cat-renderer-config" type="application/json">{data}</script>'
        '<div data-cat-renderer><img alt="Preview"><canvas width="48" height="48" hidden>'
        '</canvas></div><script src="/cat-renderer.js"></script>'
    )


EXPORT = """() => {
  const node=document.querySelector('[data-cat-renderer]');
  const config=JSON.parse(document.getElementById('cat-renderer-config').textContent);
  const canvas=document.createElement('canvas');canvas.width=canvas.height=48;
  const ctx=canvas.getContext('2d'), image=ctx.createImageData(48,48);
  node._catRenderer.grid.forEach((index,pos) => {
    if(index) image.data.set([...config.palette[index],255],pos*4);
  });
  ctx.putImageData(image,0,0);
  return canvas.toDataURL().split(',')[1];
}"""

FRAME_HASHES = """async () => {
  const node=document.querySelector('[data-cat-renderer]');
  const config=JSON.parse(document.getElementById('cat-renderer-config').textContent);
  const hashes=[];
  for(const [pose,count] of Object.entries(config.counts)) for(let frame=0;frame<count;frame++) {
    window.PersonaCat.render(node,pose,frame,count);
    const data=node.querySelector('canvas').getContext('2d').getImageData(0,0,48,48).data;
    const digest=await crypto.subtle.digest('SHA-256',data);
    hashes.push([...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join(''));
  }
  return hashes;
}"""

RGBA = """async source => {
  const image=new Image();image.src=source;await image.decode();
  const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
  const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
  return [canvas.width,canvas.height,...ctx.getImageData(0,0,canvas.width,canvas.height).data];
}"""


def build(check=False, channel=None):
    from playwright.sync_api import sync_playwright

    configs = configurations()
    targets = {}
    with tempfile.TemporaryDirectory(prefix="cat-art-build-") as temporary:
        work = Path(temporary)
        for character in configs:
            shutil.copyfile(
                ROOT / f"artwork/images/cat-assistant-style/{character}.png",
                work / f"master-{character}.png",
            )
        shutil.copyfile(ROOT / "static/icons/persona-mark.png", work / "logo.png")
        shutil.copyfile(
            ROOT / "apps/accounts/static/accounts/cat-renderer.js", work / "cat-renderer.js"
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=work))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(**({"channel": channel} if channel else {}))
                try:
                    page = browser.new_page()
                    base = f"http://127.0.0.1:{server.server_port}"
                    for character, original in configs.items():
                        config = {
                            **original,
                            "native_grid": False,
                            "source": f"/master-{character}.png",
                        }
                        (work / "index.html").write_text(html(config))
                        page.goto(f"{base}/index.html?raw={character}")
                        page.wait_for_selector('[data-render-ready="true"]')
                        encoded = page.evaluate(EXPORT)
                        generated = work / f"grid-{character}.png"
                        generated.write_bytes(base64.b64decode(encoded))
                        target = ROOT / f"static/images/cat-assistant-style48/{character}.png"
                        targets[target] = generated.read_bytes()
                        raw_hashes = page.evaluate(FRAME_HASHES)
                        config.update(native_grid=True, source=f"/grid-{character}.png")
                        (work / "index.html").write_text(html(config))
                        page.goto(f"{base}/index.html?native={character}")
                        page.wait_for_selector('[data-render-ready="true"]')
                        assert page.evaluate(FRAME_HASHES) == raw_hashes, character
                        if check:
                            shipped = work / f"shipped-{character}.png"
                            shutil.copyfile(target, shipped)
                            assert page.evaluate(RGBA, f"/{shipped.name}") == page.evaluate(
                                RGBA, f"/{generated.name}"
                            ), target
                    logo = page.evaluate("""async () => {
                      const image=new Image();image.src='/logo.png';await image.decode();
                      const canvas=document.createElement('canvas');canvas.width=canvas.height=96;
                      const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=true;
                      ctx.imageSmoothingQuality='high';ctx.drawImage(image,0,0,96,96);
                      return canvas.toDataURL().split(',')[1];
                    }""")
                    generated = work / "small-logo.png"
                    generated.write_bytes(base64.b64decode(logo))
                    target = ROOT / "static/icons/persona-mark-small.png"
                    targets[target] = generated.read_bytes()
                    if check:
                        shutil.copyfile(target, work / "shipped-logo.png")
                        assert page.evaluate(RGBA, "/small-logo.png") == page.evaluate(
                            RGBA, "/shipped-logo.png"
                        ), target
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    if not check:
        for target, data in targets.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(
        f"{'Checked RGBA' if check else 'Exported'} {len(targets)} assets; "
        "all150raw/native frames match"
    )
    for target, data in targets.items():
        print(f"{target.relative_to(ROOT)}: {len(data)} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--browser-channel")
    args = parser.parse_args()
    build(args.check, args.browser_channel)


if __name__ == "__main__":
    main()
