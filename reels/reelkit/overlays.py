"""Text and graphics, drawn once with Pillow and composited per frame as small BGR + alpha layers."""

import json
import random
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .util import FONTS, ROOT, W, H

# Reels UI covers the top ~220 px, the bottom ~400 px and a strip on the right.
SAFE_X, SAFE_TOP, SAFE_BOTTOM = 84, 230, 400


def rgb(hexstr):
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Brand:
    def __init__(self, path=ROOT / "brand.json"):
        self.d = json.loads(path.read_text())
        c = self.d["colors"]
        self.accent, self.ink, self.muted = rgb(c["accent"]), rgb(c["ink"]), rgb(c["muted"])
        self.violet, self.bg = rgb(c["violet"]), rgb(c["bg"])
        self.f = self.d["fonts"]

    def __getattr__(self, k):
        try:
            return self.d[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def font(self, kind, size):
        return ImageFont.truetype(str(FONTS / self.f[kind]), size)


@dataclass
class Layer:
    x: int
    y: int
    bgr: np.ndarray  # float32, premultiplied by alpha
    a: np.ndarray  # float32 (h, w, 1), 0..1

    def draw(self, frame, opacity=1.0, dx=0, dy=0):
        if opacity <= 0.003:
            return
        x, y = self.x + int(dx), self.y + int(dy)
        h, w = self.a.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(frame.shape[1], x + w), min(frame.shape[0], y + h)
        if x1 <= x0 or y1 <= y0:
            return
        sub = frame[y0:y1, x0:x1].astype(np.float32)
        a = self.a[y0 - y:y1 - y, x0 - x:x1 - x] * opacity
        c = self.bgr[y0 - y:y1 - y, x0 - x:x1 - x] * opacity
        frame[y0:y1, x0:x1] = np.clip(sub * (1 - a) + c, 0, 255).astype(np.uint8)


def to_layer(img):
    """RGBA Pillow image (any size, positioned at 0,0 of the reel) -> cropped Layer."""
    arr = np.asarray(img).astype(np.float32)
    alpha = arr[..., 3] / 255.0
    ys, xs = np.nonzero(alpha > 0.004)
    if not len(xs):
        return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    a = alpha[y0:y1, x0:x1, None]
    bgr = arr[y0:y1, x0:x1, 2::-1] * a
    return Layer(int(x0), int(y0), np.ascontiguousarray(bgr), np.ascontiguousarray(a))


def glow(layer, radius=22, strength=1.6):
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    r, g, b, a = blur.split()
    a = a.point(lambda v: min(255, int(v * strength)))
    out = Image.new("RGBA", layer.size)
    out.alpha_composite(Image.merge("RGBA", (r, g, b, a)))
    out.alpha_composite(layer)
    return out


def spaced(brand, text, size, tracking=0.22):
    f = brand.font("mono", size)
    gap = size * tracking
    return f, gap, sum(f.getlength(c) for c in text) + gap * (len(text) - 1)


def draw_spaced(brand, d, xy, text, size, fill, tracking=0.22):
    f, gap, _ = spaced(brand, text, size, tracking)
    x, y = xy
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + gap


def wrap(text, f, max_w):
    lines, line = [], ""
    for w in text.split():
        t = f"{line} {w}".strip()
        if f.getlength(t) <= max_w or not line:
            line = t
        else:
            lines.append(line)
            line = w
    return lines + ([line] if line else [])


def shade_band(y0, y1, alpha=125):
    """Soft dark band so white text reads over bright skin."""
    s = Image.new("RGBA", (W, H))
    ImageDraw.Draw(s).rectangle((0, y0, W, y1), fill=(0, 0, 0, alpha))
    return to_layer(s.filter(ImageFilter.GaussianBlur(70)))


def hook_words(brand, text, y_frac=0.40, size=150, tag=True):
    """Kinetic hook: one layer per word (revealed on successive beats) + the studio tag + a shade band."""
    big = brand.font("serif_italic", size)
    lines = wrap(text, big, W - 2 * SAFE_X)
    lh = int(size * 1.0)
    y0 = int(H * y_frac - lh * len(lines) / 2)
    words = []
    for i, ln in enumerate(lines):
        x = (W - big.getlength(ln)) / 2
        for wd in ln.split(" "):
            im = Image.new("RGBA", (W, H))
            ImageDraw.Draw(im).text((x, y0 + i * lh), wd, font=big, fill=brand.ink + (255,))
            words.append(to_layer(glow(im, 24, 0.8)))
            x += big.getlength(wd + " ")
    tg = Image.new("RGBA", (W, H))
    if tag:
        _, _, tw = spaced(brand, brand.tag, 26)
        draw_spaced(brand, ImageDraw.Draw(tg), ((W - tw) / 2, y0 - 66), brand.tag, 26, brand.muted + (255,))
    return words, to_layer(tg), shade_band(y0 - 150, y0 + lh * len(lines) + 90)


def caption(brand, text, y=None, size=64):
    """Story line: serif, centred, low in the safe area."""
    f = brand.font("serif", size)
    lines = wrap(text, f, W - 2 * SAFE_X - 40)
    y = y if y is not None else H - SAFE_BOTTOM - 60 - len(lines) * size * 1.1
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text(((W - f.getlength(ln)) / 2, y + i * size * 1.1), ln, font=f, fill=brand.ink + (255,))
    sh = im.filter(ImageFilter.GaussianBlur(10))
    sh = Image.eval(sh, lambda v: v)  # keep
    base = Image.new("RGBA", (W, H))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dark.putalpha(sh.split()[3].point(lambda v: int(v * 0.8)))
    base.alpha_composite(dark)
    base.alpha_composite(im)
    return to_layer(base), shade_band(int(y) - 120, int(y + len(lines) * size * 1.1) + 100, 90)


def label(brand, text):
    """Small mono caption bottom-left with a neon dot (style · placement)."""
    y = H - SAFE_BOTTOM - 40
    im = Image.new("RGBA", (W, H))
    band = Image.new("RGBA", (W, H))
    ImageDraw.Draw(band).rectangle((0, y - 50, W, y + 80), fill=(0, 0, 0, 120))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(40)))
    dot = Image.new("RGBA", (W, H))
    ImageDraw.Draw(dot).ellipse((SAFE_X, y + 9, SAFE_X + 12, y + 21), fill=brand.accent + (255,))
    im.alpha_composite(glow(dot, 8, 2))
    sh = Image.new("RGBA", (W, H))
    draw_spaced(brand, ImageDraw.Draw(sh), (SAFE_X + 30, y + 2), text.upper(), 28, (0, 0, 0, 210))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    draw_spaced(brand, ImageDraw.Draw(im), (SAFE_X + 30, y), text.upper(), 28, brand.ink + (255,))
    return to_layer(im)


