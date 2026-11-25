"""
Styles turn a beat grid + media pool into a Plan: shots on beat boundaries, transitions, text.
Every boundary sits exactly on a beat (or half beat) of the song.
"""

import math
from dataclasses import dataclass, field

from . import music

CUT_KINDS = ("cut", "flash", "fade", "dip", "whip", "zoom", "glitch", "slide")


@dataclass
class Shot:
    item: object  # media.Item, None for the end card
    b0: float
    b1: float
    t0: float
    t1: float
    src: float = 0.0
    speed: tuple = (1.0, 1.0)  # playback speed at shot start, end (linear ramp)
    motion: str = "push"  # push pull pan_l pan_r pan_u pan_d punch drift still
    amount: float = 0.07
    bumps: bool = False  # zoom pulse on drum hits
    shake: bool = False  # shake on the shot's first beat
    glitch: bool = False  # RGB split on strong hits
    label: str = ""
    caption: str = ""
    end: bool = False


@dataclass
class Cut:
    kind: str
    dur: float = 0.0
    dir: int = 1


@dataclass
class Plan:
    style: str
    song: str
    song_start: float
    grid: object
    shots: list = field(default_factory=list)
    cuts: list = field(default_factory=list)
    hook: dict = field(default_factory=dict)
    cosmic: bool = False
    name: str = ""

    @property
    def duration(self):
        return self.grid.duration


def cut_dur(kind, g):
    return {"fade": min(g.beat * 0.75, 0.5), "dip": min(g.beat * 0.5, 0.36), "whip": 0.2, "zoom": 0.26,
            "glitch": 0.16, "slide": min(0.4, g.beat * 0.6)}.get(kind, 0.0)


class Builder:
    def __init__(self, plan, pool, rng, brand):
        self.p, self.g, self.pool, self.rng, self.brand = plan, plan.grid, pool, rng, brand
        self.beat = 0.0
        self.cursor = {}
        self._dir = 1

    def pick(self, seq):
        return seq[int(self.rng.integers(len(seq)))]

    def secs(self, n):
        return self.g.t(self.beat + n) - self.g.t(self.beat)

    def add(self, n, item=None, src=None, kind=None, roles=None, speed=(1.0, 1.0), cut="cut", **fx):
        dur = self.secs(n)
        avg = (speed[0] + speed[1]) / 2
        if item is None:
            item, src = self.pool.take(dur * avg + 0.5 * max(speed), kind=kind, roles=roles)
        if item.kind == "video":
            avail = item.duration - (src or 0) - 0.15
            need = dur * avg + 0.3 * max(speed)
            if avail > 0.1 and need > avail:
                k = avail / need
                speed = (max(0.25, speed[0] * k), max(0.25, speed[1] * k))
            if item.fps < 60:  # slower than real time judders on 30 fps footage
                speed = (max(1.0, speed[0]), max(1.0, speed[1]))
        else:
            speed = (1.0, 1.0)
        s = Shot(item=item, b0=self.beat, b1=self.beat + n, t0=self.g.t(self.beat), t1=self.g.t(self.beat + n),
                 src=float(src or 0.0), speed=speed, **fx)
        if self.p.shots:
            d = 1
            if cut == "whip":
                d, self._dir = self._dir, -self._dir
            self.p.cuts.append(Cut(cut, cut_dur(cut, self.g), d))
        self.p.shots.append(s)
        self.beat += n
        return s

    def reveal(self, n, cut="flash", **fx):
        item, src = self.pool.reveal(self.secs(n) + 0.5)
        fx.setdefault("motion", "push")
        fx.setdefault("amount", 0.11)
        return self.add(n, item=item, src=src, cut=cut, label=item.label, **fx)

    def continue_(self, item, n, speed=(1.0, 1.0), **fx):
        """Same clip, picking up where it left off (stutter edits)."""
        src = self.cursor.get(item.id)
        if src is None or src + self.secs(n) * max(speed) > item.duration - 0.2:
            src = item.best_window(self.secs(n) * max(speed) * 3, rng=self.rng)
        s = self.add(n, item=item, src=src, speed=speed, **fx)
        self.cursor[item.id] = src + self.secs(0) + (s.t1 - s.t0) * (speed[0] + speed[1]) / 2
        return s

    def end(self, cut="dip"):
        n = (len(self.g.beats) - 1) - self.beat
        s = Shot(item=None, b0=self.beat, b1=self.beat + n, t0=self.g.t(self.beat), t1=self.g.duration, end=True)
        self.p.cuts.append(Cut(cut, cut_dur(cut, self.g)))
        self.p.shots.append(s)
        self.beat += n

    def hook(self, text, mode="kinetic", until=8, step=1.0, y=0.40, size=150, tag=True):
        if text:
            self.p.hook = dict(text=text, mode=mode, until=until, step=step, y=y, size=size, tag=tag)

    def label_all(self):
        for s in self.p.shots:
            if s.item is not None and s.item.label and not s.label:
                s.label = s.item.label


