# Reels

Drop photos, videos and songs in. Get a batch of finished Reels (1080×1920), cut on the beat, graded
and branded like the website.

## Use

```bash
npm run reels:setup        # once (macOS / Linux, needs Python 3.10+ and ffmpeg)
```

1. Put photos and videos in `reels/inbox/media/` (subfolders are fine).
2. Put songs in `reels/inbox/music/` (mp3, m4a, wav…).
3. Run:

```bash
npm run reels
```

Every style × every song is made. Results go to `reels/out/<date-time>/`:

| file | what |
|---|---|
| `NN-style-song.mp4` | reel with the song |
| `NN-style-song-silent.mp4` | same reel, no audio (add the song inside Instagram) |
| `contact-sheet.jpg` | one row of frames per reel, to pick quickly |
| `manifest.json` | song start time, tempo, every shot |

Options: `--styles punchy,build` · `--per-song 3` (3 variations of each) · `--length 12` (seconds) ·
`--hook "Fresh from the chair"` · `--music path/to/song.mp3` · `--analyze` (show tempo, drops and media, render nothing).

## Styles

| style | feel | how it cuts |
|---|---|---|
| `punchy` | hard, fast | sped-up process before the drop, 1–2 beat cuts after it, zoom pulses on drum hits, reveal on the drop |
| `build` | tension, then drop | long slow shots, cuts speed up in the bar before the drop, flash into the reveal |
| `story` | calm | 4+ second shots with crossfades, one line of text each (`story_lines` in `brand.json`) |
| `gallery` | portfolio | one photo per beat, whip pans on each bar |
| `stutter` | aggressive | two clips alternating every half beat, glitch on hits |
| `cosmic` | on brand | photos as cards over the eclipse, sliding in on the beat |

## Helping it choose (optional)

- **Roles from names.** A folder or file name containing `reveal`, `final`, `done`, `fresh` = the finished
  tattoo (shown on the drop). `healed`, `process`, `lining`, `shading`, `stencil`, `studio`, `artist` also work.
  Without names: videos are treated as process, the sharpest photo as the reveal.
- **Captions.** Text in square brackets in a file name becomes the caption:
  `IMG_2041 [Fine line · forearm].jpg`. Nothing is captioned otherwise; it never guesses.
- **Tempo.** If a slow song gets counted double-time, rename it `song [half].mp3` (or `[double]`).

## How the sync works

- Songs: percussive part → onset envelope at 5.8 ms resolution → beat tracker → a straight-line tempo fit,
  refined to 0.01 % / 1 ms. Songs with a drifting tempo get each beat snapped to its own drum hit.
  A fixed 11.2 ms detector delay is calibrated out. Bars come from kick + chord changes; drops from
  jumps in loudness and drum density.
- Measured on test songs with known beats (`tests/`): **beats within 1 ms** on steady songs
  (1.3 ms average on a drifting one); **cuts within half a frame (≤ 16.7 ms)** of the beat in the finished
  video; audio in the finished file within 3 ms.
- Footage: every clip is scored for sharpness, camera shake and movement; the steadiest, sharpest bits
  are used and no moment is reused in a batch. Vertical crops follow the ink / the action.
  iPhone HDR is tone-mapped; 60 fps clips allow real slow motion.

## Music and Instagram

A reel with a copyrighted song inside the file can get muted or blocked. Post the normal file; if
Instagram flags it, post the `-silent` file and add the same song in Instagram, starting at the time
in `manifest.json`.

## Re-use for another client

Change `brand.json` (name, colours, booking line, handle, hooks, story lines) and the fonts in `fonts/`.

## Tests

```bash
reels/.venv/bin/python reels/tests/synth.py /tmp/songs        # songs with known beats
reels/.venv/bin/python reels/tests/test_music.py /tmp/songs   # beat / bar / drop accuracy
reels/.venv/bin/python reels/tests/check_sync.py reels/out/<batch> /tmp/songs   # sync in finished reels
```
