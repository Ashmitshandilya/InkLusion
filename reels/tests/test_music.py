"""Measure beat / bar / drop accuracy of reelkit.music against synthetic songs with known truth."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reelkit import music  # noqa: E402


def check(mp3):
    truth = json.loads(mp3.with_suffix(".truth.json").read_text())
    a = music.analyze(mp3, force=True)
    tb = np.array(truth["beats"])
    est = np.array(a["beats"])
    # the analyser may report half / double time; compare against the matching truth grid
    ratio = a["bpm"] / truth["bpm"]
    if ratio > 1.5:
        tb = np.sort(np.r_[tb, tb[:-1] + np.diff(tb) / 2])
    elif ratio < 0.67:
        pass  # every 2nd truth beat should be matched; nearest-match below handles it
    # only beats inside the drummed / timed part
    errs = np.array([np.min(np.abs(tb - t)) for t in est if tb[0] - 0.05 <= t <= tb[-1] + 0.05])
    bars_t = np.array(truth["bars"])
    bar_err = np.array([np.min(np.abs(bars_t - t)) for t in a["bars"] if bars_t[0] - 0.05 <= t <= bars_t[-1] + 0.05])
    bar_ok = np.mean(bar_err < 0.05)
    drop_ok = [b for _, b in a["drops"]]
    return {
        "song": mp3.stem,
        "true_bpm": truth["bpm"],
        "found_bpm": a["bpm"],
        "steady": a["constant_tempo"],
        "beat_err_mean_ms": round(1000 * errs.mean(), 1),
        "beat_err_p95_ms": round(1000 * np.percentile(errs, 95), 1),
        "beat_err_max_ms": round(1000 * errs.max(), 1),
        "bars_on_downbeat": f"{100 * bar_ok:.0f}%",
        "drops_true": truth["drop_bars"],
        "drops_found": drop_ok[:3],
    }


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    rows = [check(p) for p in sorted(folder.glob("*.mp3"))]
    for r in rows:
        print(json.dumps(r))
