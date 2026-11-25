"""
Song analysis: beat grid, bars (downbeats), energy per bar, drops, drum hits.

Accuracy strategy
1. Percussive part of the song (HPSS) -> onset envelope at 5.8 ms resolution.
2. librosa's dynamic-programming tracker gives rough beats.
3. Produced music (hip-hop, pop, EDM) has a constant tempo, so a straight line t = t0 + k*P is fitted
   to those beats, then period and phase are searched finely (0.01 % / 1 ms) to sit on the transients.
4. If the song drifts (live drummer), every beat is instead snapped to its own nearest transient.
"""

import numpy as np

from .util import cache_path, file_key, load_json, log, run, save_json

SR = 22050
HOP = 128  # 5.8 ms per onset frame
VERSION = 6
BPM_RANGE = (62.0, 152.0)  # beats are normalised into this range (half / double time)
# The onset envelope peaks a fixed ~11 ms after the real transient (measured on test songs with known
# beat times, same for MP3 and WAV). Subtracted from every beat and hit.
LATENCY = 0.0112


def decode(path, sr=SR, channels=1):
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", channels, "-ar", sr, "-"], binary=True)
    y = np.frombuffer(raw, np.float32).copy()
    return y.reshape(-1, channels) if channels > 1 else y


def _at(env, times):
    """Envelope value at arbitrary times (linear interpolation)."""
    x = np.asarray(times) * SR / HOP
    return np.interp(x, np.arange(len(env)), env, left=0.0, right=0.0)


def _peak_near(env, t, win=0.03):
    """Time of the strongest envelope peak within +-win of t (parabolic sub-frame refinement)."""
    a = max(1, int((t - win) * SR / HOP))
    b = min(len(env) - 2, int((t + win) * SR / HOP) + 1)
    if b <= a:
        return t, 0.0
    i = a + int(np.argmax(env[a:b]))
    y0, y1, y2 = env[i - 1], env[i], env[i + 1]
    d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    return (i + float(np.clip(d, -0.5, 0.5))) * HOP / SR, float(y1)


def _fit_line(times):
    """Robust fit times ~ t0 + k*P (k integers). Tolerates skipped or doubled tracker beats."""
    P = float(np.median(np.diff(times)))
    t0 = float(times[0])
    keep = np.ones(len(times), bool)
    for _ in range(4):
        k = np.round((times - t0) / P)
        A = np.vstack([np.ones_like(k), k]).T
        (t0, P), *_ = np.linalg.lstsq(A[keep], times[keep], rcond=None)
        res = times - (t0 + k * P)
        keep = np.abs(res) < max(0.025, 3 * float(np.median(np.abs(res))))
    return float(t0), float(P), res


def _grid_score(env, t0, P, dur, offsets):
    ks = np.arange(-int(t0 / P) - 1, int((dur - t0) / P) + 2)
    base = t0 + ks * P
    base = base[(base >= 0) & (base <= dur)]
    T = base[None, :] + offsets[:, None]
    return _at(env, T.ravel()).reshape(T.shape).sum(1)


def _refine_grid(env, t0, P, dur):
    """Search period (+-0.4 %, then finer) and phase (+-25 ms, 1 ms) to maximise transient energy on the grid."""
    offs = np.arange(-0.025, 0.02501, 0.001)
    best = (-1.0, t0, P)
    for span, steps in ((0.004, 81), (0.00012, 25)):
        centre = best[2] if best[0] >= 0 else P
        for p in centre * (1 + np.linspace(-span, span, steps)):
            s = _grid_score(env, best[1] if best[0] >= 0 else t0, p, dur, offs)
            i = int(np.argmax(s))
            if s[i] > best[0]:
                best = (float(s[i]), (best[1] if best[0] >= 0 else t0) + offs[i], float(p))
    return best[1], best[2]


