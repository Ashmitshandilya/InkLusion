"""
Synthetic songs with known beat, bar and drop times, used to measure the analyser's accuracy.
Each song: 8-bar intro (pad + hats, no kick), 16-bar main (full drums), 4-bar break, 16-bar main.
Writes <name>.mp3 and <name>.truth.json.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 44100


def env(n, decay):
    return np.exp(-np.arange(n) / (decay * SR))


def kick(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t / 0.04)
    return 0.9 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.12)


def snare(rng):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.convolve(noise, [1, -1], "same")
    return (0.35 * noise * env(n, 0.06) + 0.3 * np.sin(2 * np.pi * 185 * t) * env(n, 0.05))


def hat(rng, open_=False):
    n = int((0.2 if open_ else 0.05) * SR)
    x = rng.standard_normal(n)
    x = np.diff(x, prepend=0)
    return 0.12 * x * env(n, 0.06 if open_ else 0.012)


def tone(freq, n, kind="saw"):
    t = np.arange(n) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * freq * t)
    return 2 * ((freq * t) % 1) - 1


CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


def make(name, bpm, offset=0.37, style="hiphop", swing=0.0, drift=0.0, seed=1, out=Path(".")):
    rng = np.random.default_rng(seed)
    sections = [("intro", 8), ("main", 16), ("break", 4), ("main", 16)]
    n_bars = sum(n for _, n in sections)
    # beat times (optionally drifting tempo, like a live drummer)
    P = 60.0 / bpm
    beats = [offset]
    for i in range(n_bars * 4):
        p = P * (1 + drift * np.sin(i / 23.0) + (drift / 3) * rng.standard_normal())
        beats.append(beats[-1] + p)
    beats = np.array(beats)
    total = beats[-1] + 2.0
    y = np.zeros(int(total * SR) + SR)

    def put(sig, t, gain=1.0):
        i = int(round(t * SR))
        j = min(len(y), i + len(sig))
        y[i:j] += gain * sig[: j - i]

    bar = 0
    drops = []
    for sec, nb in sections:
        if sec == "main":
            drops.append(bar)
        for b in range(nb):
            bi = (bar + b) * 4
            t0, t1 = beats[bi], beats[bi + 4]
            # pad chord every bar (all sections)
            n = int((t1 - t0) * SR)
            ch = CHORDS[(bar + b) % 4]
            pad = sum(tone(midi(m), n) for m in ch) / 3
            pad = np.convolve(pad, np.ones(40) / 40, "same") * (0.10 if sec != "main" else 0.07)
            put(pad * np.minimum(1, np.arange(n) / (0.05 * SR)), t0)
            for k in range(4):
                tb = beats[bi + k]
                pb = beats[bi + k + 1] - tb
                # hats on 8ths everywhere except the break
                if sec != "break":
                    for e in range(2):
                        th = tb + e * pb / 2 + (swing * pb / 2 if e == 1 else 0)
                        put(hat(rng), th, 0.8 if sec == "intro" else 1.0)
                if sec != "main":
                    continue
                if style == "four":
                    put(kick(rng), tb)
                else:
                    if k in (0, 2):
                        put(kick(rng), tb)
                    if k == 2:
                        put(kick(rng), tb + pb * 0.5, 0.7)
                if k in (1, 3):
                    put(snare(rng), tb)
                # bass on the root
                if k in (0, 2):
                    n = int(pb * 1.6 * SR)
                    put(0.25 * tone(midi(ch[0] - 24), n, "sine") * env(n, 0.4), tb)
        bar += nb

    y = y / np.max(np.abs(y)) * 0.9
    st = np.stack([y, y], 1)
    out.mkdir(parents=True, exist_ok=True)
    wav = out / f"{name}.wav"
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    mp3 = out / f"{name}.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "192k", mp3], check=True)
    wav.unlink()
    truth = {"bpm": bpm, "beats": beats.tolist(), "bars": beats[::4].tolist(), "drop_bars": drops,
             "drift": drift}
    (out / f"{name}.truth.json").write_text(json.dumps(truth))
    return mp3


SONGS = [
    ("hiphop-92", dict(bpm=92.0, style="hiphop")),
    ("hiphop-84.6", dict(bpm=84.6, style="hiphop", offset=0.81, swing=0.12)),
    ("trap-140", dict(bpm=140.0, style="hiphop", offset=0.12)),
    ("house-124", dict(bpm=124.0, style="four", offset=0.05)),
    ("slow-68", dict(bpm=68.0, style="hiphop", offset=1.3)),
    ("live-drift-100", dict(bpm=100.0, style="hiphop", drift=0.012)),
]

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "songs")
    for name, kw in SONGS:
        print(make(name, out=out, **kw))
