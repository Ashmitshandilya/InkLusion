"""Shared helpers: paths, ffmpeg calls, cache keys, logging."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # reels/
CACHE = ROOT / "cache"
FONTS = ROOT / "fonts"
W, H, FPS = 1080, 1920, 30

# Natural skin, deep blacks, slight cool-magenta in the shadows only. Applied once, when media is prepared.
GRADE = (
    "eq=contrast=1.08:brightness=-0.012:saturation=0.94,"
    "curves=all='0/0 0.08/0.05 0.5/0.5 0.92/0.95 1/1',"
    "colorbalance=rs=0.015:bs=0.035,"
    "unsharp=5:5:0.45:5:5:0"
)

# iPhones film HDR (HLG / Dolby Vision) by default; without tone-mapping it looks grey. 203-nit reference
# white (BT.2408) + mobius roll-off measured within 5 % of the SDR original on a test clip.
TONEMAP = (
    "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=tonemap=mobius:param=0.3:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)


def run(cmd, binary=False):
    r = subprocess.run([str(c) for c in cmd], capture_output=True)
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace")[-2500:]
        raise RuntimeError(f"command failed: {' '.join(map(str, cmd))[:300]}\n{err}")
    return r.stdout if binary else r.stdout.decode(errors="replace")


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(out)


def file_key(path, salt=""):
    p = Path(path)
    st = p.stat()
    return hashlib.sha1(f"{p.name}:{st.st_size}:{st.st_mtime_ns}:{salt}".encode()).hexdigest()[:16]


def cache_path(kind, key, ext):
    d = CACHE / kind
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.{ext}"


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=1))


_T0 = time.time()


def log(msg):
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True, file=sys.stderr)


def fmt_time(t):
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m)}:{s:06.3f}"
