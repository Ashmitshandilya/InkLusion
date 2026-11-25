#!/usr/bin/env python3
"""
InkLusion reel editor. Cuts phone footage into 1080x1920 Reels, timed to a song's beat.

    python3 reels/reel.py auto reels/raw/session1 --bpm 92 --style punchy --hook "4 hours." --out farzi-1
    python3 reels/reel.py render reels/specs/farzi-1.json

`auto` writes a spec (reels/specs/<out>.json) from a folder of clips and renders it.
Edit the spec (which clip, where, how many beats, speed) and run `render` again.
The last clip in the folder (by name) is treated as the reveal.

Music is NOT put in the file. Add the song inside Instagram (licensed there), start it on a
beat, and the cuts land on the beat. Use --preview-audio song.mp3 for a private check copy.

Needs: ffmpeg, ffprobe, Pillow.
"""

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
W, H, FPS = 1080, 1920, 30
NEON = (255, 43, 214)
INK = (244, 238, 242)
MUTED = (160, 150, 158)

# Reels UI covers the top ~220px, bottom ~380px and a strip on the right. Keep text inside.
SAFE_X, SAFE_BOTTOM = 84, 400

STUDIO = "INKLUSION  ·  ROORKEE"
END_LINE = "Book on WhatsApp  ·  63983 30495"
END_HANDLE = "@inklusiontattoo___"

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".3gp", ".avi"}

# Natural skin, deep blacks, slight cool-magenta in the shadows only.
GRADE = (
    "eq=contrast=1.08:brightness=-0.012:saturation=0.94,"
    "curves=all='0/0 0.08/0.05 0.5/0.5 0.92/0.95 1/1',"
    "colorbalance=rs=0.015:bs=0.035:rm=0:bm=0,"
    "unsharp=5:5:0.45:5:5:0"
)


# ---------------------------------------------------------------- helpers

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{' '.join(map(str, cmd))}\n{r.stderr[-2500:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(out)["format"]["duration"])


def is_hdr(path):
    """iPhones film HDR (HLG / Dolby Vision) by default; it looks grey unless tone-mapped."""
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
               "-of", "csv=p=0", str(path)])
    return out.strip() in ("arib-std-b67", "smpte2084")


TONEMAP = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


SERIF = "InstrumentSerif-Regular.woff"
SERIF_I = "InstrumentSerif-Italic.woff"
MONO = "GeistMono-Regular.ttf"
SANS = "Geist-Regular.ttf"


def spaced(text, size, tracking=0.22):
    """Mono label with letter spacing, as on the site."""
    f = font(MONO, size)
    gap = size * tracking
    widths = [f.getlength(c) for c in text]
    return f, gap, sum(widths) + gap * (len(text) - 1)


def draw_spaced(d, xy, text, size, fill, tracking=0.22):
    f, gap, _ = spaced(text, size, tracking)
    x, y = xy
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + gap


def glow(layer, radius=22, strength=1.6):
    """Neon glow: blurred copy of the layer under itself."""
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    r, g, b, a = blur.split()
    a = a.point(lambda v: min(255, int(v * strength)))
    blur = Image.merge("RGBA", (r, g, b, a))
    out = Image.new("RGBA", layer.size)
    out.alpha_composite(blur)
    out.alpha_composite(layer)
    return out


