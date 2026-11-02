# AFTERLIGHT — VEIN SERIES

An original 30-second, car-only film for **blitzedo**. Three cars share a family chassis, with individual aero kits, paint, molten veins, lamp colors and booster palettes.

| Car | Body and energy | Aero details | Lamps and boosters |
| --- | --- | --- | --- |
| CINDER / 07 | Graphite ceramic; orange-gold lava | Wide fenders, double canards, taller double wing | Amber headlights, red tails, gold-to-red twin plumes |
| GLACIER / 08 | Pearl silver; cyan-mint lava | Compact nose, single canards, lower wing | Mint headlights, violet tails, cyan-violet twin plumes |
| VESPER / 09 | Deep violet; magenta lava | Extended nose, dorsal fin, swept wing endplates | Pale-violet headlights, orange tails, magenta-violet twin plumes |

## The cut

Each nine-second section begins with a low front orbit, cuts into the hood's branching channels, then reveals the twin boosters from a rear three-quarter angle. Bright pulses travel through the inlaid veins; small flame licks rise at the hot junctions. The final three seconds show all three cars together.

| Time | Shot |
| --- | --- |
| 00–03 / 09–12 / 18–21 | Low front beauty passes |
| 03–05.4 / 12–14.4 / 21–23.4 | Moving vein and cabin details |
| 05.4–09 / 14.4–18 / 23.4–27 | Nozzle deployment and booster ignition |
| 27–30 | Three-car lineup and fade |

The cars remain in a dark reflective studio. Wheels spin, suspension compresses under thrust, nozzle petals open and the camera moves around the actual geometry. The blitzedo badge and serial are mounted on each car.

## Files

- `models/CINDER.glb`, `models/GLACIER.glb`, `models/VESPER.glb`: editable static car meshes, glass, lamp materials, vein coordinates, four wheels and twelve nozzle petals per car.
- `showcase.py`: cameras, shot timing, multipass renderer and animation.
- `car_geometry.py`: body, cockpit, intake, louvers, splitters and variant aero kits.
- `styles.py`: all three palettes and paint assignments.
- `veins.py`: surface-projected branching paths, recessed beds and flame anchors.
- `boosters.py`: the approved twin-jet geometry, nozzle hardware and spark system.
- `shaders/`: lighting, molten lamps, traveling veins, blaze, jets, sparks, reflections, bloom and heat haze.
- `sound.py`, `AFTERLIGHT_score.wav`: original stereo music and synthesized engine/ignition/jet effects.
- `master.py`: final video/audio mux and loudness normalization.
- `export_model.py`: rebuild the three GLB models.
- `verify_delivery.py`: inspect the movie, extract encoded frames and rebuild the source ZIP.
- `AFTERLIGHT_Preview.png`: actual frames decoded from the finished movie.

The GLB files contain the static model and emissive materials. The moving molten surfaces, pulses, flames, plume deformation, particles and post effects are implemented in the supplied GLSL renderer; glTF does not bake those custom effects into the static models.

## Reproduce

Requires Linux with EGL/OpenGL 3.3 (Mesa works), Python 3.10+, FFmpeg/ffprobe, NumPy and Pillow. No paid asset, external render service or API is required. `engine.py` defaults to surfaceless Mesa software rendering and eight worker threads. Set the environment variables there differently to use a compatible GPU.

From this directory:

```bash
python3 -m pip install -r requirements.txt
python3 showcase.py --stills --width 1920 --height 1080
python3 showcase.py --width 2880 --height 1620 --frames 900 --output AFTERLIGHT_picture.mp4
python3 sound.py
python3 master.py
python3 export_model.py
python3 verify_delivery.py
```

The picture is rendered at 2880×1620 and downsampled to 1920×1080. Delivery is 900 frames at 30 fps, H.264/YUV420p with explicit BT.709 tags, stereo AAC at 48 kHz, and MP4 fast-start. The master uses a measured two-pass loudness filter targeting −16 LUFS and −1 dBTP. If the score changes, measure again and update the values in `master.py`.

For a short moving test, use `--start 90 --frames 90` to render global seconds 3–6. `--start` is a frame index; full delivery starts at frame 0.

## Reference and authorship

The lighting study uses Bruno Simon's [folio-2025](https://github.com/brunosimon/folio-2025) source as its reference, especially its colored light/shadow treatment and restrained material hierarchy. This original car series extends that direction with three energy palettes, animated lava channels and twin boosters. No folio vehicle model is included. The car geometry, shot design and audio were authored for this film. See `COLOR_AND_MOTION_STUDY.md` and `THIRD_PARTY_NOTICES.txt` for the source study and attribution.
