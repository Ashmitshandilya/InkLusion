#!/usr/bin/env python3
"""
Realistic highlight covers: AI artwork (black background) + the highlight's name in huge smoky
blackletter BEHIND the subject, so the art overlaps the word.

    reels/.venv/bin/python brand/highlight-covers/compose.py art/reviews.png reviews ...
Each pair: <art image> <word>. Writes <n>-<word>.png (1080x1920) next to this file.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE.parents[1] / "reels" / "fonts" / "PirataOne-Regular.woff2"
W, H = 1080, 1920
PINK = (255, 43, 214)


def font(size):
    try:
        return ImageFont.truetype(str(FONT), size)
    except OSError:  # Pillow without woff2 support: convert once with fontTools
        from fontTools.ttLib import TTFont
        ttf = FONT.with_suffix(".ttf")
        if not ttf.exists():
            f = TTFont(str(FONT))
            f.flavor = None
            f.save(str(ttf))
        return ImageFont.truetype(str(ttf), size)


def grade(art):
    """Slight alteration: deeper blacks, crisper mid-tones, cooler greys, pink kept."""
    a = art.astype(np.float32) / 255
    lum = a.mean(2, keepdims=True)
    pinkish = np.clip((a[..., 0:1] - a[..., 1:2]) * 3, 0, 1)  # keep pink areas saturated
    grey = lum + (a - lum) * (0.55 + 0.45 * pinkish)
    grey = np.clip((grey - 0.04) / 0.94, 0, 1) ** 1.12  # crush blacks, gentle contrast
    grey[..., 2:3] += 0.015 * (1 - pinkish)  # faint cool cast
    return np.clip(grey * 255, 0, 255).astype(np.uint8)


def subject_mask(art):
    """Background is near-black: the subject is anything brighter, feathered."""
    g = cv2.cvtColor(art, cv2.COLOR_RGB2GRAY).astype(np.float32)
    m = np.clip((g - 14) / 40, 0, 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 3)


def word_layer(word, cy):
    """Huge blackletter word in smoky grey with a pink inner glow, as background texture."""
    size = 300
    f = font(size)
    while f.getlength(word) > 700 and size > 120:  # stay inside the profile circle
        size -= 10
        f = font(size)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    bx = d.textbbox((0, 0), word, font=f)
    x = (W - (bx[2] - bx[0])) / 2 - bx[0]
    y = cy - (bx[1] + bx[3]) / 2
    d.text((x, y), word, font=f, fill=255)
    m = np.asarray(img).astype(np.float32) / 255
    # smoke texture inside the letters
    rng = np.random.default_rng(len(word))
    n = cv2.resize(rng.random((48, 27)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), 25)
    n = (n - n.min()) / (n.max() - n.min() + 1e-9)
    tone = 0.24 + 0.26 * n  # dim, uneven grey
    rgb = np.dstack([tone * 235, tone * 228, tone * 232]) * m[..., None]
    glow = cv2.GaussianBlur(m, (0, 0), 30)[..., None] * np.array(PINK, np.float32)[None, None] * 0.22
    edge = cv2.GaussianBlur(m, (0, 0), 1.2)
    return rgb + glow, m, edge


def compose(art_path, word, out):
    art = np.asarray(Image.open(art_path).convert("RGB")).copy()
    # some previews come as a disc on white: black out anything bright touching the corners
    h, w = art.shape[:2]
    if art[:4, :4].mean() > 200 or art[-4:, -4:].mean() > 200:
        yy, xx = np.mgrid[0:h, 0:w]
        outside = np.hypot(xx - w / 2, yy - h / 2) > min(h, w) / 2 - 2
        art[outside] = 0
    art = grade(art)
    side = 860
    art = cv2.resize(art, (side, side), interpolation=cv2.INTER_LANCZOS4 if art.shape[0] < side else cv2.INTER_AREA)
    mask = subject_mask(art)

    canvas = np.zeros((H, W, 3), np.float32)
    # dark backdrop: soft vignette + faint grain
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot((xx - W / 2) / W, (yy - H / 2) / H)
    canvas += (np.clip(0.5 - r, 0, 1) * 34)[..., None] * np.array([1.0, 0.75, 0.95])
    word_rgb, wm, _ = word_layer(word, H / 2 + 250)
    canvas = canvas * (1 - wm[..., None] * 0.9) + word_rgb

    x0, y0 = (W - side) // 2, (H - side) // 2 - 50
    reg = canvas[y0:y0 + side, x0:x0 + side]
    m = mask[..., None]
    canvas[y0:y0 + side, x0:x0 + side] = reg * (1 - m) + art.astype(np.float32) * m

    # thin ring that frames the circle crop
    ring = np.zeros((H, W), np.uint8)
    cv2.circle(ring, (W // 2, H // 2), 500, 255, 3, cv2.LINE_AA)
    canvas = canvas * (1 - ring[..., None] / 255 * 0.35) + ring[..., None] / 255 * 0.35 * 200
    grain = np.random.default_rng(1).normal(0, 5, (H, W, 1))
    out_img = np.clip(canvas + grain, 0, 255).astype(np.uint8)
    Image.fromarray(out_img).save(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        n = i // 2 + 1
        out = HERE / f"{n}-{Path(args[i]).stem}.png"
        compose(args[i], args[i + 1], out)
        print("wrote", out)