def wrap(text, f, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        t = f"{line} {w}".strip()
        if f.getlength(t) <= max_w or not line:
            line = t
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


# ---------------------------------------------------------------- overlays (PNG)

def hook_png(path, text, sub=""):
    """Big serif hook line, centred a little above middle, mono studio label above it."""
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    big = font(SERIF_I, 150)
    lines = wrap(text, big, W - 2 * SAFE_X)
    lh = 150
    block = lh * len(lines) + (90 if sub else 0)
    y0 = int(H * 0.42 - block / 2)

    _, _, lw = spaced(STUDIO, 26)
    draw_spaced(d, ((W - lw) / 2, y0 - 70), STUDIO, 26, MUTED + (255,))

    neon = Image.new("RGBA", (W, H))
    nd = ImageDraw.Draw(neon)
    for i, ln in enumerate(lines):
        x = (W - big.getlength(ln)) / 2
        nd.text((x, y0 + i * lh), ln, font=big, fill=INK + (255,))
    img.alpha_composite(glow(neon, 26, 0.9))
    if sub:
        sf = font(SERIF, 84)
        x = (W - sf.getlength(sub)) / 2
        s = Image.new("RGBA", (W, H))
        ImageDraw.Draw(s).text((x, y0 + len(lines) * lh + 10), sub, font=sf, fill=NEON + (255,))
        img.alpha_composite(glow(s, 20, 1.4))
    # soft dark band behind the text so it reads on bright skin
    shade = Image.new("RGBA", (W, H))
    ImageDraw.Draw(shade).rectangle((0, y0 - 140, W, y0 + block + 80), fill=(0, 0, 0, 120))
    shade = shade.filter(ImageFilter.GaussianBlur(70))
    shade.alpha_composite(img)
    shade.save(path)


def label_png(path, text):
    """Small mono caption bottom-left with a neon dot, inside the Reels safe area."""
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    y = H - SAFE_BOTTOM - 40
    dot = Image.new("RGBA", (W, H))
    ImageDraw.Draw(dot).ellipse((SAFE_X, y + 9, SAFE_X + 12, y + 21), fill=NEON + (255,))
    img.alpha_composite(glow(dot, 8, 2))
    sh = Image.new("RGBA", (W, H))
    draw_spaced(ImageDraw.Draw(sh), (SAFE_X + 30, y + 2), text.upper(), 28, (0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(sh)
    draw_spaced(d, (SAFE_X + 30, y), text.upper(), 28, INK + (255,))
    img.save(path)


def end_card_png(path, line=END_LINE, handle=END_HANDLE):
    """Black space, stars and the eclipse from the website, with the wordmark."""
    rnd = random.Random(7)
    S = 1.12  # drawn larger so a slow push-in has room
    cw, ch = int(W * S), int(H * S)
    bg = Image.new("RGBA", (cw, ch), (5, 5, 5, 255))

    neb = Image.new("RGBA", (cw, ch))
    nd = ImageDraw.Draw(neb)
    for _ in range(26):
        x, y = rnd.gauss(cw * 0.55, cw * 0.28), rnd.gauss(ch * 0.33, ch * 0.16)
        r = rnd.uniform(120, 340)
        c = NEON if rnd.random() < 0.6 else (92, 46, 242)
        nd.ellipse((x - r, y - r, x + r, y + r), fill=c + (rnd.randint(10, 28),))
    bg.alpha_composite(neb.filter(ImageFilter.GaussianBlur(120)))

    stars = Image.new("RGBA", (cw, ch))
    sd = ImageDraw.Draw(stars)
    for _ in range(420):
        x, y, r = rnd.uniform(0, cw), rnd.uniform(0, ch), rnd.choice([0.8, 1, 1, 1.4, 2])
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(240, 225, 255, rnd.randint(90, 230)))
    bg.alpha_composite(stars)

    # eclipse: corona, bright rim, black disc
    cx, cy, R = cw * 0.5, ch * 0.33, 230
    cor = Image.new("RGBA", (cw, ch))
    cd = ImageDraw.Draw(cor)
    for k, a in ((1.6, 55), (1.32, 95), (1.15, 170)):
        cd.ellipse((cx - R * k, cy - R * k, cx + R * k, cy + R * k), fill=NEON + (a,))
    bg.alpha_composite(cor.filter(ImageFilter.GaussianBlur(70)))
    rim = Image.new("RGBA", (cw, ch))
    ImageDraw.Draw(rim).ellipse((cx - R - 7, cy - R - 7, cx + R + 7, cy + R + 7), fill=(255, 215, 248, 255))
    bg.alpha_composite(rim.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(bg).ellipse((cx - R, cy - R, cx + R, cy + R), fill=(0, 0, 0, 255))

    # wordmark
    a, b = font(SERIF, 230), font(SERIF_I, 230)
    wa, wb = a.getlength("Ink"), b.getlength("Lusion")
    x = (cw - wa - wb) / 2
    y = ch * 0.53
    t = Image.new("RGBA", (cw, ch))
    td = ImageDraw.Draw(t)
    td.text((x, y), "Ink", font=a, fill=INK + (255,))
    n = Image.new("RGBA", (cw, ch))
    ImageDraw.Draw(n).text((x + wa, y), "Lusion", font=b, fill=NEON + (255,))
    t.alpha_composite(glow(n, 30, 1.5))
    bg.alpha_composite(t)

    d = ImageDraw.Draw(bg)
    tag = "TATTOO STUDIO  ·  ROORKEE"
    _, _, lw = spaced(tag, 30)
    draw_spaced(d, ((cw - lw) / 2, y - 40), tag, 30, MUTED + (255,))
    sf = font(SANS, 46)
    d.text(((cw - sf.getlength(line)) / 2, y + 330), line, font=sf, fill=INK + (235,))
    _, _, hw = spaced(handle, 28, 0.12)
    draw_spaced(d, ((cw - hw) / 2, y + 410), handle, 28, NEON + (255,), 0.12)
    bg.convert("RGB").save(path)


# ---------------------------------------------------------------- render

def frames_for(segs, beat):
    """Frame count per segment from cumulative beat times, so cuts never drift off the beat."""
    t, out = 0.0, []
    for s in segs:
        a, t = round(t * FPS), t + s["beats"] * beat
        out.append(round(t * FPS) - a)
    return out


def render_segment(seg, n_frames, beat, out):
    dur = n_frames / FPS
    speed = float(seg.get("speed", 1))
    src_len = dur * speed
    total = probe(seg["src"])
    at = max(0.0, min(float(seg.get("at", 0)), total - src_len - 0.05))
    if total < src_len:  # clip too short for this speed: slow it to fit
        speed, at = max(0.25, total / dur * 0.98), 0.0

    T = "(t)"
    if seg.get("push"):  # slow push-in over the whole shot
        z = f"(1+0.07*{T}/{dur:.3f})"
    elif seg.get("punch"):  # jump closer on the second half, on the beat
        z = f"(1+0.13*gte({T},{min(beat, dur / 2):.3f}))"
    else:
        z = "1"

    vf = [TONEMAP] if is_hdr(seg["src"]) else []
    vf += [
        f"setpts=(PTS-STARTPTS)/{speed}",
        f"fps={FPS}",
        f"scale=w='ceil({W}*{z}/2)*2':h='ceil({H}*{z}/2)*2':force_original_aspect_ratio=increase:eval=frame",
        f"crop={W}:{H}",
        "setsar=1",
        GRADE,
    ]
    if seg.get("flash"):
        vf.append("fade=t=in:st=0:d=0.13:color=white")
    run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-t", f"{src_len + 0.5:.3f}", "-i", seg["src"],
        "-vf", ",".join(vf), "-frames:v", str(n_frames), "-an",
        "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", str(out),
    ])


def render_card(png, n_frames, out):
    dur = n_frames / FPS
    z = f"(1+0.06*t/{dur:.3f})"
    run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
        "-vf", (
            f"scale=w='ceil({W}*{z}/2)*2':h='ceil({H}*{z}/2)*2':force_original_aspect_ratio=increase:eval=frame,"
            f"crop={W}:{H},setsar=1,"
            f"fade=t=in:st=0:d=0.35:color=black"
        ),
        "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "medium", "-crf", "15",
        "-pix_fmt", "yuv420p", str(out),
    ])


