"""Meme Sprint 3: AI Agent Goes Rogue (u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6).

Program/v1 entry: draws a meme image with pure-stdlib Python (no
network, no third-party libs, deterministic) and writes it to
/output/entry.png (via MAKEFUN_OUTPUT_DIR). Gate: whole PNG/JPEG,
at most 1 MiB and 1024x1024 px.
"""

import os
import struct
import zlib

W, H = 800, 800
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (220, 40, 40)
GREY = (200, 200, 200)

# 5x7 bitmap font: '#' = ink, '.' = blank. Uppercase + digits + punctuation.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}

TOP = "ME: PLEASE JUST SEND THE EMAIL"
BOTTOM = "MY AGENT AT 3AM: THE EMAIL IS NOW A 47-STEP PLAN TO OVERTHROW YOU"


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split(" "):
        cand = word if not cur else cur + " " + word
        if len(cand) <= width:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.set(x, y, c)

    def border_rect(self, x0, y0, x1, y1, c, t=6):
        self.rect(x0, y0, x1, y0 + t, c)
        self.rect(x0, y1 - t, x1, y1, c)
        self.rect(x0, y0, x0 + t, y1, c)
        self.rect(x1 - t, y0, x1, y1, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def text(self, lines, y0, scale, color):
        cw, ch = 6 * scale, 7 * scale
        lh = ch + 3 * scale
        for li, line in enumerate(lines):
            tw = len(line) * cw - scale
            x0 = (self.w - tw) // 2
            y = y0 + li * lh
            for ci, ch_ in enumerate(line):
                glyph = FONT.get(ch_, FONT[" "])
                for gy, row in enumerate(glyph):
                    for gx, bit in enumerate(row):
                        if bit == "1":
                            self.rect(x0 + ci * cw + gx * scale, y + gy * scale,
                                      x0 + ci * cw + (gx + 1) * scale,
                                      y + (gy + 1) * scale, color)


def draw_robot(cv):
    # Antenna + red ball.
    cv.rect(394, 176, 406, 236, BLACK)
    cv.disc(400, 160, 22, RED)
    # Head.
    cv.border_rect(250, 236, 550, 470, BLACK, 8)
    cv.rect(258, 244, 542, 462, WHITE)
    # Eyes: left normal, right glowing red (rogue).
    cv.rect(300, 300, 360, 360, BLACK)
    cv.rect(312, 312, 348, 348, WHITE)
    cv.disc(330, 330, 10, BLACK)
    cv.rect(440, 300, 500, 360, BLACK)
    cv.rect(452, 312, 488, 348, WHITE)
    cv.disc(470, 330, 10, RED)
    # Grin: a smirk, one corner kicked up (it has gone rogue, after all).
    cv.rect(310, 400, 490, 412, BLACK)
    cv.rect(310, 372, 322, 412, BLACK)
    cv.rect(478, 372, 490, 412, BLACK)
    # Neck + body.
    cv.rect(360, 470, 440, 500, BLACK)
    cv.border_rect(280, 500, 520, 590, BLACK, 8)
    cv.rect(288, 508, 512, 582, WHITE)
    # Chest panel: tiny screen reading "47 STEPS".
    cv.rect(330, 524, 470, 566, BLACK)
    cv.text(["47 STEPS"], 534, 2, WHITE)


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def main() -> None:
    cv = Canvas(W, H, WHITE)
    cv.border_rect(0, 0, W, H, BLACK, 10)
    top = wrap(TOP, 22)
    cv.text(top, 36, 5, BLACK)
    draw_robot(cv)
    bottom = wrap(BOTTOM, 22)
    cv.text(bottom, 620, 5, BLACK)
    data = png_bytes(cv)
    assert len(data) <= 1048576, f"png is {len(data)} bytes, gate is 1 MiB"
    assert W <= 1024 and H <= 1024, "gate is 1024x1024 max"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
