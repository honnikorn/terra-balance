#!/usr/bin/env python3
"""
Terra Balance – Icon Generator
Generates all required PNG icons for PWA manifest and Android app.
Run: python3 icons/generate-icons.py
Requires: Pillow  →  pip install Pillow
"""

import os
import math
import struct
import zlib

# Try Pillow first; fall back to pure-Python PNG writer
try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

# ── Colour palette (matches the game) ─────────────────────────────────────────
BG       = (2,   5,   8)        # #020508  deep space
OCEAN    = (15,  55, 100)       # dark blue ocean
LAND1    = (22,  80,  50)       # #165032  dark forest green
LAND2    = (45, 120,  70)       # brighter green land
GLOW     = (82, 180, 232)       # #52b4e8  cyan highlight
GOLD     = (201, 162,  39)      # #c9a227
ATMOS    = (20,  60, 120, 60)   # thin atmosphere halo (RGBA)

ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]


# ── Pure-Python PNG fallback ───────────────────────────────────────────────────
def _write_png(path, width, height, pixels_rgba):
    """Write RGBA pixel array to a PNG file without any dependencies."""
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    raw = b''
    for row in pixels_rgba:
        raw += b'\x00' + b''.join(struct.pack('BBBB', *px) for px in row)

    png = (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', ihdr)
        + chunk(b'IDAT', zlib.compress(raw, 9))
        + chunk(b'IEND', b'')
    )
    with open(path, 'wb') as f:
        f.write(png)