def space_bg(brand, seed=7, scale=1.1, eclipse=(0.5, 0.33, 230), stars=420):
    """Black space: nebula, stars and the eclipse from the website. Returns BGR uint8 (scaled up)."""
    rnd = random.Random(seed)
    cw, ch = int(W * scale), int(H * scale)
    bg = Image.new("RGBA", (cw, ch), brand.bg + (255,))
    neb = Image.new("RGBA", (cw, ch))
    nd = ImageDraw.Draw(neb)
    for _ in range(26):
        x, y = rnd.gauss(cw * 0.55, cw * 0.28), rnd.gauss(ch * 0.33, ch * 0.16)
        r = rnd.uniform(120, 340)
        c = brand.accent if rnd.random() < 0.6 else brand.violet
        nd.ellipse((x - r, y - r, x + r, y + r), fill=c + (rnd.randint(10, 28),))
    bg.alpha_composite(neb.filter(ImageFilter.GaussianBlur(120)))
    st = Image.new("RGBA", (cw, ch))
    sd = ImageDraw.Draw(st)
    for _ in range(stars):
        x, y, r = rnd.uniform(0, cw), rnd.uniform(0, ch), rnd.choice([0.8, 1, 1, 1.4, 2])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(240, 225, 255, rnd.randint(90, 230)))
    bg.alpha_composite(st)
    if eclipse:
        ex, ey, R = eclipse
        cx, cy = cw * ex, ch * ey
        cor = Image.new("RGBA", (cw, ch))
        cd = ImageDraw.Draw(cor)
        for k, a in ((1.6, 55), (1.32, 95), (1.15, 170)):
            cd.ellipse((cx - R * k, cy - R * k, cx + R * k, cy + R * k), fill=brand.accent + (a,))
        bg.alpha_composite(cor.filter(ImageFilter.GaussianBlur(R * 0.3)))
        rim = Image.new("RGBA", (cw, ch))
        ImageDraw.Draw(rim).ellipse((cx - R - 7, cy - R - 7, cx + R + 7, cy + R + 7), fill=(255, 215, 248, 255))
        bg.alpha_composite(rim.filter(ImageFilter.GaussianBlur(4)))
        ImageDraw.Draw(bg).ellipse((cx - R, cy - R, cx + R, cy + R), fill=(0, 0, 0, 255))
    return bg


