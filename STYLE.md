# Emotion Lanterns: model and look rules

A LinkedIn video for [emotion-detection-in-text](https://github.com/SilverUmer21/emotion-detection-in-text).
The style follows our study of Bruno Simon's folio-2025 ([docs/folio-study/](docs/folio-study/FOLIO-2025-STUDY.md)).
Every model and colour here is our own. Mockup stage: nothing is approved yet.

## What the folio props taught us (measured 2026-10-31)

We imported six folio prop sets (lanterns, pole lights, benches, fences, crates and bricks) into
Blender 5.2 and rendered one of each design with its palette.

| Observation | Evidence |
|---|---|
| Very low poly | 12 triangles (fence board) to 358 (pole light) |
| Two or three palette colours per prop | Pole light uses slots 0/9/18; bench 0/18; crate 11/16/18 |
| Glass is a separate mesh | Lantern `light` and pole light `glass` are their own objects using the end palette slot |
| Chunkiness comes from layered parts, not bevels | Bench slats float with gaps; crate corners are separate cubes that overhang the frame |
| Silhouettes taper and flare | Pole light: pyramid plinth, collar band, housing wider at the top, overhanging roof, finial |
| Wood is flat-shaded, rounded stone is smooth | Bench smooth fraction 0.0, pole light 0.85 |

Our dihedral-angle measurements were unreliable because glTF splits vertices at hard edges, so the
table above relies on renders and counts only.

## Our rules

1. **Build props from 3–7 chunky parts.** Stack them: plinth, post, collar, head, cap, finial.
   Leave visible gaps or overhangs between parts.
2. **Taper everything.** Bases are wider at the bottom and caps overhang the part below them.
3. **2–3 palette colours per prop,** plus one emissive.
4. **Hand-made tilt.** Each instance gets a random lean of ±2° and a rotation of ±4°.
5. **No textures.** Use flat colour. Shading comes from the sun and the shadow tint.
6. **Low poly.** Keep a lantern under 400 triangles. Wood and stone are flat-shaded.

7. **Grass is a carpet, not spikes.** We use about 16k short, wide blades:
   - Clumped by blob noise, with bare patches between the clumps.
   - All blades lean with one wind direction.
   - Normals point up, so each blade shades like the ground beneath it.
   - Blades cast no shadows, and the root-to-tip shadow gradient is gentle.

   The first mockup used 2.7k tall blades that cast shadows. They read as dark spikes (owner
   feedback, 2026-10-31).

## Video (20 s, 30 fps, 1080 × 1350)

| Time | Beat |
|---|---|
| 0–0.7 s | Camera eases in over the dark ring |
| 0.7–1.5 s | "thank you" slams in letter by letter: drop, squash, dust, camera kick. The last letter adds a shockwave, an island bounce and a white flash |
| 1.8–2.4 s | Gratitude, caring and love ignite with an overshoot; the counters run up |
| 5–6.8 s | Letters pop away and the island spins to bring the blue arc to the camera |
| 7.1–8.9 s | "see you at 5" lands. Neutral lights, then nervousness flickers on |
| 10.6–14.4 s | Scene dims for the fact card: 9 in 10 "nervous" calls are wrong (precision 0.10, recall 0.70) |
| 14.4–20 s | Pull back, all 28 lanterns light in a wave, end card |

**Pipeline:**

| Script | Job |
|---|---|
| `lanterns_video.py` | Renders graded frames, set procedurally per frame |
| `compose_video.py` | Adds the text pass |
| `encode.py` | Encodes the MP4 with Blender's FFmpeg |

## Palette (ours)

| Role | Colour |
|---|---|
| Stone | `#8c87a6` |
| Wood | `#e2a36b` |
| Dark wood / metal | `#4a3233` |
| Moss top | `#b9ae4c` |
| Path slabs | `#efc49c` |
| Cliff rock | `#9c7e93` |
| Letter blocks | `#fff1e2` |

**Dusk preset (ours):** light `#ffa38a` × 1.15, shadow tint `#3f1a8f`, fog `#4a4fd8` → `#f25fb8`.

**Lantern families:**

| Family | Colour | Emotions |
|---|---|---|
| Warm | `#ffb03a` | Positive emotions |
| Blue | `#4f8bff` | Negative emotions |
| Teal | `#4ff0d0` | Thinking emotions: confusion, curiosity, realization, surprise |
| White | white | Neutral |

Emission is divided by its own luminance, so every hue glows equally bright at the same probability.