# ---------------------------------------------------------------- the styles
# Each: (target seconds, window mode, builder function). Window mode decides which part of the song.

def punchy(b, content_bars, hook):
    g = b.g
    drop = g.drop if g.drop is not None and 1 <= g.drop <= content_bars - 2 else min(2, content_bars - 2)
    rev = 2 if content_bars - drop >= 4 else 1
    while b.beat < drop * 4:
        n = min(2, drop * 4 - b.beat)
        b.add(n, kind="video", roles=("process",), speed=b.pick([(3.0, 1.6), (2.5, 1.4), (4.0, 2.0)]),
              motion=b.pick(["push", "pan_l", "pan_r", "drift"]), amount=0.06)
    first = True
    pats = [[1, 1, 2], [2, 1, 1], [1, 1, 1, 1], [2, 2], [1, 2, 1]]
    while b.beat < (content_bars - rev) * 4:
        left = (content_bars - rev) * 4 - b.beat
        pat, acc = [], 0
        for n in b.pick(pats):
            if acc + n <= left:
                pat.append(n)
                acc += n
        pat = pat or [left]
        for j, n in enumerate(pat):
            b.add(n, kind=b.pick(["video", "video", None]), speed=b.pick([(2.0, 1.0), (1.5, 1.5), (3.0, 1.2)]),
                  motion=b.pick(["punch", "push", "pan_l", "pan_r"]), amount=0.08, bumps=True,
                  shake=first, cut="flash" if (first or j == 0) else b.pick(["cut", "cut", "glitch", "zoom"]))
            first = False
    b.reveal(rev * 4, cut="flash", bumps=True)
    b.end("dip")
    b.hook(hook, "kinetic", until=min(drop * 4, 8) or 4)


