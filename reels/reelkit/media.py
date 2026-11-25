"""
Media: scan the inbox, prepare every photo and video once (rotation, HDR, 9:16 crop around the ink,
colour grade), and score each moment of each video so the editor can pick the best bits.

Roles come from folder or file names (optional):
  reveal / final / done / fresh   -> the finished tattoo, used on the drop
  healed                          -> healed photos
  process / lining / shading / stencil / session -> work in progress
  studio / shop / setup           -> the studio
  artist / portrait               -> the artist
Captions: put text in square brackets in the file name, e.g. "IMG_2041 [Fine line · forearm].jpg".
"""

import math
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .util import GRADE, TONEMAP, W, H, cache_path, file_key, load_json, log, probe, run, save_json

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:  # HEIC photos then need converting first
    pass

VERSION = 4
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".3gp", ".avi"}
IMG_W, IMG_H = 1350, 2400  # prepared photos: 1.25x the reel size, room to zoom

ROLES = {
    "reveal": {"reveal", "final", "finished", "done", "result", "fresh", "after"},
    "healed": {"healed", "heal"},
    "process": {"process", "lining", "line", "lines", "shading", "shade", "stencil", "session", "wip", "working",
                "before"},
    "studio": {"studio", "shop", "setup", "machine", "space"},
    "artist": {"artist", "portrait", "selfie", "shaurya"},
}
ANA_FPS = 6


@dataclass
class Item:
    id: str
    path: str
    kind: str  # image | video
    role: str  # reveal | healed | process | studio | artist | work
    label: str = ""
    w: int = 0
    h: int = 0
    duration: float = 0.0
    fps: int = 30
    file: str = ""  # prepared proxy (video mp4 / image png)
    sharp: float = 0.0  # 0..1 across the batch
    fit: bool = False  # photo shown whole on a soft background instead of cropped
    focus: tuple = (0.5, 0.5)  # where the ink is, in the prepared frame
    scores: list = field(default_factory=list)  # videos: quality per 1/ANA_FPS s
    activity: float = 0.0
    steady: float = 0.0

    def best_window(self, length, used=(), rng=None):
        """Start time of the best stretch of `length` seconds, avoiding stretches already used."""
        if self.kind != "video":
            return 0.0
        lo, hi = 0.3, self.duration - length - 0.3
        if hi <= lo:
            return max(0.0, (self.duration - length) / 2)
        sc = np.array(self.scores) if self.scores else np.zeros(1)
        best, best_t = -1e9, lo
        for t in np.arange(lo, hi + 1e-6, 0.1):
            a, b = int(t * ANA_FPS), max(int(t * ANA_FPS) + 1, int((t + length) * ANA_FPS))
            s = float(sc[a:b].mean()) if a < len(sc) else -1
            for u0, u1 in used:
                ov = max(0.0, min(t + length, u1) - max(t, u0))
                s -= 3.0 * ov / length
            if rng is not None:
                s += rng.uniform(0, 0.05)
            if s > best:
                best, best_t = s, float(t)
        return best_t


def _words(path, root):
    rel = Path(path).relative_to(root) if root in Path(path).parents else Path(path).name
    text = re.sub(r"\[.*?\]", " ", str(rel).lower())
    return set(re.split(r"[^a-z]+", text))


def _role(path, root, kind):
    words = _words(path, root)
    for role, keys in ROLES.items():
        if words & keys:
            return role
    return "process" if kind == "video" else "work"


def _label(path):
    m = re.search(r"\[(.+?)\]", Path(path).stem)
    return m.group(1).strip() if m else ""


def _saliency(gray):
    """Where the ink is: dense dark lines on skin -> edge energy, blurred, with a gentle centre bias."""
    g = gray.astype(np.float32)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    mag = cv2.magnitude(gx, gy)
    mag = cv2.GaussianBlur(mag, (0, 0), max(gray.shape) / 30)
    h, w = gray.shape
    yy, xx = np.mgrid[0:h, 0:w]
    bias = np.exp(-(((xx - w / 2) / (w * 0.6)) ** 2 + ((yy - h / 2) / (h * 0.6)) ** 2))
    return mag * (0.6 + 0.4 * bias)


