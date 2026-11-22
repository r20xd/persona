"""Current toy PNG invariants and screenshot decoding for live browser checks."""

import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOYS = ROOT / "static/images/cat-pixel48"


def decode(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    chunks = {}
    offset = 8
    while offset < len(data):
        length = struct.unpack("!I", data[offset : offset + 4])[0]
        kind, payload = data[offset + 4 : offset + 8], data[offset + 8 : offset + 8 + length]
        assert (
            zlib.crc32(kind + payload) & 0xFFFFFFFF
            == struct.unpack("!I", data[offset + 8 + length : offset + 12 + length])[0]
        )
        chunks[kind] = chunks.get(kind, b"") + payload
        offset += 12 + length
    w, h, depth, mode, _, _, interlace = struct.unpack("!IIBBBBB", chunks[b"IHDR"])
    assert depth == 8 and mode == 3 and interlace == 0
    palette = list(zip(*[iter(chunks[b"PLTE"])] * 3, strict=True))
    alpha = chunks[b"tRNS"]
    raw = zlib.decompress(chunks[b"IDAT"])
    assert len(raw) == h * (w + 1)
    rows = []
    for y in range(h):
        assert raw[y * (w + 1)] == 0
        rows.append(list(raw[y * (w + 1) + 1 : (y + 1) * (w + 1)]))
    return w, h, palette, alpha, rows


def test_toys_have_exact_grid_and_binary_palette():
    paths = list(TOYS.glob("*.png"))
    assert {path.name for path in paths} == {
        f"toy-{kind}.png" for kind in ("yarn", "ball", "mouse", "fish")
    }
    for path in paths:
        w, h, palette, alpha, rows = decode(path)
        assert (w, h) == (32, 32)
        assert len(palette) <= 16 and set(alpha) == {0, 255}
        used = {pixel for row in rows for pixel in row}
        assert used <= set(range(len(palette)))
        assert 0 in used and len(used) >= 3


def test_generator_reproduces_current_toys_without_source_rasters(tmp_path):
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_cat_toys.py")],
        cwd=tmp_path,
        check=True,
    )
    generated = tmp_path / TOYS.relative_to(ROOT)
    assert {path.name for path in generated.glob("*.png")} == {
        path.name for path in TOYS.glob("*.png")
    }
    for path in TOYS.glob("*.png"):
        assert path.read_bytes() == (generated / path.name).read_bytes()


def screenshot_pixels(data):
    """Decode Chrome's RGB/RGBA screenshot including all PNG filter modes."""
    chunks = {}
    offset = 8
    while offset < len(data):
        length = struct.unpack("!I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunks[kind] = chunks.get(kind, b"") + data[offset + 8 : offset + 8 + length]
        offset += 12 + length
    w, h, depth, mode, _, _, _ = struct.unpack("!IIBBBBB", chunks[b"IHDR"])
    assert depth == 8 and mode in (2, 6)
    bpp = 3 if mode == 2 else 4
    raw = zlib.decompress(chunks[b"IDAT"])
    stride = w * bpp
    previous = [0] * stride
    rows = []
    for y in range(h):
        kind = raw[y * (stride + 1)]
        scan = list(raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)])
        for i in range(stride):
            a = scan[i - bpp] if i >= bpp else 0
            b = previous[i]
            c = previous[i - bpp] if i >= bpp else 0
            if kind == 1:
                predict = a
            elif kind == 2:
                predict = b
            elif kind == 3:
                predict = (a + b) // 2
            elif kind == 4:
                p = a + b - c
                distances = [abs(p - a), abs(p - b), abs(p - c)]
                predict = [a, b, c][distances.index(min(distances))]
            else:
                assert kind == 0
                predict = 0
            scan[i] = (scan[i] + predict) % 256
        rows.append([tuple(scan[x * bpp : x * bpp + 3]) for x in range(w)])
        previous = scan
    return w, h, rows


def test_four_toys_do_not_overlap_at_scene_positions():
    placements = {"yarn": (0, 48), "ball": (20, 72), "mouse": (52, 72), "fish": (72, 48)}
    occupied = set()
    for toy, (ox, oy) in placements.items():
        ink = {
            (x + ox, y + oy)
            for y, row in enumerate(decode(TOYS / f"toy-{toy}.png")[4])
            for x, v in enumerate(row)
            if v
        }
        assert not occupied & ink
        occupied |= ink