def analyze(path, force=False):
    key = file_key(path, f"music{VERSION}")
    cp = cache_path("music", key, "json")
    if not force and (cached := load_json(cp)):
        return cached

    import librosa

    log(f"analysing song {path.name}")
    y = decode(path)
    dur = len(y) / SR

    y_perc = librosa.effects.percussive(y, margin=1.5)
    env = librosa.onset.onset_strength(y=y_perc, sr=SR, hop_length=HOP, n_fft=1024, n_mels=96)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    env = env / (np.percentile(env, 99.5) + 1e-9)

    # low band (kick) onset envelope from the full mix
    mel = librosa.feature.melspectrogram(y=y, sr=SR, n_fft=2048, hop_length=HOP, n_mels=64, fmax=8000)
    mel_db = librosa.power_to_db(mel)
    freqs = librosa.mel_frequencies(n_mels=64, fmax=8000)
    low = mel_db[freqs < 160]
    kick = np.maximum(0, np.diff(low, axis=1, prepend=low[:, :1])).mean(0)
    kick = kick / (np.percentile(kick, 99.5) + 1e-9)
    # 1) rough tempo + beats
    tempo = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=env, sr=SR, hop_length=HOP))[0])
    _, bf = librosa.beat.beat_track(onset_envelope=env, sr=SR, hop_length=HOP, start_bpm=tempo, tightness=200,
                                    units="frames")
    tracked = librosa.frames_to_time(bf, sr=SR, hop_length=HOP)
    if len(tracked) < 8:
        raise RuntimeError(f"{path.name}: could not find a steady beat")

    # 2) constant-tempo grid
    t0, P, _ = _fit_line(tracked)
    t0, P = _refine_grid(env, t0, P, dur)
    # 3) is the song really constant? compare transient positions with the grid
    snapped = np.array([_peak_near(env, t, 0.04)[0] for t in tracked])
    strength = _at(env, snapped)
    strong = strength > np.percentile(strength, 40)
    k = np.round((snapped - t0) / P)
    dev = np.abs(snapped - (t0 + k * P))[strong]
    constant = bool(np.median(dev) < 0.012 and np.percentile(dev, 90) < 0.03)

    if constant:
        n0 = int(np.floor(-t0 / P))
        beats = t0 + np.arange(n0, int((dur - t0) / P) + 1) * P
        beats = beats[(beats >= 0) & (beats <= dur - 0.05)]
    else:
        beats = list(np.array([_peak_near(env, t, 0.03)[0] if s > 0.15 else t
                               for t, s in zip(tracked, _at(env, tracked))]))
        # the tracker can start late / stop early (quiet intro): walk outwards with the local period
        p0 = float(np.median(np.diff(beats[:9])))
        while beats[0] - p0 > 0.05:
            t, v = _peak_near(env, beats[0] - p0, 0.03)
            beats.insert(0, t if v > 0.25 else beats[0] - p0)
        p1 = float(np.median(np.diff(beats[-9:])))
        while beats[-1] + p1 < dur - 0.05:
            t, v = _peak_near(env, beats[-1] + p1, 0.03)
            beats.append(t if v > 0.25 else beats[-1] + p1)
        beats = np.array(beats)
        P = float(np.median(np.diff(beats)))
    beats = beats - LATENCY
    beats = beats[beats >= 0]

    # 4) normalise into a usable range: double or halve
    bpm = 60.0 / P
    while bpm < BPM_RANGE[0]:
        beats = np.sort(np.concatenate([beats, beats[:-1] + np.diff(beats) / 2]))
        P /= 2
        bpm = 60.0 / P
    while bpm > BPM_RANGE[1]:
        even, odd = beats[0::2], beats[1::2]
        beats = even if _at(kick, even + LATENCY).sum() >= _at(kick, odd + LATENCY).sum() else odd
        P *= 2
        bpm = 60.0 / P
    # manual override from the file name: "song [half].mp3" / "song [double].mp3"
    tag = path.stem.lower()
    if "[half]" in tag and len(beats) > 16:
        even, odd = beats[0::2], beats[1::2]
        beats = even if _at(kick, even + LATENCY).sum() >= _at(kick, odd + LATENCY).sum() else odd
        P *= 2
    elif "[double]" in tag:
        beats = np.sort(np.concatenate([beats, beats[:-1] + np.diff(beats) / 2]))
        P /= 2

    # 5) downbeats: kick + harmonic change, choose the phase (0..3) that scores highest
    chroma = librosa.feature.chroma_stft(y=y, sr=SR, hop_length=512)
    bfr = np.clip((beats * SR / 512).astype(int), 0, chroma.shape[1] - 1)
    cb = librosa.util.sync(chroma, bfr, aggregate=np.median)  # one column per inter-beat span
    cb = cb / (np.linalg.norm(cb, axis=0, keepdims=True) + 1e-9)
    # column k+1 is the span starting at beat k (column 0 is before the first beat)
    change = (1 - np.sum(cb[:, 1:] * cb[:, :-1], axis=0))[: len(beats)]
    change = np.pad(change, (0, max(0, len(beats) - len(change))))
    kb = np.array([max(_at(kick, [t + LATENCY + d])[0] for d in (-0.01, 0, 0.01, 0.02)) for t in beats])

    def z(v):
        return (v - v.mean()) / (v.std() + 1e-9)

    feat = z(kb) + 0.8 * z(change)
    phase = int(np.argmax([feat[p::4].mean() for p in range(4)]))
    bars = beats[phase::4]

    # 6) energy per bar (loudness + drum density) and drops
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    rdb = 20 * np.log10(rms + 1e-6)
    rt = np.arange(len(rdb)) * 512 / SR

    def per_bar(times, vals):
        out = []
        for a, b in zip(bars[:-1], bars[1:]):
            m = (times >= a) & (times < b)
            out.append(float(vals[m].mean()) if m.any() else 0.0)
        return np.array(out)

    et = np.arange(len(env)) * HOP / SR
    loud, drums = per_bar(rt, rdb), per_bar(et, env)

    def norm(v):
        lo, hi = np.percentile(v, 5), np.percentile(v, 95)
        return np.clip((v - lo) / (hi - lo + 1e-9), 0, 1)

    inten = 0.6 * norm(loud) + 0.4 * norm(drums)
    drops = []
    for b in range(2, len(inten) - 2):
        nov = inten[b:b + 2].mean() - inten[max(0, b - 4):b].mean()
        if nov > 0.15:
            drops.append((float(nov), b))
    drops.sort(reverse=True)
    chosen = []
    for s, b in drops:
        if all(abs(b - c) >= 8 for _, c in chosen):
            chosen.append((s, b))

    # 7) accents on the 8th-note grid
    eighths = np.sort(np.concatenate([beats, beats[:-1] + np.diff(beats) / 2]))
    ev = np.array([max(_at(env, [t + LATENCY + d])[0] for d in (-0.01, 0, 0.01)) for t in eighths])
    thr = max(np.percentile(ev, 82), 0.35)
    hits = [[float(t - LATENCY), float(v)] for t, v in zip(eighths, ev) if v >= thr]

    res = {
        "file": path.name,
        "duration": dur,
        "bpm": round(60.0 / P, 3),
        "constant_tempo": constant,
        "beats": [round(float(t), 5) for t in beats],
        "downbeat_phase": phase,
        "bars": [round(float(t), 5) for t in bars],
        "intensity": [round(float(v), 3) for v in inten],
        "drops": [[round(s, 3), b] for s, b in chosen[:6]],
        "hits": hits,
    }
    save_json(cp, res)
    log(f"  {path.name}: {res['bpm']:.2f} bpm, {'steady' if constant else 'drifting'} tempo, "
        f"{len(bars)} bars, drops at bars {[b for _, b in chosen[:4]]}")
    return res