def render(spec_path, preview_audio=None):
    spec = json.loads(Path(spec_path).read_text())
    beat = 60.0 / float(spec["bpm"])
    segs = spec["segments"]
    end = spec.get("end", {"beats": 4})
    allsegs = segs + ([{"beats": end["beats"], "card": True}] if end else [])
    frames = frames_for(allsegs, beat)

    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    name = spec.get("name", Path(spec_path).stem)
    tmp = Path(tempfile.mkdtemp(prefix="reel-"))
    try:
        parts = []
        for i, (s, n) in enumerate(zip(allsegs, frames)):
            p = tmp / f"s{i:02d}.mp4"
            if s.get("card"):
                png = tmp / "end.png"
                end_card_png(png, end.get("line", END_LINE), end.get("handle", END_HANDLE))
                render_card(png, n, p)
            else:
                render_segment(s, n, beat, p)
            parts.append(p)
            print(f"  cut {i + 1}/{len(allsegs)}  {n / FPS:5.2f}s", flush=True)

        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

        # overlays: hook on the first cuts, labels on their segments
        inputs, chains, last, k = [], [], "[0:v]", 1
        starts = [sum(frames[:i]) / FPS for i in range(len(frames))]
        overlays = []
        if spec.get("hook"):
            hp = tmp / "hook.png"
            hook_png(hp, spec["hook"], spec.get("hook_sub", ""))
            hold = min(sum(frames[:-1]) / FPS, max(1.6, spec.get("hook_beats", 4) * beat))
            overlays.append((hp, 0.0, hold))
        for i, s in enumerate(segs):
            if s.get("label"):
                lp = tmp / f"label{i}.png"
                label_png(lp, s["label"])
                overlays.append((lp, starts[i], frames[i] / FPS))
        for png, st, d in overlays:
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{st + d:.3f}", "-i", str(png)]
            fi = min(0.18, d / 4)
            chains.append(
                f"[{k}:v]format=rgba,fade=t=in:st={st:.3f}:d={fi:.3f}:alpha=1,"
                f"fade=t=out:st={st + d - fi:.3f}:d={fi:.3f}:alpha=1[o{k}]"
            )
            chains.append(f"{last}[o{k}]overlay=0:0:eof_action=pass[v{k}]")
            last, k = f"[v{k}]", k + 1
        chains.append(f"{last}vignette=angle=PI/5,noise=alls=3:allf=t,format=yuv420p[vout]")

        total = sum(frames) / FPS
        final = out_dir / f"{name}.mp4"
        common = [
            "-filter_complex", ";".join(chains), "-map", "[vout]",
            # ~16 Mbps cap: sharp after Instagram's re-encode, still quick to upload from a phone
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
        ]
        # posting copy: silent track, add the song in Instagram
        run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), *inputs,
             "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
             *common, "-map", f"{k}:a", "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.3f}", str(final)])
        print(f"  -> {final}  ({total:.1f}s, {len(allsegs)} cuts, {spec['bpm']} bpm)")

        if preview_audio:
            prev = out_dir / f"{name}.preview.mp4"
            a_at = float(spec.get("song_start", 0))
            run(["ffmpeg", "-y", "-v", "error", "-i", str(final), "-ss", f"{a_at:.3f}", "-i", str(preview_audio),
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-af", f"afade=t=out:st={total - 0.8:.3f}:d=0.8", "-t", f"{total:.3f}", str(prev)])
            print(f"  -> {prev}  (private check copy with the song, do not post)")
        return final
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- auto specs

STYLES = {
    # punchy: 1-2 beat hard cuts, sped-up process, flash every 4th cut, reveal on the drop
    "punchy": dict(pattern=[2, 1, 1, 2, 1, 1, 2, 2], speed=[3, 4, 2], punch_every=2, flash_every=4, reveal=8),
    # build: long calm shots, then fast cuts, flash into the reveal
    "build": dict(pattern=[4, 4, 4, 2, 1, 1, 1, 1], speed=[1.5, 2, 3], punch_every=0, flash_every=0, reveal=8,
                  push_first=3),
    # calm: slow, 4-beat shots with slow push-ins, for story / studio / healed work
    "calm": dict(pattern=[4, 4, 4, 4, 4], speed=[1, 1.5], punch_every=0, flash_every=0, reveal=8, push_all=True),
}


def auto(folder, bpm, style, hook, hook_sub, out, labels):
    clips = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in VIDEO_EXT)
    if not clips:
        sys.exit(f"No video files in {folder}")
    st = STYLES[style]
    beat = 60.0 / bpm
    process, reveal = (clips[:-1] or clips), clips[-1]
    durs = {c: probe(c) for c in clips}

    segs, used = [], {c: 0 for c in process}
    for i, beats in enumerate(st["pattern"] * math.ceil(len(process) / len(st["pattern"]))):
        if i >= max(len(st["pattern"]), len(process)):
            break
        c = process[i % len(process)]
        speed = st["speed"][i % len(st["speed"])]
        need = beats * beat * speed
        # spread picks across the clip, skipping the shaky first/last half second
        slots = max(1, math.ceil(len(st["pattern"]) / len(process)))
        span = max(0.0, durs[c] - need - 1.0)
        at = 0.5 + span * ((used[c] + 0.5) / slots)
        used[c] += 1
        s = {"src": str(c), "at": round(at, 2), "beats": beats, "speed": speed}
        if st.get("punch_every") and i % st["punch_every"] == 1:
            s["punch"] = True
        if st.get("flash_every") and i % st["flash_every"] == 0 and i:
            s["flash"] = True
        if st.get("push_all") or i < st.get("push_first", 0):
            s["push"] = True
        segs.append(s)

    rv = {"src": str(reveal), "at": round(max(0.0, durs[reveal] - st["reveal"] * beat - 0.3), 2),
          "beats": st["reveal"], "speed": 1, "push": True, "flash": style != "calm"}
    if labels:
        rv["label"] = labels
    segs.append(rv)

    spec = {
        "name": out, "bpm": bpm, "style": style, "hook": hook, "hook_sub": hook_sub,
        "song_start": 0, "segments": segs, "end": {"beats": 4},
    }
    sp = ROOT / "specs" / f"{out}.json"
    sp.parent.mkdir(exist_ok=True)
    sp.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"  spec -> {sp}")
    return sp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auto", help="build a spec from a folder of clips, then render")
    a.add_argument("folder")
    a.add_argument("--bpm", type=float, required=True)
    a.add_argument("--style", choices=STYLES, default="punchy")
    a.add_argument("--hook", default="")
    a.add_argument("--hook-sub", default="")
    a.add_argument("--label", default="", help="caption on the reveal, e.g. 'Fresh · forearm'")
    a.add_argument("--out", required=True)
    a.add_argument("--preview-audio")
    r = sub.add_parser("render", help="render an existing spec")
    r.add_argument("spec")
    r.add_argument("--preview-audio")
    args = ap.parse_args()

    if args.cmd == "auto":
        sp = auto(args.folder, args.bpm, args.style, args.hook, args.hook_sub, args.out, args.label)
        render(sp, args.preview_audio)
    else:
        render(args.spec, args.preview_audio)


if __name__ == "__main__":
    main()
