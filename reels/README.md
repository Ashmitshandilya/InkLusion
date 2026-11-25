# Reels

Cuts Shaurya's phone footage into 1080×1920 Reels timed to a song's beat, graded and branded
like the website (eclipse end card, same fonts).

## Use
1. Put one session's clips in `reels/raw/<name>/`. Name them in order (`01.mp4`, `02.mp4`…);
   the **last one is the reveal** (finished tattoo).
2. Run:
   ```bash
   python3 reels/reel.py auto reels/raw/<name> --bpm 92 --style punchy --hook "Four hours." --hook-sub "Thirty seconds." --label "Fresh · forearm" --out <name>
   ```
3. Tweak `reels/specs/<name>.json` (which clip, `at` seconds, `beats`, `speed`, `punch`, `flash`,
   `push`, `label`) and re-run `python3 reels/reel.py render reels/specs/<name>.json`.
4. Post `reels/out/<name>.mp4`. In Instagram add the song, drag its start to a beat. Cuts land on the beat.

## Styles
| style | feel | cuts |
|---|---|---|
| `punchy` | hard, fast, swagger | 1–2 beat cuts, 2–4× speed, punch-ins, flashes, reveal on the drop |
| `build` | slow start, then drop | 3 long shots, then 1-beat cuts, flash into the reveal |
| `calm` | story, studio, healed work | 4-beat shots, slow push-ins |

## Music
Songs are never put into the posted file: Instagram's library is licensed for Reels, a song baked
into the file can get the reel muted or taken down. `--preview-audio song.mp3` (+ `"song_start"` in
the spec) makes a private `*.preview.mp4` only for checking the sync.

## Notes
- iPhone HDR clips are tone-mapped automatically (otherwise they look grey).
- Text stays inside the Reels safe area (top 220 px, bottom 400 px are covered by the app UI).
- Fonts in `reels/fonts/` are under the SIL Open Font License.