# ---------------------------------------------------------------- choosing a section

class Grid:
    """Beat grid of one excerpt, times relative to the excerpt start (a downbeat)."""

    def __init__(self, a, start_bar, n_bars):
        bars = np.array(a["bars"])
        beats = np.array(a["beats"])
        self.song = a
        self.start = float(bars[start_bar])
        end = float(bars[start_bar + n_bars])
        bi = int(np.argmin(np.abs(beats - self.start)))
        ei = int(np.argmin(np.abs(beats - end)))
        self.beats = beats[bi:ei + 1] - self.start
        self.n_bars = n_bars
        self.beat = float(np.median(np.diff(self.beats)))
        self.bar = self.beat * 4
        self.duration = float(self.beats[-1])
        self.hits = [(t - self.start, s) for t, s in a["hits"] if self.start <= t < end]
        self.intensity = a["intensity"][start_bar:start_bar + n_bars]
        self.drop = None
        for _, b in a["drops"]:
            if start_bar < b < start_bar + n_bars:
                self.drop = b - start_bar
                break

    def t(self, beat_index):
        """Time of a (possibly fractional) beat index."""
        i = int(np.floor(beat_index))
        f = beat_index - i
        i = min(max(i, 0), len(self.beats) - 1)
        if f == 0 or i + 1 >= len(self.beats):
            return float(self.beats[i]) + (f * self.beat if i + 1 >= len(self.beats) else 0.0)
        return float(self.beats[i] + f * (self.beats[i + 1] - self.beats[i]))


def pick_window(a, n_bars, mode, rng, used=()):
    """
    Choose where in the song the reel sits. Returns the start bar.
    mode: ("drop", frac)  drop lands at frac of the reel
          "high"          loudest, busiest stretch
          "mid"           steady, mid-energy stretch (story)
    `used` holds start bars already used for this song, so variations take different parts.
    """
    inten = np.array(a["intensity"])
    nb = len(inten)
    if nb <= n_bars + 1:
        return 0
    starts = np.arange(0, nb - n_bars)
    phrase0 = a["drops"][0][1] % 4 if a["drops"] else 0

    def overlap_pen(s):
        return sum(max(0, n_bars - abs(s - u)) / n_bars for u in used)

    scores = {}
    if isinstance(mode, tuple) and mode[0] == "drop" and a["drops"]:
        for strength, d in a["drops"]:
            s = d - int(round(mode[1] * n_bars))
            if 0 <= s < nb - n_bars:
                scores[s] = strength + 0.2 * inten[d:d + 2].mean() - overlap_pen(s)
    if not scores:
        for s in starts:
            seg = inten[s:s + n_bars]
            if mode == "mid":
                sc = -abs(seg.mean() - 0.55) - 0.4 * seg.std() - 0.6 * (seg < 0.3).mean()  # avoid drumless intros
            else:
                sc = seg.mean() - 0.3 * (seg < 0.25).mean()
            sc += 0.06 * ((s - phrase0) % 4 == 0) - overlap_pen(s) + rng.uniform(0, 0.02)
            scores[int(s)] = sc
    return int(max(scores, key=scores.get))