def _best_crop(sal, aspect=9 / 16):
    """Best 9:16 window (fractions) over a saliency map, plus how much of the ink it keeps."""
    h, w = sal.shape
    total = sal.sum() + 1e-9
    if w / h > aspect:
        cw = int(round(h * aspect))
        col = sal.sum(0)
        cs = np.convolve(col, np.ones(cw), "valid")
        x = int(np.argmax(cs))
        return (x / max(1, w - cw) if w > cw else 0.5, 0.5), cs[x] / total
    ch = int(round(w / aspect))
    row = sal.sum(1)
    cs = np.convolve(row, np.ones(ch), "valid")
    y = int(np.argmax(cs))
    return (0.5, y / max(1, h - ch) if h > ch else 0.5), cs[y] / total


def _grade_png(src_png, dst_png):
    run(["ffmpeg", "-v", "error", "-y", "-i", src_png, "-vf", GRADE, dst_png])


def _prepare_image(it, tmpdir):
    img = ImageOps.exif_transpose(Image.open(it.path)).convert("RGB")
    it.w, it.h = img.size
    small = np.asarray(img.convert("L").resize((max(1, int(512 * img.width / max(img.size))),
                                                 max(1, int(512 * img.height / max(img.size))))))
    sal = _saliency(small)
    lap = cv2.Laplacian(small, cv2.CV_32F).var()
    it.sharp = float(math.log1p(lap))
    (fx, fy), kept = _best_crop(sal)
    if kept >= 0.72 or img.width / img.height < 0.75:
        # crop to 9:16 around the ink
        sw, sh = img.size
        if sw / sh > 9 / 16:
            cw, ch = int(sh * 9 / 16), sh
        else:
            cw, ch = sw, int(sw * 16 / 9)
        x0, y0 = int((sw - cw) * fx), int((sh - ch) * fy)
        crop = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((IMG_W, IMG_H), Image.LANCZOS)
        s2 = sal[int(y0 * small.shape[0] / sh): int((y0 + ch) * small.shape[0] / sh),
                 int(x0 * small.shape[1] / sw): int((x0 + cw) * small.shape[1] / sw)]
    else:
        # whole photo on a dark, blurred copy of itself (keeps wide pieces complete)
        it.fit = True
        bg = ImageOps.fit(img, (IMG_W // 8, IMG_H // 8)).resize((IMG_W, IMG_H), Image.BILINEAR)
        bg = Image.fromarray(cv2.GaussianBlur(np.asarray(bg), (0, 0), 40))
        bg = Image.eval(bg, lambda v: int(v * 0.28))
        fw = int(IMG_W * 0.94)
        fh = int(fw * img.height / img.width)
        if fh > IMG_H * 0.9:
            fh = int(IMG_H * 0.9)
            fw = int(fh * img.width / img.height)
        fg = img.resize((fw, fh), Image.LANCZOS)
        crop = bg.copy()
        crop.paste(fg, ((IMG_W - fw) // 2, (IMG_H - fh) // 2))
        s2 = None
    if s2 is not None and s2.size:
        yy, xx = np.mgrid[0:s2.shape[0], 0:s2.shape[1]]
        m = s2.sum() + 1e-9
        it.focus = (float((xx * s2).sum() / m / s2.shape[1]), float((yy * s2).sum() / m / s2.shape[0]))
    tmp = Path(tmpdir) / f"{it.id}.png"
    crop.save(tmp)
    out = cache_path("prepared", it.id, "png")
    _grade_png(tmp, out)
    tmp.unlink()
    it.file = str(out)


def _video_info(it):
    pr = probe(it.path)
    v = next(s for s in pr["streams"] if s.get("codec_type") == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = rot or int(v.get("tags", {}).get("rotate", 0) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    num, den = (v.get("avg_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    dur = float(v.get("duration") or pr["format"].get("duration") or 0)
    hdr = v.get("color_transfer") in ("arib-std-b67", "smpte2084")
    return w, h, fps, dur, hdr


def _prepare_video(it):
    w, h, fps, dur, hdr = _video_info(it)
    it.w, it.h, it.duration = w, h, dur
    it.fps = 60 if fps >= 50 else 30
    pre = (TONEMAP + ",") if hdr else ""

    # 1) low-res analysis pass
    s = 320 / max(w, h)
    aw, ah = max(2, int(w * s) // 2 * 2), max(2, int(h * s) // 2 * 2)
    raw = run(["ffmpeg", "-v", "error", "-i", it.path, "-vf", f"{pre}fps={ANA_FPS},scale={aw}:{ah}",
               "-f", "rawvideo", "-pix_fmt", "gray", "-"], binary=True)
    fr = np.frombuffer(raw, np.uint8).reshape(-1, ah, aw)
    if len(fr) < 2:
        raise RuntimeError(f"{Path(it.path).name}: video too short")
    win = cv2.createHanningWindow((aw, ah), cv2.CV_32F)
    sharp, shake, act, bright = [], [0.0], [0.0], []
    sal = np.zeros((ah, aw), np.float32)
    prev = None
    for f in fr:
        g = f.astype(np.float32)
        sharp.append(math.log1p(cv2.Laplacian(f, cv2.CV_32F).var()))
        bright.append(g.mean() / 255)
        if prev is not None:
            (dx, dy), _ = cv2.phaseCorrelate(prev, g, win)
            shake.append(math.hypot(dx, dy) / aw)
            M = np.float32([[1, 0, -dx], [0, 1, -dy]])
            comp = cv2.warpAffine(g, M, (aw, ah), borderMode=cv2.BORDER_REPLICATE)
            d = np.abs(comp - prev)
            act.append(float(d[8:-8, 8:-8].mean()) / 255)
            sal += cv2.GaussianBlur(d, (0, 0), 6)
        prev = g
    sal = sal / (sal.max() + 1e-9) + 0.5 * _saliency(fr[len(fr) // 2]) / (_saliency(fr[len(fr) // 2]).max() + 1e-9)
    sharp, shake, act, bright = map(np.array, (sharp, shake, act, bright))
    zs = (sharp - sharp.mean()) / (sharp.std() + 1e-9)
    pen = np.clip(shake / 0.02, 0, 2.5)
    score = 0.5 * zs - pen + 0.4 * np.clip(act / 0.03, 0, 1) - 1.5 * (bright < 0.1)
    score = np.convolve(score, np.ones(3) / 3, "same")
    it.scores = [round(float(v), 3) for v in score]
    it.sharp = float(np.median(sharp))
    it.activity = float(np.median(act))
    it.steady = float(1 - np.clip(np.median(shake) / 0.02, 0, 1))

    # 2) crop window around the action, then the proxy: rotated, SDR, 9:16, graded, constant fps
    (fx, fy), _ = _best_crop(sal)
    out = cache_path("prepared", it.id, "mp4")
    vf = (f"{pre}crop=w='min(iw,ih*9/16)':h='min(ih,iw*16/9)':x='(iw-ow)*{fx:.4f}':y='(ih-oh)*{fy:.4f}',"
          f"scale={W}:{H}:flags=lanczos,fps={it.fps},setsar=1,{GRADE},format=yuv420p,setpts=PTS-STARTPTS")
    run(["ffmpeg", "-v", "error", "-y", "-i", it.path, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "14", "-g", str(it.fps // 2), "-pix_fmt", "yuv420p", out])
    it.duration = float(probe(out)["format"]["duration"])
    it.file = str(out)


def scan(folder):
    folder = Path(folder)
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith("."))
    items = []
    for p in files:
        ext = p.suffix.lower()
        kind = "image" if ext in IMAGE_EXT else "video" if ext in VIDEO_EXT else None
        if kind:
            items.append(Item(id=file_key(p, f"media{VERSION}"), path=str(p), kind=kind,
                              role=_role(p, folder, kind), label=_label(p)))
    return items


def prepare(items, workers=4, tmpdir="/tmp"):
    def one(it):
        cp = cache_path("media", it.id, "json")
        c = load_json(cp)
        if c and Path(c.get("file", "")).exists():
            c.update(path=it.path, role=it.role, label=it.label)
            return Item(**{k: (tuple(v) if k == "focus" else v) for k, v in c.items()})
        log(f"preparing {Path(it.path).name}")
        try:
            (_prepare_video if it.kind == "video" else lambda x: _prepare_image(x, tmpdir))(it)
        except Exception as e:  # one bad file must not stop the batch
            log(f"  skipped {Path(it.path).name}: {str(e).splitlines()[0][:160]}")
            return None
        save_json(cp, asdict(it))
        return it

    with ThreadPoolExecutor(max_workers=workers) as ex:
        out = [x for x in ex.map(one, items) if x]
    # sharpness relative to the batch, 0..1, photos and videos ranked separately (measured differently)
    for kind in ("image", "video"):
        group = [x for x in out if x.kind == kind]
        if group:
            s = np.array([x.sharp for x in group])
            lo, hi = s.min(), s.max()
            for x in group:
                x.sharp = float((x.sharp - lo) / (hi - lo + 1e-9)) if hi > lo else 0.5
    return out


class Pool:
    """Hands out media to the styles, spreading use evenly across the batch."""

    def __init__(self, items, rng):
        self.items = items
        self.rng = rng
        self.uses = {it.id: 0 for it in items}
        self.spans = {it.id: [] for it in items}
        self.videos = [i for i in items if i.kind == "video"]
        self.images = [i for i in items if i.kind == "image"]

    def _pick(self, cands):
        m = min(self.uses[c.id] for c in cands)
        least = [c for c in cands if self.uses[c.id] <= m + 0]
        least.sort(key=lambda c: -c.sharp)
        top = least[: max(1, len(least) // 2 + 1)]
        return top[int(self.rng.integers(len(top)))]

    def take(self, need=0.0, kind=None, roles=None, exclude=()):
        """One shot's media. need = seconds of source footage the shot plays (videos)."""
        cands = [i for i in self.items if i.id not in exclude]
        if kind == "video" and any(c.kind == "video" for c in cands):
            cands = [c for c in cands if c.kind == "video"]
        elif kind == "image" and any(c.kind == "image" for c in cands):
            cands = [c for c in cands if c.kind == "image"]
        if roles:
            r = [c for c in cands if c.role in roles]
            cands = r or cands
        if not cands:
            cands = self.items
        it = self._pick(cands)
        self.uses[it.id] += 1
        start = 0.0
        if it.kind == "video":
            need = min(need, max(0.2, it.duration - 0.2))
            start = it.best_window(need, self.spans[it.id], self.rng)
            self.spans[it.id].append((start, start + need))
        return it, start

    def reveal(self, need=0.0):
        """The finished piece for the drop: tagged reveal/healed first, else the sharpest photo,
        else the steadiest video."""
        for roles in (("reveal",), ("healed",), ("work",)):
            c = [i for i in self.items if i.role in roles]
            if c:
                if roles == ("work",):
                    c = sorted(c, key=lambda i: -i.sharp)[:3]
                return self.take(need, roles=roles, exclude=[i.id for i in self.items if i not in c])
        vids = sorted(self.videos, key=lambda i: -(i.steady + i.sharp - i.activity * 5))
        if vids:
            return self.take(need, exclude=[i.id for i in self.items if i is not vids[0]])
        return self.take(need)
