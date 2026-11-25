"""
Frame-by-frame renderer. Builds every frame of a Plan in numpy/OpenCV and pipes it to ffmpeg with the
song excerpt. A shot boundary at beat time T appears on frame round(T * 30): at most half a frame
(16.7 ms) from the beat.
"""

import math
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from . import overlays as ov
from .util import FPS, H, W, log, run

FRAME_BYTES = W * H * 3
CARD = (142, 400, 796, 1062)  # cosmic style photo card (x, y, w, h), 3:4


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


class VideoReader:
    """Sequential reader of a prepared proxy. Re-opens (accurate seek) only when asked to jump."""

    def __init__(self, item):
        self.it = item
        self.proc = None
        self.idx = -1
        self.frame = None
        self.n = max(1, int(item.duration * item.fps) - 1)

    def _open(self, i):
        self.close()
        ss = max(0.0, (i - 0.5) / self.it.fps)
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}", "-i", self.it.file, "-f", "rawvideo", "-pix_fmt", "bgr24",
             "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=FRAME_BYTES * 2)
        self.idx = i - 1

    def get(self, t):
        i = min(max(0, int(round(t * self.it.fps))), self.n)
        if self.proc is None or i < self.idx or i > self.idx + 120:
            self._open(i)
        while self.idx < i:
            buf = self.proc.stdout.read(FRAME_BYTES)
            if len(buf) < FRAME_BYTES:  # end of clip: hold the last frame
                self.idx = i
                break
            self.frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            self.idx += 1
        if self.frame is None:
            self.frame = np.zeros((H, W, 3), np.uint8)
        return self.frame

    def close(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc = None


class Renderer:
    def __init__(self, plan, brand, seed=0):
        self.p, self.brand, self.g = plan, brand, plan.grid
        self.rng = np.random.default_rng(seed)
        self.readers, self.images = {}, {}
        self.hits = [(t, s) for t, s in self.g.hits]
        self.strong = [t for t, s in self.g.hits if s >= 0.6]
        self.end_img = None
        if plan.cosmic:
            # big eclipse behind the card: its rim and corona show around the card's sides
            sb = ov.space_bg(brand, seed=11, scale=1.08, eclipse=(0.5, 0.485, 470), stars=520)
            self.space = np.ascontiguousarray(np.asarray(sb.convert("RGB"))[..., ::-1])
            self.card_frame = ov.card_frame(brand, CARD)
        self._texts()

    # ------------------------------------------------------------ sources
    def source(self, shot, t):
        it = shot.item
        if it.kind == "image":
            if it.id not in self.images:
                self.images[it.id] = cv2.imread(it.file, cv2.IMREAD_COLOR)
            return self.images[it.id]
        r = self.readers.get(id(shot))
        if r is None:
            r = self.readers[id(shot)] = VideoReader(it)
        dt = t - shot.t0
        D = max(1e-3, shot.t1 - shot.t0)
        s0, s1 = shot.speed
        u = min(max(dt / D, 0.0), 1.0)
        st = D * (s0 * u + (s1 - s0) * u * u / 2)  # integral of a linear speed ramp
        if dt < 0:
            st = dt * s0
        elif dt > D:
            st += (dt - D) * s1
        return r.get(max(0.0, shot.src + st))

    def release(self, shot):
        r = self.readers.pop(id(shot), None)
        if r:
            r.close()

    # ------------------------------------------------------------ one shot at time t
    def shot_frame(self, shot, t):
        ow, oh = (CARD[2], CARD[3]) if self.p.cosmic and not shot.end else (W, H)
        if shot.end:
            return self.end_frame(shot, t)
        src = self.source(shot, t)
        sh, sw = src.shape[:2]
        D = max(1e-3, shot.t1 - shot.t0)
        u = min(max((t - shot.t0) / D, 0.0), 1.0)
        a = shot.amount
        z, px, py = 1.0, 0.0, 0.0
        m = shot.motion
        if m == "push":
            z = 1 + a * u
        elif m == "pull":
            z = 1 + a * (1 - u)
        elif m in ("pan_l", "pan_r"):
            z = 1 + a + 0.03
            px = (-1 + 2 * u) * (1 if m == "pan_r" else -1)
        elif m in ("pan_u", "pan_d"):
            z = 1 + a + 0.03
            py = (-1 + 2 * u) * (1 if m == "pan_d" else -1)
        elif m == "punch":
            z = 1 + a * ease_out((t - shot.t0) / 0.18) + a * 0.25 * u
        elif m == "drift":
            z = 1 + a * 0.6 + a * 0.3 * u
            px = 0.35 * math.sin(2.2 * u + shot.b0)
        else:
            z = 1 + a * 0.3
        rot, ox, oy = 0.0, 0.0, 0.0
        if shot.bumps:
            th = [h for h, s in self.hits if shot.t0 - 1e-3 <= h <= t]
            if th:
                z *= 1 + 0.045 * math.exp(-(t - th[-1]) / 0.08)
        if shot.shake and t >= shot.t0:
            e = math.exp(-(t - shot.t0) / 0.12)
            ph = (t - shot.t0) * 2 * math.pi * 13
            ox, oy, rot = 18 * e * math.sin(ph), 12 * e * math.cos(ph * 1.3), 0.8 * e * math.sin(ph * 0.7)
        s0 = max(ow / sw, oh / sh)
        S = s0 * z
        fx, fy = shot.item.focus if m in ("push", "punch") else (0.5, 0.5)
        k = min(1.0, (z - 1) / 0.12) * 0.6
        cx = (0.5 + (fx - 0.5) * k) * sw
        cy = (0.5 + (fy - 0.5) * k) * sh
        hw, hh = ow / (2 * S), oh / (2 * S)
        cx += px * max(0.0, sw / 2 - hw) * 0.85
        cy += py * max(0.0, sh / 2 - hh) * 0.85
        cx = min(max(cx, hw), sw - hw)
        cy = min(max(cy, hh), sh - hh)
        M = np.float32([[S, 0, ow / 2 - S * cx + ox], [0, S, oh / 2 - S * cy + oy]])
        if rot:
            R = cv2.getRotationMatrix2D((ow / 2, oh / 2), rot, 1.0)
            M = (np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]))[:2].astype(np.float32)
        out = cv2.warpAffine(src, M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if shot.glitch:
            th = [h for h in self.strong if shot.t0 - 1e-3 <= h <= t and t - h < 0.09]
            if th:
                d = int(16 * (1 - (t - th[-1]) / 0.09)) + 2
                out = out.copy()
                out[:, d:, 2] = out[:, :-d, 2]
                out[:, :-d, 0] = out[:, d:, 0]
        return out

    def end_frame(self, shot, t):
        if self.end_img is None:
            self.end_img = ov.end_card(self.brand)
        u = min(max((t - shot.t0) / max(1e-3, shot.t1 - shot.t0), 0.0), 1.0)
        img = self.end_img
        sh, sw = img.shape[:2]
        S = (W / sw) * (1.0 + 0.045 * u)
        M = np.float32([[S, 0, W / 2 - S * sw / 2], [0, S, H / 2 - S * sh / 2]])
        out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
        fade = min(1.0, max(0.0, (t - shot.t0) / 0.25)) if not self.p.cuts or self.p.cuts[-1].kind == "cut" else 1.0
        return out if fade >= 1 else (out * fade).astype(np.uint8)

    # ------------------------------------------------------------ cosmic card style
    def cosmic_bg(self, t):
        sh, sw = self.space.shape[:2]
        S = W / sw * (1 + 0.03 * t / max(1, self.p.duration))
        dx = 18 * math.sin(t * 0.25)
        M = np.float32([[S, 0, W / 2 - S * sw / 2 + dx], [0, S, H / 2 - S * sh / 2]])
        return cv2.warpAffine(self.space, M, (W, H), flags=cv2.INTER_LINEAR)

    def compose_cards(self, t, cards):
        """cards: list of (card_bgr, dy, opacity)."""
        frame = self.cosmic_bg(t).copy()
        x, y, w, h = CARD
        for img, dy, op in cards:
            if op <= 0:
                continue
            self.card_frame.draw(frame, op, dy=dy)
            if op >= 0.999 and dy == 0:
                frame[y:y + h, x:x + w] = img
            else:
                ov.Layer(x, y, img.astype(np.float32) * op, np.full((h, w, 1), op, np.float32)).draw(frame, 1.0, dy=dy)
        return frame

    # ------------------------------------------------------------ text
    def _texts(self):
        self.text_items = []  # (layer, t_in, t_out, kind)
        hk = self.p.hook
        if hk:
            words, tag, band = ov.hook_words(self.brand, hk["text"], y_frac=hk.get("y", 0.4),
                                             size=hk.get("size", 150), tag=hk.get("tag", True))
            t_end = self.g.t(hk["until"])
            self.text_items.append((band, 0.0, t_end, "fade"))
            self.text_items.append((tag, 0.0, t_end, "fade"))
            for i, wl in enumerate(words):
                tin = self.g.t(i * hk["step"]) if hk["mode"] == "kinetic" else 0.05
                if tin < t_end - 0.1:
                    self.text_items.append((wl, tin, t_end, "pop" if hk["mode"] == "kinetic" else "fade"))
        for s in self.p.shots:
            if s.label:
                self.text_items.append((ov.label(self.brand, s.label), s.t0 + 0.05, s.t1 - 0.05, "fade"))
            if s.caption:
                lay, band = ov.caption(self.brand, s.caption)
                self.text_items.append((band, s.t0 + 0.1, s.t1 - 0.1, "fade"))
                self.text_items.append((lay, s.t0 + 0.2, s.t1 - 0.15, "fade"))

    def draw_texts(self, frame, t):
        for lay, a, b, kind in self.text_items:
            if lay is None or t < a or t > b:
                continue
            fi = 0.12 if kind == "pop" else 0.2
            op = min(1.0, (t - a) / fi, (b - t) / 0.18)
            dy = 26 * (1 - ease_out((t - a) / fi)) if kind == "pop" else 0
            lay.draw(frame, max(0.0, op), dy=dy)

    # ------------------------------------------------------------ transitions
    @staticmethod
    def blend(A, B, p):
        return cv2.addWeighted(A, 1 - p, B, p, 0)

    def transition(self, cut, A, B, p, t):
        k = cut.kind
        if k == "fade":
            return self.blend(A, B, ease_io(p))
        if k == "dip":
            return (A * (1 - 2 * p)).astype(np.uint8) if p < 0.5 else (B * (2 * p - 1)).astype(np.uint8)
        if k == "whip":
            e = ease_io(p)
            strip = np.hstack([A, B]) if cut.dir > 0 else np.hstack([B, A])
            x = int(e * W) if cut.dir > 0 else int((1 - e) * W)
            out = np.ascontiguousarray(strip[:, x:x + W])
            kb = int(90 * math.sin(math.pi * p)) | 1
            return cv2.blur(out, (kb, 1)) if kb > 2 else out
        if k == "zoom":
            e = ease_io(p)
            za, zb = 1 + 0.6 * e, 1.35 - 0.35 * e
            def zoom(img, z):
                M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
                return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
            out = self.blend(zoom(A, za), zoom(B, zb), e)
            kb = int(30 * math.sin(math.pi * p)) | 1
            return cv2.GaussianBlur(out, (kb, kb), 0) if kb > 2 else out
        if k == "glitch":
            out = (A if p < 0.5 else B).copy()
            d = int(40 * (1 - abs(2 * p - 1))) + 1
            out[:, d:, 2] = out[:, :-d, 2]
            out[:, :-d, 0] = out[:, d:, 0]
            for _ in range(5):
                y0 = int(self.rng.integers(0, H - 80))
                hh = int(self.rng.integers(20, 120))
                out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(self.rng.integers(-80, 80)), axis=1)
            return out
        return B if p >= 0.5 else A

    # ------------------------------------------------------------ main loop
    def frames(self):
        shots, cuts = self.p.shots, self.p.cuts
        N = int(round(self.p.duration * FPS))
        starts = [int(round(s.t0 * FPS)) for s in shots] + [N]
        # transition windows in frames, clamped to the neighbouring shots
        wins = []
        for j, c in enumerate(cuts):
            T = starts[j + 1]
            lim = 0.8 * min(starts[j + 1] - starts[j], starts[j + 2] - starts[j + 1]) / FPS
            d = min(c.dur, lim)
            half = int(round(d * FPS / 2))
            wins.append((T - half, T + half) if half > 0 else (T, T))
        flashes = [shots[j + 1].t0 for j, c in enumerate(cuts) if c.kind == "flash"]
        thumbs = {}
        si = 0
        for f in range(N):
            t = f / FPS
            while si + 1 < len(shots) and f >= starts[si + 1]:
                self.release(shots[si - 1]) if si > 0 else None
                si += 1
            frame = None
            for j, (a, b) in enumerate(wins):
                if a <= f < b and b > a:
                    p = (f - a + 0.5) / (b - a)
                    A_s, B_s = shots[j], shots[j + 1]
                    if self.p.cosmic and not B_s.end and not A_s.end and cuts[j].kind == "slide":
                        e = ease_io(p)
                        frame = self.compose_cards(t, [
                            (self.shot_frame(A_s, t), -220 * e, 1 - e),
                            (self.shot_frame(B_s, t), 260 * (1 - e), e)])
                    else:
                        A = self._full(A_s, t)
                        B = self._full(B_s, t)
                        frame = self.transition(cuts[j], A, B, p, t)
                    break
            if frame is None:
                frame = self._full(shots[si], t)
            frame = np.ascontiguousarray(frame)
            for T in flashes:
                if 0 <= t - T < 0.3:
                    a = 0.85 * math.exp(-(t - T) / 0.07)
                    frame = cv2.addWeighted(frame, 1 - a, np.full_like(frame, 255), a, 0)
            if not shots[si].end:
                self.draw_texts(frame, t)
            mid = (starts[si] + starts[si + 1]) // 2
            if f == mid:
                thumbs[si] = cv2.resize(frame, (180, 320), interpolation=cv2.INTER_AREA)
            yield frame
        for s in shots:
            self.release(s)
        self.thumbs = [thumbs[k] for k in sorted(thumbs)]

    def _full(self, shot, t):
        if self.p.cosmic and not shot.end:
            return self.compose_cards(t, [(self.shot_frame(shot, t), 0, 1.0)])
        return self.shot_frame(shot, t)


