# What the magenta Vesper taught us, and how we refined it

Version 1 · 2026-11-03 · Builds on [the folio study](../folio-study/FOLIO-2025-STUDY.md) and the
`after-light-work` branch ([afterlight/](../../afterlight/README.md)). Owner request: get to know the
folio research, research the learned concepts and refine them, starting from the magenta Vesper
car, its lava veins, lighting and boosters.

**How to read this.** *Observed* means read in the Afterlight source or measured in its frames.
*Inference* means our interpretation. Every refinement listed here is built and running in
[`vesper/`](../../vesper/README.md). Section 4 explains what carries over to a phone game.

## 1. Why the Vesper works (observed in `afterlight/`)

| # | Concept | Where it lives | What it does on screen |
|---|---|---|---|
| L1 | **One hue family, three jobs.** Violet paint `#795b95`, magenta energy `#ff25ba`, violet-magenta shadow tint `(.31,.06,.43)` | `styles.py`, `common.glsl` | Paint, glow and shadow all sit within about 40° of hue, so the frame reads as one colour story. The orange tail lamps are the only complement |
| L2 | **Folio's single tinted shadow.** Form shadow and cast shadow are merged with `max()` and multiplied into the base colour, never into grey | `object.frag` | Shadowed violet stays saturated violet. Nothing looks dirty |
| L3 | **Energy lights its surroundings.** Three cabin point lights, six fixed vein-junction lights and two booster lights add coloured diffuse and specular light to the paint | `object.frag` | The magenta looks hot because the body next to it turns magenta. In folio only the sun lights things; here the energy does too |
| L4 | **Luminance-normalised emission.** `e /= luminance(e)` before intensity | `object.frag` (from folio) | Every hue blooms equally at the same intensity, so magenta is never weaker than orange |
| L5 | **Distance-along-path pulses.** Each vein ribbon stores the distance from its root in `uv.x`. `fract(x·0.48 − time·speed)` sends a bright core along it | `veins.py`, `vein.frag` | The veins flow instead of blinking as one strip |
| L6 | **Shader-built plumes.** A static tube mesh holds only (u, angle, layer). The vertex shader sets length, radius, shock cells and sway | `boosters.py`, `jet.vert` | Plumes can grow, wobble and breathe at no CPU cost |
| L7 | **A mirror pass, not a mirror material.** The car is redrawn flipped into a 1/3-resolution buffer and sampled with a small blur | `showcase.py`, `floor.frag` | A dark studio floor gets believable reflections |
| L8 | **Bloom only above 1.0** (folio rule) plus a hue-preserving shoulder | `bloom.frag`, `composite.frag` | Only emissives glow; lit paint stays crisp, and hot magenta does not clip to white |
| L9 | **Local heat haze.** Screen distortion only along the projected plume segments, scaled by boost | `composite.frag` | Heat haze sells the plume as hot without blurring the whole frame |
| L10 | **One curve drives picture and sound.** `boost_at(t)` sets plume length, squat, light and the roar envelope | `showcase.py`, `sound.py` | Audio and picture can't drift apart |

## 2. What held it back (observed)

1. **The junction lights don't move.** The pulses travel, but the six vein lights sit at fixed points with
   steady strength. The paint never reacts to a pulse passing.
2. **Pulse speed jumps during ignition.** The phase is `time · (0.74 + 0.55·boost)` with section time
   `time` up to 9 s. While boost ramps (about 4.4–6.0 s), the phase speed gains
   `time · 0.55 · dboost/dt`, roughly +2.6 units/s at 5.2 s. The pulses briefly run about 3.5× faster,
   then settle. It reads as a surge, but nothing controls it.
3. **Two-colour lava.** `mix(ember, fire, hot)` then `mix(…, core, vein)`. It has no temperature scale, so
   cooling, heating and the flood front can't be shown.
4. **The energy has no route.** The heart, veins and boosters all glow from the first frame. Nothing
   travels from one to the other, so the effects never become a story.
5. **Plumes are two shells with moving shock cells.** Real shock diamonds stay still relative to the
   nozzle. Moving cells read as texture, not physics.
6. **Sparks fly in straight lines** and fade in the air.
7. **A mirror floor can't show speed.** The car never moves, and a featureless reflective floor gives
   no motion cue.
8. **One bloom radius** at 1/4 resolution, with no streak, motion blur or camera shake.

## 3. Refinements built in `vesper/`