def end_card(brand):
    """Eclipse + wordmark + booking line. BGR uint8 at 1.1x for a slow push-in."""
    bg = space_bg(brand)
    cw, ch = bg.size
    a, b = brand.font("serif", 230), brand.font("serif_italic", 230)
    w1, w2 = brand.wordmark
    wa, wb = a.getlength(w1), b.getlength(w2)
    x, y = (cw - wa - wb) / 2, ch * 0.53
    t = Image.new("RGBA", (cw, ch))
    ImageDraw.Draw(t).text((x, y), w1, font=a, fill=brand.ink + (255,))
    n = Image.new("RGBA", (cw, ch))
    ImageDraw.Draw(n).text((x + wa, y), w2, font=b, fill=brand.accent + (255,))
    t.alpha_composite(glow(n, 30, 1.5))
    bg.alpha_composite(t)
    d = ImageDraw.Draw(bg)
    _, _, lw = spaced(brand, brand.tag, 30)
    draw_spaced(brand, d, ((cw - lw) / 2, y - 40), brand.tag, 30, brand.muted + (255,))
    sf = brand.font("sans", 46)
    d.text(((cw - sf.getlength(brand.line)) / 2, y + 330), brand.line, font=sf, fill=brand.ink + (235,))
    _, _, hw = spaced(brand, brand.handle, 28, 0.12)
    draw_spaced(brand, d, ((cw - hw) / 2, y + 410), brand.handle, 28, brand.accent + (255,), 0.12)
    return np.ascontiguousarray(np.asarray(bg.convert("RGB"))[..., ::-1])


def card_frame(brand, rect):
    """Thin neon border + glow around a photo card at rect (x, y, w, h)."""
    x, y, w, h = rect
    im = Image.new("RGBA", (W, H))
    ImageDraw.Draw(im).rectangle((x - 2, y - 2, x + w + 1, y + h + 1), outline=brand.accent + (255,), width=2)
    g = glow(im, 26, 1.2)
    # cut the inside so the photo is not tinted
    cut = Image.new("L", (W, H), 255)
    ImageDraw.Draw(cut).rectangle((x, y, x + w - 1, y + h - 1), fill=0)
    r, gg, b, a = g.split()
    a = Image.fromarray(np.minimum(np.asarray(a), np.asarray(cut)))
    shadow = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shadow).rectangle((x + 10, y + 30, x + w + 10, y + h + 40), fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    sa = np.minimum(np.asarray(shadow.split()[3]), np.asarray(cut))
    shadow.putalpha(Image.fromarray(sa))
    out = Image.new("RGBA", (W, H))
    out.alpha_composite(shadow)
    out.alpha_composite(Image.merge("RGBA", (r, gg, b, a)))
    return to_layer(out)