def render(plan, brand, out_path, seed=0):
    out_path = Path(out_path)
    g = plan.grid
    dur = g.duration
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        # sample-accurate excerpt (atrim), short fade-in against clicks, fade-out over the end card
        run(["ffmpeg", "-v", "error", "-y", "-i", plan.song, "-af",
             f"atrim=start={plan.song_start:.5f}:duration={dur:.5f},asetpts=PTS-STARTPTS,"
             f"afade=t=in:st=0:d=0.012,afade=t=out:st={max(0.0, dur - 1.4):.3f}:d=1.4",
             "-ar", "48000", "-ac", "2", wav])
        enc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
             "-i", "-", "-i", str(wav), "-vf", "vignette=angle=PI/5,noise=alls=3:allf=t,format=yuv420p",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
             "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
             str(out_path)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        r = Renderer(plan, brand, seed)
        try:
            for fr in r.frames():
                enc.stdin.write(fr.tobytes())
        finally:
            enc.stdin.close()
            err = enc.stderr.read().decode(errors="replace")
            enc.wait()
        if enc.returncode != 0:
            raise RuntimeError(f"encoder failed for {out_path.name}: {err[-1500:]}")
    silent = out_path.with_name(out_path.stem + "-silent.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", out_path, "-c:v", "copy", "-an", "-movflags", "+faststart", silent])
    return r.thumbs
