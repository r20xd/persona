"""Reproduce current 32×32 toy PNGs using the original CAT07 drawing and encoder.

Run from the repository root. Uses only Python's standard library; no raster input.
"""

import struct
import zlib
from pathlib import Path

PALETTE = [
    (0, 0, 0),
    (76, 66, 115),
    (137, 126, 196),
    (184, 177, 237),
    (219, 215, 250),
    (255, 249, 242),
    (255, 192, 219),
    (234, 133, 184),
    (48, 48, 81),
    (126, 209, 233),
    (255, 218, 119),
    (96, 154, 188),
]


def png(path, rows):
    """Write indexed PNG: one exact colour per pixel, no intermediate alpha."""
    h, w = len(rows), len(rows[0])
    assert all(len(row) == w for row in rows)

    def chunk(kind, data):
        return (
            struct.pack("!I", len(data))
            + kind
            + data
            + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    data = b"".join(b"\0" + bytes(row) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 3, 0, 0, 0))
        + chunk(b"PLTE", bytes(c for rgb in PALETTE for c in rgb))
        + chunk(b"tRNS", bytes([0] + [255] * (len(PALETTE) - 1)))
        + chunk(b"IDAT", zlib.compress(data, 9))
        + chunk(b"IEND", b"")
    )


class Drawing:
    def __init__(self, size):
        self.size = size
        self.rows = [[0] * size for _ in range(size)]

    def dot(self, x, y, colour):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.rows[y][x] = colour

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.dot(xx, yy, colour)

    def shape(self, points, fill=5, edge=2):
        for x, y in points:
            border = any(
                (x + dx, y + dy) not in points for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]
            )
            self.dot(x, y, edge if border else fill)

    def ellipse(self, x, y, w, h, fill=5, edge=2):
        points = {
            (xx, yy)
            for yy in range(y, y + h)
            for xx in range(x, x + w)
            if ((2 * xx + 1 - 2 * x - w) * h) ** 2 + ((2 * yy + 1 - 2 * y - h) * w) ** 2
            <= (w * h) ** 2
        }
        self.shape(points, fill, edge)

    def polygon(self, vertices, fill=5, edge=2):
        points = set()
        for y in range(min(p[1] for p in vertices), max(p[1] for p in vertices) + 1):
            for x in range(min(p[0] for p in vertices), max(p[0] for p in vertices) + 1):
                inside = False
                for a, b in zip(vertices, vertices[1:] + vertices[:1], strict=True):
                    if (a[1] > y + 0.5) != (b[1] > y + 0.5):
                        if x + 0.5 < (b[0] - a[0]) * (y + 0.5 - a[1]) / (b[1] - a[1]) + a[0]:
                            inside = not inside
                if inside:
                    points.add((x, y))
        self.shape(points, fill, edge)

    def line(self, x, y, endx, endy, colour):
        dx, dy = abs(endx - x), -abs(endy - y)
        sx, sy = (1 if x < endx else -1), (1 if y < endy else -1)
        error = dx + dy
        while True:
            self.dot(x, y, colour)
            if (x, y) == (endx, endy):
                break
            twice = error * 2
            if twice >= dy:
                error += dy
                x += sx
            if twice <= dx:
                error += dx
                y += sy


def toy(kind):
    d = Drawing(32)
    e, r, line = d.ellipse, d.rect, d.line
    if kind == "yarn":
        e(4, 4, 23, 23, 11, 1)
        e(6, 5, 17, 17, 9, 9)
        for offset in (0, 5, 10):
            line(7 + offset, 6, 5, 17 + offset, 11)
            line(8 + offset, 7, 6, 17 + offset, 4)
        line(8, 23, 24, 10, 1)
        line(13, 26, 26, 16, 1)
        line(22, 24, 28, 25, 11)
        line(28, 25, 28, 29, 11)
        line(28, 29, 23, 29, 11)
    elif kind == "ball":
        e(4, 3, 24, 25, 9, 1)
        d.polygon([(16, 4), (22, 8), (21, 15), (14, 17), (10, 11)], 5, 11)
        d.polygon([(7, 17), (14, 17), (18, 25), (11, 26), (6, 22)], 5, 11)
        line(21, 15, 27, 19, 11)
        line(10, 11, 5, 10, 11)
        line(18, 25, 23, 26, 11)
        r(10, 6, 3, 1, 5)
    elif kind == "mouse":
        e(7, 13, 21, 13, 4, 1)
        e(8, 7, 10, 12, 3, 1)
        e(10, 9, 6, 7, 6, 7)
        e(12, 16, 13, 7, 5, 5)
        r(24, 17, 2, 2, 8)
        r(27, 20, 2, 2, 7)
        for x in range(14, 23, 3):
            line(x, 22, x + 1, 24, 2)
        line(8, 23, 3, 26, 7)
        line(3, 26, 3, 29, 7)
        line(3, 29, 8, 29, 7)
    else:
        d.polygon([(4, 9), (12, 14), (12, 20), (4, 25)], 9, 1)
        e(9, 8, 20, 18, 9, 1)
        e(14, 10, 12, 13, 4, 4)
        r(24, 14, 2, 2, 8)
        r(24, 14, 1, 1, 5)
        d.polygon([(15, 8), (19, 4), (22, 9)], 11, 1)
        d.polygon([(15, 25), (20, 29), (22, 24)], 11, 1)
        for y in range(14, 23, 3):
            line(15, y, 17, y + 1, 11)
    return d.rows


def main():
    for kind in ("yarn", "ball", "mouse", "fish"):
        png(Path(f"static/images/cat-pixel48/toy-{kind}.png"), toy(kind))


if __name__ == "__main__":
    main()