| # | Refinement | Fixes | Implementation |
|---|---|---|---|
| R1 | **Pulses are real lights.** Each frame the CPU finds every pulse position on all 18 arteries (plus the flood heads) and sends the 24 strongest as point lights | 1 | `veins_plus.py` keeps each artery's centre line; `World.pulses()`; `pulses[24]` in `object.frag` |
| R2 | **Phase-integrated flow.** `flowPhase(t) = ∫ (0.74 + 0.9·boost + 0.012·speed) dt` is computed on the CPU and shared by veins, flames and pulse lights | 2 | `_FLOW` table in `magenta.py` |
| R3 | **Magenta temperature ramp** `magma(t)`: crust → deep violet → magenta → hot pink → white. Brightness rises with t² | 3 | `common.glsl` |
| R4 | **Crust plates and glowing cracks.** Moving Voronoi cells across the ribbon; cracks run hotter than plates. fBm churn on top | 3 | `vein.frag` |
| R5 | **The energy has a route:** heartbeat → flood → lamps → boosters → cool-down → drain home. The flood front is white-hot and the drain retreats from the tips | 4 | `fill_front`, `drain_front`, `cool`, `heart` curves |
| R6 | **"Asleep" lighting.** The key light starts at 30% and wakes with `charge`, so the heart lights the opening alone | 4 | `wake` in `object.frag` |
| R7 | **Three-shell plume:** white-hot core (first 60% only), magenta sheath, violet haze. **Stationary shock diamonds** that pinch the core and fade along the plume | 5 | `jet.vert`, `jet.frag` |
| R8 | **Sputter, then ignition.** Three growing pops, then ignition. Each pop sends an expanding shock ring across the floor and kicks the camera | 5 | `POPS`, `rings[4]` in `floor.frag` |
| R9 | **Embers with gravity** that skip once on the wet floor and cool along `magma` | 6 | `spark.vert` |
| R10 | **Speed on a mirror.** Floor panel seams stream past with travel, wet patches sharpen the reflections, and ripples shift them. Seams across the direction of travel are **box-filtered over the shutter** (analytic motion blur) | 7 | `floor.frag` |
| R11 | **Post stack:** bloom at 1/4 and 1/8, an anamorphic streak from pixels above 2.4, plume heat haze from noise, radial chromatic fringe (stronger with shake), grain, violet-black floor | 8 | `composite.frag`, `Renderer.render` |
| R12 | **Sub-frame motion blur** (3 sub-frames, 5 at speed and ignition; 180° shutter; never across a cut) and a **noise camera rig** driven by speed, pops and ignition | 8 | `frame_at`, `camera` |
| R13 | **Score locked to the same curves**, with roar following boost and whine following speed | L10 kept | `score.py` |

### Measured cost (this cloud host, Mesa llvmpipe, 4 CPU threads)

| Render | Original showcase | Magenta cut |
|---|---|---|
| 960×540, 1 sub-frame | 0.14 s | 0.43 s |
| 2560×1440, delivery (3–5 sub-frames) | — | ≈3–5 s per frame |

The extra cost comes from the 24 pulse lights, three plume shells and the post passes, and above all from
sub-frames. On a GPU these are all cheap.

## 4. What carries over to a phone game (inference)

| Technique | Phone budget | How to keep it |
|---|---|---|
| L1/L2 one hue family, tinted shadow | Free | Folio material in Godot (see the folio study §9) |
| L4 luminance-normalised emission | Free | One line in the emissive shader |
| L5 + R2 + R3 + R4 veins | Cheap | UV.x distance and one uniform `flowPhase`; drop the Voronoi on low tier |
| R1 pulse lights | **Expensive per pixel** | Mobile tier: 4 lights max, or fake the spill with an additive decal under each pulse |
| L6 + R7 plumes | Cheap | Vertex shader; 2 shells on low tier |
| L7 mirror pass | Medium | Only on hero shots and menus; screen-space or none in play |
| R10 streaming floor | Cheap | Pure shader maths |
| R11 post | Medium | Godot glow (HDR threshold 1.0); skip streak and chromatic fringe on low tier |
| R12 motion blur | Film only | Trailers via Movie Maker mode, not live play |

**The main lesson for game design:** in the Vesper, **energy moving along a line is the event**.
A board game played on lines (Barah Goti's Alquerque lattice) can use that directly: legal moves,
captures and the Switch can all be shown as energy travelling along board lines. See
[HIJACK-TWELVE.md](../../hijack12/HIJACK-TWELVE.md).
