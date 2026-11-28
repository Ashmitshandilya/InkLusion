#!/usr/bin/env python3
"""Instagram highlight covers in the InkLusion look. 1080x1920 each, icon inside the centre circle.

    reels/.venv/bin/python reels/highlights.py
Writes brand/highlight-covers/*.png and preview.png (how they look as circles on the profile).
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reelkit.overlays import Brand, glow  # noqa: E402

W, H = 1080, 1920
CX, CY = W // 2, H // 2
OUT = Path(__file__).resolve().parents[1] / "brand" / "highlight-covers"
B = Brand()
NEON, INK = B.accent, B.ink


def background(seed):
    rnd = random.Random(seed)
    bg = Image.new("RGBA", (W, H), B.bg + (255,))
    neb = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(neb)
    for _ in range(14):
        x, y = rnd.gauss(CX, 260), rnd.gauss(CY, 300)
        r = rnd.uniform(140, 320)
        c = NEON if rnd.random() < 0.55 else B.violet
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (rnd.randint(10, 22),))
    bg.alpha_composite(neb.filter(ImageFilter.GaussianBlur(130)))
    st = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(st)
    for _ in range(260):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.choice([0.8, 1, 1.3, 1.8])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(240, 228, 255, rnd.randint(70, 210)))
    bg.alpha_composite(st)
    # eclipse rim around the icon: ties the four together and frames the circle crop
    R = 360
    cor = Image.new("RGBA", (W, H))
    ImageDraw.Draw(cor).ellipse((CX - R * 1.12, CY - R * 1.12, CX + R * 1.12, CY + R * 1.12), fill=NEON + (70,))
    bg.alpha_composite(cor.filter(ImageFilter.GaussianBlur(60)))
    ImageDraw.Draw(bg).ellipse((CX - R, CY - R, CX + R, CY + R), fill=(0, 0, 0, 255))
    rim = Image.new("RGBA", (W, H))
    ImageDraw.Draw(rim).ellipse((CX - R, CY - R, CX + R, CY + R), outline=(255, 200, 245, 255), width=3)
    bg.alpha_composite(glow(rim, 10, 1.4))
    return bg


def neon(draw_fn, width=10, radius=18):
    """Draw line art with draw_fn(ImageDraw, colour, width) and give it a neon glow."""
    lay = Image.new("RGBA", (W, H))
    draw_fn(ImageDraw.Draw(lay), INK + (255,), width)
    col = Image.new("RGBA", (W, H))
    draw_fn(ImageDraw.Draw(col), NEON + (255,), width + 8)
    out = glow(col, radius, 1.6)
    out.alpha_composite(glow(lay, 4, 1.0))
    return out


def star_pts(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def sparkle_pts(cx, cy, r, k=0.16):
    """Four-point star (the ✦ used across the site)."""
    pts = []
    for i in range(32):
        a = 2 * math.pi * i / 32
        c, s = math.cos(a), math.sin(a)
        rr = r * (abs(c) ** (2 / 0.5) + abs(s) ** (2 / 0.5)) ** -0.5 if False else None
        # astroid: |x|^(2/3) + |y|^(2/3) = r^(2/3)
        pts.append((cx + r * c ** 3 if c >= 0 else cx - r * (-c) ** 3, cy + r * s ** 3 if s >= 0 else cy - r * (-s) ** 3))
    return pts


def reviews(d, col, w):
    d.line(star_pts(CX, CY - 10, 190, 80) + [star_pts(CX, CY - 10, 190, 80)[0]], fill=col, width=w, joint="curve")
    for i, x in enumerate((-110, -55, 0, 55, 110)):
        p = star_pts(CX + x, CY + 230, 20, 8)
        d.polygon(p, fill=col)


def highlights(d, col, w):
    d.line(sparkle_pts(CX, CY, 210) + [sparkle_pts(CX, CY, 210)[0]], fill=col, width=w, joint="curve")
    for x, y, r in ((CX + 170, CY - 170, 55), (CX - 175, CY + 160, 38)):
        p = sparkle_pts(x, y, r)
        d.polygon(p, fill=col)


def faqs(d, col, w):
    f = B.font("serif_italic", 520)
    q = "?"
    bx = d.textbbox((0, 0), q, font=f)
    d.text((CX - (bx[0] + bx[2]) / 2, CY - (bx[1] + bx[3]) / 2 - 10), q, font=f, fill=col)


def dm(d, col, w):
    x0, y0, x1, y1 = CX - 200, CY - 150, CX + 200, CY + 110
    d.rounded_rectangle((x0, y0, x1, y1), radius=90, outline=col, width=w)
    d.line([(CX - 90, y1 - 3), (CX - 140, y1 + 85), (CX - 20, y1 - 3)], fill=col, width=w, joint="curve")
    for x in (-90, 0, 90):
        d.ellipse((CX + x - 22, CY - 42, CX + x + 22, CY + 2), fill=col)


COVERS = [("reviews", reviews), ("highlights", highlights), ("faqs", faqs), ("dm-for-details", dm)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tiles = []
    for i, (name, fn) in enumerate(COVERS):
        img = background(seed=20 + i)
        img.alpha_composite(neon(fn))
        img = img.convert("RGB")
        img.save(OUT / f"{i + 1}-{name}.png")
        tiles.append((name, img))
    # preview: the circles as they appear on the profile
    s, pad = 220, 70
    prev = Image.new("RGB", (pad + len(tiles) * (s + pad), s + 150), (13, 15, 19))
    d = ImageDraw.Draw(prev)
    labels = {"reviews": "reviews ;)", "highlights": "Highlights", "faqs": "FAQs", "dm-for-details": "DM for details"}
    for i, (name, img) in enumerate(tiles):
        sq = img.crop((0, (H - W) // 2, W, (H + W) // 2)).resize((s, s), Image.LANCZOS)
        m = Image.new("L", (s, s), 0)
        ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
        x = pad + i * (s + pad)
        d.ellipse((x - 8, 32, x + s + 8, 40 + s + 8 - 8), outline=(60, 62, 70), width=4)
        prev.paste(sq, (x, 36), m)
        f = B.font("sans", 28)
        t = labels[name]
        d.text((x + s / 2 - f.getlength(t) / 2, s + 70), t, font=f, fill=(235, 235, 240))
    prev.save(OUT / "preview.png")
    print(f"saved to {OUT}")


if __name__ == "__main__":
    main()