def build(b, content_bars, hook):
    g = b.g
    drop = g.drop if g.drop is not None and 2 <= g.drop <= content_bars - 2 else max(2, content_bars // 2)
    while b.beat < (drop - 1) * 4:
        b.add(4, kind="video", roles=("process", "studio", "artist"), speed=(1.4, 1.4),
              motion=b.pick(["push", "pull", "drift"]), amount=0.05, cut="fade")
    for n, sp in ((2, (2.0, 3.0)), (1, (3.0, 4.0)), (0.5, (4.0, 4.0)), (0.5, (4.0, 4.0))):
        b.add(n, kind="video", roles=("process",), speed=sp, motion="punch", amount=0.07)
    rev = min(8, (content_bars - drop) * 4 - (4 if content_bars - drop >= 3 else 0))
    b.reveal(rev, cut="flash", bumps=True, shake=True)
    while b.beat < content_bars * 4:
        n = min(b.pick([1, 2, 2]), content_bars * 4 - b.beat)
        b.add(n, kind="image", motion=b.pick(["punch", "pan_l", "pan_r"]), amount=0.08, bumps=True,
              cut="whip" if b.beat % 4 == 0 else "cut")
    b.end("dip")
    b.hook(hook, "static", until=min(4, (drop - 1) * 4) or 4)


def story(b, content_bars, hook):
    g = b.g
    per = max(1, math.ceil(4.0 / g.bar))  # long enough to read a line
    lines = list(b.brand.story_lines)
    i = 0
    while b.beat < (content_bars - per) * 4:
        s = b.add(per * 4, kind=b.pick(["video", "image"]), roles=("process", "studio", "artist", "work"),
                  speed=(0.5, 0.5), motion=b.pick(["push", "pull", "pan_l", "pan_r", "pan_u"]), amount=0.05,
                  cut="fade")
        if i < len(lines):
            s.caption = lines[i]
        i += 1
    b.reveal((content_bars * 4) - b.beat, cut="fade", amount=0.06)
    b.end("fade")
    b.label_all()


def gallery(b, content_bars, hook):
    g = b.g
    per = 1 if g.beat >= 0.42 else 2
    motions = ["punch", "pan_l", "push", "pan_r", "pull", "pan_u"]
    k = 0
    while b.beat < (content_bars - 1) * 4:
        b.add(per, kind="image", roles=("work", "reveal", "healed"), motion=motions[k % len(motions)],
              amount=0.08, bumps=True, cut="whip" if b.beat % 4 == 0 and b.beat else "cut")
        k += 1
    b.reveal(4, cut="flash")
    b.end("dip")
    b.label_all()
    b.hook(hook, "kinetic", until=4)


def stutter(b, content_bars, hook):
    for bar in range(content_bars - 1):
        a, _ = b.pool.take(3.0, kind="video")
        c, _ = b.pool.take(3.0, kind="video", exclude=[a.id])
        for h in range(8):
            b.continue_(a if h % 2 == 0 else c, 0.5, speed=(1.5, 1.5), motion="still", amount=0.04,
                        bumps=True, glitch=True, shake=h == 0, cut="glitch" if h == 0 and bar else "cut")
    b.reveal(4, cut="flash", shake=True, bumps=True)
    b.end("glitch")
    b.hook(hook, "kinetic", until=4, step=0.5)


def cosmic(b, content_bars, hook):
    b.p.cosmic = True
    g = b.g
    per = 2 if g.beat >= 0.5 else 4
    while b.beat < (content_bars - 1) * 4:
        n = min(per, (content_bars - 1) * 4 - b.beat)
        b.add(n, kind=b.pick(["image", "image", "video"]), roles=("work", "reveal", "healed", "process"),
              speed=(1.0, 1.0), motion=b.pick(["push", "pull", "drift"]), amount=0.05, cut="slide")
    b.reveal(4, cut="slide", amount=0.06)
    b.end("dip")
    b.label_all()
    b.hook(hook, "static", until=4, y=0.155, size=104, tag=False)


STYLES = {
    #          target s, window, fn, needs
    "punchy": (15, ("drop", 0.25), punchy),
    "build": (18, ("drop", 0.45), build),
    "story": (20, "mid", story),
    "gallery": (12, "high", gallery),
    "stutter": (10, "high", stutter),
    "cosmic": (14, "mid", cosmic),
}


def plan(style, song_path, analysis, pool, rng, brand, hook="", used_windows=(), length=None):
    target, mode, fn = STYLES[style]
    target = length or target
    bars = music.np.array(analysis["bars"])
    bar_len = float(music.np.median(music.np.diff(bars)))
    content = max(3, int(round(target / bar_len)))
    end_bars = max(1, math.ceil(2.2 / bar_len))
    total = content + end_bars
    if isinstance(mode, tuple):
        mode = ("drop", mode[1] * content / total)
    start_bar = music.pick_window(analysis, total, mode, rng, used_windows)
    start_bar = min(start_bar, max(0, len(bars) - 1 - total))
    total = min(total, len(bars) - 1 - start_bar)
    content = max(2, total - end_bars)
    grid = music.Grid(analysis, start_bar, total)
    p = Plan(style=style, song=str(song_path), song_start=grid.start, grid=grid)
    fn(Builder(p, pool, rng, brand), content, hook)
    return p, start_bar
