"""
Measure beat sync in finished reels made from synthetic songs (known beat times).
- video: detects hard cuts from frame differences, compares each with the nearest true beat / half beat
- audio: detects drum onsets in the reel's own audio track, compares with the true beats
Usage: check_sync.py <batch folder> <songs folder with .truth.json>
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelkit.util import run  # noqa: E402

FPS = 30


def cuts(mp4):
    raw = run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", "scale=90:160", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
              binary=True)
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 160, 90).astype(np.float32)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2))
    thr = max(12.0, 4 * np.median(d))
    idx = [i + 1 for i in range(1, len(d) - 1) if d[i] > thr and d[i] >= d[i - 1] and d[i] >= d[i + 1]]
    return np.array(idx) / FPS


def audio_onsets(mp4):
    import librosa

    raw = run(["ffmpeg", "-v", "error", "-i", mp4, "-f", "f32le", "-ac", "1", "-ar", "22050", "-"], binary=True)
    y = np.frombuffer(raw, np.float32)
    env = librosa.onset.onset_strength(y=y, sr=22050, hop_length=128)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=22050, hop_length=128, units="time", backtrack=False)
    return on - 0.0112  # same detector latency as the analyser


HARD = {"cut", "flash", "glitch"}


if __name__ == "__main__":
    batch, songs = Path(sys.argv[1]), Path(sys.argv[2])
    man = json.loads((batch / "manifest.json").read_text())
    allv, alla, miss = [], [], 0
    for m in man:
        truth = json.loads((songs / Path(m["song"]).with_suffix(".truth.json").name).read_text())
        tb = np.array(truth["beats"]) - m["song_start_seconds"]
        grid = np.sort(np.r_[tb, tb[:-1] + np.diff(tb) / 2])  # beats and half beats
        planned = [sh["at"] for sh, k in zip(m["shots"][1:], m["cuts"]) if k in HARD]
        det = cuts(batch / m["file"])
        ev = []
        for p in planned:
            near = det[np.abs(det - p) < 0.12] if len(det) else []
            if not len(near):
                miss += 1
                continue
            d = near[np.argmin(np.abs(near - p))]
            ev.append(np.min(np.abs(grid - d)) * 1000)
        ev = np.array(ev or [0.0])
        on = audio_onsets(batch / m["file"])
        on = on[(on > 0.05) & (on < m["seconds"] - 1.5)]
        ea = np.array([np.min(np.abs(tb - t)) for t in on]) * 1000 if len(on) else np.array([np.nan])
        ea = ea[ea < 0.25 * 60000 / truth["bpm"]] if len(on) else ea
        allv += list(ev)
        alla += list(ea)
        print(f"{m['file']:<28} hard cuts {len(planned):>3}  on-beat error mean {ev.mean():5.1f} ms  max {ev.max():5.1f} ms"
              f"  | audio onsets {len(on):>3}  error mean {np.nanmean(ea):5.1f} ms  max {np.nanmax(ea):5.1f} ms")
    allv, alla = np.array(allv), np.array(alla)
    print(f"\nALL: {len(allv)} hard cuts ({miss} not detected), error mean {allv.mean():.1f} ms, "
          f"max {allv.max():.1f} ms | audio onsets error mean {np.nanmean(alla):.1f} ms, max {np.nanmax(alla):.1f} ms")
