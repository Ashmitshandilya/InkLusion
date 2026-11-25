#!/usr/bin/env python3
"""
Drop photos/videos in reels/inbox/media and songs in reels/inbox/music, then:

    python3 reels/make.py                      # every style x every song
    python3 reels/make.py --styles punchy,build --per-song 2
    python3 reels/make.py --analyze            # only show what it found (tempo, drops, media)

Output: reels/out/<date-time>/  ->  NN-style-song.mp4 (with music), NN-style-song-silent.mp4,
        contact-sheet.jpg, manifest.json (song start time, bpm, shots).
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reelkit import media, music, styles  # noqa: E402
from reelkit.compose import render  # noqa: E402
from reelkit.overlays import Brand  # noqa: E402
from reelkit.util import ROOT, fmt_time, log  # noqa: E402

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")[:28] or "song"


def _render_job(args):
    plan, out, seed = args
    t = time.time()
    thumbs = render(plan, Brand(), out, seed)
    return out, thumbs, time.time() - t


def contact_sheet(rows, path):
    import cv2

    if not rows:
        return
    tw, th, pad, lw, cap = 180, 320, 8, 300, 14
    rows = [(n, [t[int(i)] for i in np.linspace(0, len(t) - 1, min(cap, len(t)))]) for n, t in rows]
    width = lw + max(len(t) for _, t in rows) * (tw + pad)
    sheet = np.full(((th + pad) * len(rows) + pad, width, 3), 18, np.uint8)
    for r, (name, thumbs) in enumerate(rows):
        y = pad + r * (th + pad)
        cv2.putText(sheet, name, (12, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 225, 235), 1, cv2.LINE_AA)
        for i, im in enumerate(thumbs):
            x = lw + i * (tw + pad)
            sheet[y:y + th, x:x + tw] = im
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--media", default=str(ROOT / "inbox" / "media"))
    ap.add_argument("--music", default=str(ROOT / "inbox" / "music"), help="folder or a single song file")
    ap.add_argument("--styles", default=",".join(styles.STYLES), help=f"any of {','.join(styles.STYLES)}")
    ap.add_argument("--per-song", type=int, default=1, help="variations of each style per song")
    ap.add_argument("--length", type=float, help="target seconds (default per style)")
    ap.add_argument("--hook", help="opening text (default: rotates through brand.json hooks)")
    ap.add_argument("--seed", type=int, default=int(time.time()) % 10000)
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--out", default=str(ROOT / "out"))
    ap.add_argument("--analyze", action="store_true", help="analyse only, render nothing")
    a = ap.parse_args()

    brand = Brand()
    rng = np.random.default_rng(a.seed)
    mp = Path(a.music)
    songs = [mp] if mp.is_file() else sorted(p for p in mp.rglob("*") if p.suffix.lower() in AUDIO_EXT)
    if not songs:
        sys.exit(f"No songs found in {mp}. Put .mp3/.m4a/.wav files there.")
    found = media.scan(a.media)
    if not found:
        sys.exit(f"No photos or videos found in {a.media}.")
    chosen = [s.strip() for s in a.styles.split(",") if s.strip()]
    bad = [s for s in chosen if s not in styles.STYLES]
    if bad:
        sys.exit(f"Unknown style(s): {bad}. Pick from {list(styles.STYLES)}")

    log(f"{len(found)} media files, {len(songs)} songs")
    items = media.prepare(found, workers=os.cpu_count() or 2)
    analyses = {s: music.analyze(s) for s in songs}

    print("\nSongs")
    for s, an in analyses.items():
        drops = ", ".join(fmt_time(an["bars"][b]) for _, b in an["drops"][:3]) or "none found"
        print(f"  {s.name}: {an['bpm']:.1f} bpm ({'steady' if an['constant_tempo'] else 'drifting'}), "
              f"{len(an['bars'])} bars, drops at {drops}")
    print("Media")
    for it in items:
        extra = f"{it.duration:.1f}s, steady {it.steady:.2f}" if it.kind == "video" else ("whole photo" if it.fit else "cropped")
        print(f"  {Path(it.path).name}: {it.kind}, {it.role}, sharp {it.sharp:.2f}, {extra}"
              + (f", label '{it.label}'" if it.label else ""))
    if a.analyze:
        return

    pool = media.Pool(items, rng)
    hooks = list(brand.hooks)
    jobs, manifest = [], []
    batch = Path(a.out) / time.strftime("%Y-%m-%d_%H%M%S")
    batch.mkdir(parents=True, exist_ok=True)
    n = 0
    for s in songs:
        used = []
        for v in range(a.per_song):
            for st in chosen:
                n += 1
                hook = a.hook if a.hook is not None else hooks[(n - 1) % len(hooks)]
                plan, start_bar = styles.plan(st, s, analyses[s], pool, rng, brand, hook, used, a.length)
                used.append(start_bar)
                name = f"{n:02d}-{st}-{slug(s.stem)}"
                plan.name = name
                out = batch / f"{name}.mp4"
                jobs.append((plan, out, int(rng.integers(1 << 30))))
                manifest.append({
                    "file": out.name, "silent": f"{name}-silent.mp4", "style": st, "song": s.name,
                    "song_start": fmt_time(plan.song_start), "song_start_seconds": round(plan.song_start, 3),
                    "bpm": analyses[s]["bpm"], "seconds": round(plan.duration, 2), "hook": plan.hook.get("text", ""),
                    "shots": [{"media": Path(sh.item.path).name if sh.item else "end card",
                               "at": round(sh.t0, 3), "beats": sh.b1 - sh.b0, "src": round(sh.src, 2),
                               "speed": [round(x, 2) for x in sh.speed], "motion": sh.motion} for sh in plan.shots],
                    "cuts": [c.kind for c in plan.cuts],
                })
    (batch / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log(f"rendering {len(jobs)} reels with {a.jobs} workers -> {batch}")

    thumbs = {}
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(_render_job, j): j[1] for j in jobs}
        for f in as_completed(futs):
            try:
                out, th, secs = f.result()
                thumbs[out.name] = th
                log(f"  done {out.name} ({secs:.0f}s)")
            except Exception as e:
                log(f"  FAILED {futs[f].name}: {str(e)[:400]}")
    rows = [(m["file"].replace(".mp4", ""), thumbs[m["file"]]) for m in manifest if m["file"] in thumbs]
    contact_sheet(rows, batch / "contact-sheet.jpg")

    print(f"\n{len(rows)} reels in {batch}")
    for m in manifest:
        print(f"  {m['file']:<36} {m['seconds']:>5.1f}s  song from {m['song_start']}  ({m['bpm']:.0f} bpm)")
    print("\nPosting: upload the normal file. If Instagram mutes it, upload the -silent one and add the same song,\n"
          "starting at the time shown above.")


if __name__ == "__main__":
    main()