# ── Icon drawing ──────────────────────────────────────────────────────────────
def lerp_colour(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_icon_pillow(size, maskable=False):
    """Draw the Terra Balance icon using Pillow."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    cx = cy = size // 2
    r  = int(size * 0.47)
    pad = int(size * (0.13 if maskable else 0.03))

    # Background
    bg_r = cx  # fill entire canvas for maskable
    if maskable:
        d.rectangle([0, 0, size, size], fill=(*BG, 255))
    else:
        d.ellipse([cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r], fill=(*BG, 255))

    # Atmosphere glow
    for i in range(6):
        t = i / 6
        ar = r + int(size * 0.06 * (1 - t))
        alpha = int(40 * (1 - t))
        d.ellipse([cx - ar, cy - ar, cx + ar, cy + ar],
                  outline=(*GLOW, alpha), width=max(1, size // 80))

    # Ocean base
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*OCEAN, 255))

    # Simplified continent shapes (scaled to icon size)
    s = size / 512  # scale factor

    def poly(pts, colour):
        scaled = [(int(cx + p[0] * s), int(cy + p[1] * s)) for p in pts]
        d.polygon(scaled, fill=(*colour, 255))

    # North America
    poly([(-140, -160), (-70, -200), (-30, -170), (-20, -100),
          (-80, -60), (-150, -80), (-160, -120)], LAND1)
    poly([(-100, -130), (-55, -155), (-25, -130), (-45, -90), (-95, -85)], LAND2)

    # South America
    poly([(-60, -30), (-20, -30), (10, 40), (0, 130),
          (-50, 150), (-80, 80), (-70, 0)], LAND1)

    # Europe
    poly([(20, -200), (80, -210), (90, -160), (60, -130),
          (10, -140), (0, -180)], LAND2)

    # Africa
    poly([(10, -100), (80, -120), (100, -50), (90,  80),
          (50, 150), (10, 130), (-10, 40), (0, -50)], LAND1)
    poly([(20, -80), (75, -95), (90, -40), (80, 50), (40, 100),
          (10, 90), (0, 10)], LAND2)

    # Asia / Russia
    poly([(100, -220), (220, -230), (230, -120), (160, -100),
          (100, -130), (80, -170)], LAND1)
    poly([(100, -100), (200, -110), (210, -40), (160, -20),
          (90, -40), (85, -80)], LAND2)

    # Australia
    poly([(130, 60), (200, 50), (210, 110), (180, 150),
          (120, 140), (110, 90)], LAND2)

    # Polar ice caps
    d.ellipse([cx - r, cy - r, cx - r + int(r * 0.6), cy - r + int(r * 0.4)],
              fill=(200, 220, 240, 220))

    # Highlight sheen
    hr = int(r * 0.5)
    hx = cx - int(r * 0.2)
    hy = cy - int(r * 0.2)
    for i in range(4):
        t  = i / 4
        hr2 = int(hr * (1 - t * 0.8))
        alp = int(25 * (1 - t))
        d.ellipse([hx - hr2, hy - hr2, hx + hr2, hy + hr2],
                  fill=(255, 255, 255, alp))

    # Gold orbit ring
    ring_r = int(r * 1.12)
    ring_w = max(1, size // 90)
    d.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
          start=-30, end=120, fill=(*GOLD, 200), width=ring_w)
    d.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
          start=160, end=310, fill=(*GOLD, 80), width=max(1, ring_w - 1))

    return img


def draw_icon_pure(size):
    """Draw a simplified icon without Pillow (pure Python)."""
    pixels = []
    cx = cy = size / 2
    r  = size * 0.47
    ring_r = r * 1.12

    for y in range(size):
        row = []
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > ring_r + 2:
                row.append((0, 0, 0, 0))  # transparent outside
            elif dist > r:
                # Atmosphere / ring area
                ang = math.degrees(math.atan2(dy, dx))
                in_ring = (dist > ring_r - 2) and (dist < ring_r + 2)
                if in_ring and (-30 <= ang <= 120):
                    row.append((*GOLD, 200))
                else:
                    row.append((0, 0, 0, 0))
            else:
                # Inside the globe
                nx = dx / r
                ny = dy / r
                # Simple latitude/longitude colouring
                lat = math.degrees(math.asin(max(-1, min(1, -ny))))
                lon = math.degrees(math.atan2(dy, dx)) + 60

                # Ice caps
                if abs(lat) > 70:
                    row.append((200, 220, 240, 255))
                else:
                    # Rough land/ocean split
                    land_val = (
                        math.sin(lon * 0.04) * math.cos(lat * 0.06) +
                        math.sin(lon * 0.07 + 1.2) * 0.5 +
                        math.cos(lat * 0.09 + 0.8) * 0.3
                    )
                    if land_val > 0.05:
                        t = min(1.0, (land_val - 0.05) / 0.4)
                        c = lerp_colour(LAND1, LAND2, t)
                    else:
                        t = min(1.0, (-land_val + 0.3) / 0.6)
                        c = lerp_colour(OCEAN, (8, 35, 75), t)

                    # Highlight
                    hl = max(0, (0.4 - dist / r) * 0.3)
                    c = tuple(min(255, int(c[i] + hl * 80)) for i in range(3))
                    row.append((*c, 255))
        pixels.append(row)
    return pixels


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    if HAS_PILLOW:
        print("Using Pillow for high-quality icon rendering.")
        for sz in ICON_SIZES:
            img  = draw_icon_pillow(sz)
            path = os.path.join(out_dir, f'icon-{sz}.png')
            img.save(path, 'PNG', optimize=True)
            print(f'  ✓  icons/icon-{sz}.png')

        # Maskable icon (safe zone = 80% of canvas)
        img_mask = draw_icon_pillow(512, maskable=True)
        path = os.path.join(out_dir, 'icon-512-maskable.png')
        img_mask.save(path, 'PNG', optimize=True)
        print(f'  ✓  icons/icon-512-maskable.png')
    else:
        print("Pillow not found — using pure-Python fallback (lower quality).")
        print("Install Pillow for better icons:  pip install Pillow\n")
        for sz in ICON_SIZES:
            pixels = draw_icon_pure(sz)
            path   = os.path.join(out_dir, f'icon-{sz}.png')
            _write_png(path, sz, sz, pixels)
            print(f'  ✓  icons/icon-{sz}.png')

        pixels = draw_icon_pure(512)
        path   = os.path.join(out_dir, 'icon-512-maskable.png')
        _write_png(path, 512, 512, pixels)
        print(f'  ✓  icons/icon-512-maskable.png')

    print(f'\nAll icons written to {out_dir}/')
    print('Next: copy the icons folder into your Android project res directories.')


if __name__ == '__main__':
    main()
