# BLITZ CUT — a beat-synced blitzedo edit

30 seconds · 1920×1080 · 30 fps · stereo · 128 BPM, every cut on the grid.

**[Watch BLITZ_30s.mp4](BLITZ_30s.mp4)**

![Contact sheet from the encoded film](BLITZ_contact_sheet.png)

Owner brief: slow cinematic shots first, from behind the cars and the boosters; then really fast
camera angles, shots, transitions and animations, all synced to the beat.

## The edit (bar = 1.875 s)

| Bars | Time | Shots | Music |
|---|---|---|---|
| 1–2 | 0–3.75 s | **Rear dolly:** almost on the floor, creeping up between Vesper's twin nozzles, pilot flames flickering | Dark Fm9 pad opening, half-time heartbeat kick, sub |
| 3–4 | 3.75–7.5 s | **Rear orbit:** a slow arc behind the three-car grid; the nozzle petals open on beat 3 of bar 4 | High arpeggio enters, reverse swells, petal ticks on 16ths |
| 5 | 7.5–9.4 s | **Nozzle macro:** the core ring pulses on every beat | Backbeat, hats, sidechained bass, a tone on each core pulse |
| 6 | 9.4–11.25 s | **Name cards:** GLACIER, CINDER, VESPER, one per beat as each car's lamps fire, then all three noses | A lamp clunk, taiko and whoosh per card |
| 7 | 11.25–13.1 s | **Build:** a cut on every beat (heart, Cinder's rear, Glacier's nose, Vesper's face) with whip-ins | Kick on every beat, eighth snares, riser |
| 8 | 13.1–15 s | **Strobe:** half-beat cuts with a glitch, a giant **3 · 2 · 1**, then a black, silent beat | The roll speeds up to 32nds, countdown braams, dead silence |
| 9 | 15–16.9 s | **Launch:** a camera fixed to the floor as the pack ignites and blasts away, then a whip pan to side tracking | THE DROP: braam, sub drop, four-on-the-floor, reese bass, chord stabs, roar |
| 10 | 16.9–18.75 s | **One shot per beat:** crash zoom onto a wheel, a top-down spin, a low front chase, a floor-camera pass-by | Whooshes on every whip; a doppler pass-by |
| 11 | 18.75–20.6 s | **Barrel roll:** a full orbit with camera roll, a nozzle smear at speed, the multi-colour heart | Braam on the downbeat |
| 12 | 20.6–22.5 s | **Overtake:** Vesper surges past Cinder; a drone dives over the pack | |
| 13 | 22.5–24.4 s | **Glitch montage:** eight half-beat cuts with alternating whips and slice glitches | Stutter repeats on the last two beats |
| 14 | 24.4–26.25 s | **Slow motion:** time ramps to 20%, a slow arc around Vesper as the race brakes | Tape stop, drone, slow heartbeats, reverse swell |
| 15–16 | 26.25–30 s | **blitzedo:** the letters slam up on 16th notes in molten multi-colour, then a light sweep | Impact, braam, a bell per letter in F Yaman, final chord, shimmer |

## How it's built

- **`cut.py`** reuses the story film's renderer ([`hijack_film/film.py`](../hijack_film/README.md))
  and the unchanged Afterlight cars, and swaps in this edit's timeline, cameras and post-processing.
  - **The beat grid** (`bar()`, `KICKS`) drives every shot boundary, whip-in, flash, glitch window,
    lattice pulse, bloom pump and camera punch.
  - **Two clocks:** wall time drives the edit and the overlays; story time (`tau`) drives the cars,
    so the slow-motion bar can slow the world without slowing the cuts.
  - **The highway:** the cars stay put while the floor travels. The Barah Goti lattice repeats
    endlessly and is motion-blurred analytically. "Ground" cameras (launch, pass-by) subtract the
    travel, so the pack really tears past them.
  - **Transitions:** whip-ins (the view swings in over 0.12 s with up to 9 motion-blur sub-frames),
    two-frame cut flashes, zoom blur on crash zooms, the drop and the slam, slice glitch and
    chromatic split on the strobe and montage.
  - **Motion graphics:** per-beat name cards and the 3-2-1 countdown are drawn as overlays.
- **`score.py`** builds the track on the same grid with **`synth.py`** (the story film's NumPy and
  SciPy instruments). Part A (to bar 14) is mixed, then stuttered, gated and tape-stopped. Part B (the
  slow-motion bar and the logo) is mixed separately and summed. `master.py` masters to −14 LUFS /
  −1 dBTP.

## Reproduce

```bash
cd blitz_cut
python3 cut.py --stills --width 1920 --height 1080       # stills -> renders/
python3 cut.py --width 2560 --height 1440 --subframes 3  # picture (~90-100 min on 4 CPU threads)
python3 score.py && python3 master.py                    # -> BLITZ_30s.mp4
```
