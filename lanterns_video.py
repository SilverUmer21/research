"""Emotion Lanterns: 20 s, 30 fps, 1080x1350 animation (renders graded frames, no text).

  blender -b --factory-startup --python lanterns_video.py -- \
      [--frames 0-599 | --frames 46,60,250] [--samples 32]

Writes renders/video/frame_####.png, renders/video/meta_####.json (lantern screen positions and
glow) and renders/video/timeline.json for compose_video.py. Every frame is set procedurally from
the timeline below; there are no keyframes. Scores are made-up placeholders.
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lanterns_scene as S  # noqa: E402

FPS, FRAMES = 30, 600
OUT = S.ROOT / 'renders/video'
OUT.mkdir(parents=True, exist_ok=True)

HERO = {'text': 'thank you', 'first_land': 22, 'gap': 3,
        'ignite': [('gratitude', 54, .93), ('caring', 64, .46), ('love', 72, .31)], 'exit': 150}
NERVES = {'text': 'see you at 5', 'first_land': 214, 'gap': 3,
          'ignite': [('neutral', 246, .52)], 'flicker': ('nervousness', 256, .41), 'exit': 440}
SPIN = (160, 205)                      # island turns the blue arc to the camera
SPIN_ANGLE = 2 * math.pi * (1 - (25.5 - 6.0) / len(S.EMOTIONS))
FACT = (318, 432)                      # the scene dims for the fact card
PULLBACK = (432, 520)
WAVE = 450                             # all 28 lanterns light in a wave for the end card


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = min(1.0, max(0.0, t))
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def spring(s, decay, freq):
    """Damped oscillation starting at 1 when s = 0; 0 before the impulse."""
    return 0.0 if s < 0 else math.exp(-s / decay) * math.cos(s * freq)


# ---------------------------------------------------------------- build
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
glass = {}


def glass_for(emo, fam):
    glass[emo] = (S.glow(fam, 0.0, name=f'glass_{emo}'), fam)
    return glass[emo][0]


island, lanterns = S.build_island(6.0, glass_for)
S.sun_and_world()
cam = S.make_camera()
S.setup_render(int(S.arg('--samples', '32')))


def make_letters(text, tag):
    """Text -> mesh -> one object per letter, origin at the letter's bottom centre."""
    txt = S.sentence(text)
    bpy.ops.object.select_all(action='DESELECT')
    txt.select_set(True)
    bpy.context.view_layer.objects.active = txt
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)  # caps and walls convert unwelded
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    parts = list(bpy.context.selected_objects)
    letters = []
    for ob in parts:
        xs = [v.co.x for v in ob.data.vertices]
        ys = [v.co.y for v in ob.data.vertices]
        zs = [v.co.z for v in ob.data.vertices]
        pivot = Vector(((min(xs) + max(xs)) / 2, min(ys), (min(zs) + max(zs)) / 2))
        ob.data.transform(Matrix.Translation(-pivot))
        ob.location = ob.matrix_world @ pivot
        letters.append(ob)
    letters.sort(key=lambda o: o.location.x * math.cos(S.CAM_AZ + math.pi / 2)
                 + o.location.y * math.sin(S.CAM_AZ + math.pi / 2))
    for i, ob in enumerate(letters):
        ob.name = f'{tag}_{i}'
        ob['base'] = list(ob.location)
        ob['spin'] = random.Random(hash(tag) + i).uniform(-1, 1)
    return letters


def make_puffs(n):
    puffs = []
    for k in range(n):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        ob = bpy.context.active_object
        ob.name = f'puff{k}'
        ob.data.materials.append(S.toon('letter'))
        ob.hide_render = True
        puffs.append(ob)
    return puffs


hero_letters = make_letters(HERO['text'], 'hero')
nerves_letters = make_letters(NERVES['text'], 'nerves')
PUFFS_PER = 6
puffs = {ob.name: make_puffs(PUFFS_PER) for ob in hero_letters + nerves_letters}
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=.012, major_segments=64, minor_segments=6)
ring = bpy.context.active_object
ring.data.materials.append(S.glow('warm', .6, name='shockwave'))
ring.hide_render = True


def land_frames(cfg, letters):
    return [cfg['first_land'] + cfg['gap'] * i for i in range(len(letters))]


HERO_LAND = land_frames(HERO, hero_letters)
NERVES_LAND = land_frames(NERVES, nerves_letters)
SLAMS = [(f, .9 if i < len(HERO_LAND) - 1 else 3.2) for i, f in enumerate(HERO_LAND)] + \
        [(f, .5 if i < len(NERVES_LAND) - 1 else 1.6) for i, f in enumerate(NERVES_LAND)]
SHOCKS = [(HERO_LAND[-1], 1.0), (NERVES_LAND[-1], .6)]


# ---------------------------------------------------------------- per-frame state
def letter_state(ob, land, exit_f, f, island_dz):
    base = Vector(ob['base'])
    drop = 10
    if f < land - drop or f >= exit_f + 9:
        ob.hide_render = True
        return
    ob.hide_render = False
    up, side, z, spin = 1.0, 1.0, 0.0, 0.0
    if f < land:  # falling, stretched, spinning into place
        t = (f - (land - drop)) / drop
        z = 7.5 * (1 - t * t)
        up = 1 + .4 * t
        side = 1 / math.sqrt(up)
        spin = (1 - t) ** 2 * math.radians(50) * ob['spin']
    else:  # squash on impact, wobble back
        s = f - land
        up = 1 - .5 * spring(s, 3.0, .85)
        side = 1 / math.sqrt(max(up, .3))
    if f >= exit_f:  # pop: hop up and shrink away
        t = (f - exit_f) / 9
        z += 1.4 * math.sin(math.pi * min(t, 1) * .8)
        k = max(0.0, 1 - t) ** 2
        up, side = up * k, side * k
        spin += t * math.radians(90) * ob['spin']
    ob.location = base + Vector((0, 0, z + island_dz))
    ob.rotation_euler = (math.radians(90), spin, S.CAM_AZ + math.radians(90))
    ob.scale = (side, up, side)  # text space: Y is up


def puff_state(letter, land, f, island_dz):
    base = Vector(letter['base'])
    rnd = random.Random(letter.name)
    for k, ob in enumerate(puffs[letter.name]):
        s = f - land
        if s < 0 or s > 16:
            ob.hide_render = True
            continue
        ob.hide_render = False
        t = s / 16
        a = 2 * math.pi * k / PUFFS_PER + rnd.uniform(-.4, .4)
        r = .3 + 1.3 * ease_out(t)
        ob.location = base + Vector((math.cos(a) * r, math.sin(a) * r, .1 + .6 * ease_out(t) + island_dz))
        size = .12 * (1 - t) ** 1.5 * min(1, s / 2) * rnd.uniform(.7, 1.2)
        ob.scale = (size,) * 3


def glow_at(emo, f):
    """Quiet light: lanterns fade up slowly with no flare, so the letter slam stays the one loud beat."""
    p = 0.0
    for cfg in (HERO, NERVES):
        out = 1 - ease_in_out((f - cfg['exit']) / 18)
        for e, f0, target in cfg['ignite']:
            if e == emo and f >= f0:
                p = target * ease_in_out((f - f0) / 22) * out
        if 'flicker' in cfg and cfg['flicker'][0] == emo and f >= cfg['flicker'][1]:
            s, target = f - cfg['flicker'][1], cfg['flicker'][2]
            unease = 1 - .3 * abs(math.sin(s * .3)) * math.exp(-s / 70)  # soft shimmer that settles
            p = target * ease_in_out(s / 26) * unease * out
    if f >= WAVE:  # end card: every lantern comes up in a slow sweep around the ring
        i = [e for e, _ in S.EMOTIONS].index(emo)
        p = max(p, .3 * ease_in_out((f - WAVE - 2 * i) / 20))
    return p


def camera_state(f):
    t_in = ease_out(f / 40)
    az = S.CAM_AZ + math.radians(-8 * (1 - t_in) + .012 * f)
    elev = math.radians(36 - 2 * t_in)
    dist = 47 - 7 * t_in
    target = S.TARGET.copy()
    pb = ease_in_out((f - PULLBACK[0]) / (PULLBACK[1] - PULLBACK[0]))
    dist += 24 * pb
    elev += math.radians(14 * pb)
    target.z += 4.5 * pb
    roll, shake = 0.0, Vector()
    for f0, amp in SLAMS:
        s = f - f0
        if s >= 0:
            roll += math.radians(.9 * amp) * math.exp(-s / 5) * math.sin(s * .95)
            rnd = random.Random(f0 * 7 + f)
            shake += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) \
                * .09 * amp * math.exp(-s / 3.5)
    return az, elev, dist, target, roll, shake


def island_dz(f):
    return sum(-a * .16 * spring(f - f0, 4.0, .75) for f0, a in SLAMS if a > 1)


def frame(f):
    dz = island_dz(f)
    island.location.z = dz
    island.rotation_euler.z = SPIN_ANGLE * ease_in_out((f - SPIN[0]) / (SPIN[1] - SPIN[0]))
    for ob, land in zip(hero_letters, HERO_LAND):
        letter_state(ob, land, HERO['exit'] + 2 * hero_letters.index(ob), f, dz)
        puff_state(ob, land, f, dz)
    for ob, land in zip(nerves_letters, NERVES_LAND):
        letter_state(ob, land, NERVES['exit'] + 2 * nerves_letters.index(ob), f, dz)
        puff_state(ob, land, f, dz)
    ring.hide_render = True
    for f0, amp in SHOCKS:
        s = f - f0
        if 0 <= s <= 18:
            t = s / 18
            ring.hide_render = False
            r = 2.4 + 9 * amp * ease_out(t)
            ring.location = (0, 0, .12 + dz)
            ring.scale = (r, r, max(.05, 1 - t) * 4)
            S.set_glow(ring.data.materials[0], 'warm', .3 * (1 - t) ** 2)
    for emo, (mat, fam) in glass.items():
        S.set_glow(mat, fam, glow_at(emo, f))
    az, elev, dist, target, roll, shake = camera_state(f)
    S.place_camera(cam, az, elev, dist, target, roll, shake)
    bpy.context.view_layer.update()


def bloom_gain(f):
    g = .6
    for f0, amp in SLAMS:
        if f >= f0:
            g += .18 * amp * math.exp(-(f - f0) / 4)
    return g


def exposure(f):
    dim = ease_in_out((f - FACT[0]) / 14) * (1 - ease_in_out((f - FACT[1] + 14) / 14))
    return 1 - .55 * dim


timeline = {
    'fps': FPS, 'frames': FRAMES, 'placeholder_scores': True,
    'hero': {'text': HERO['text'], 'land': HERO_LAND, 'exit': HERO['exit'],
             'ignite': HERO['ignite']},
    'nerves': {'text': NERVES['text'], 'land': NERVES_LAND, 'exit': NERVES['exit'],
               'ignite': NERVES['ignite'] + [list(NERVES['flicker'])]},
    'slams': SLAMS, 'fact': FACT, 'pullback': PULLBACK, 'wave': WAVE, 'spin': SPIN,
}
(OUT / 'timeline.json').write_text(json.dumps(timeline, indent=1))

spec = S.arg('--frames', f'0-{FRAMES - 1}')
if '-' in spec:
    a, b = map(int, spec.split('-'))
    todo = range(a, b + 1)
else:
    todo = [int(x) for x in spec.split(',')]
for f in todo:
    frame(f)
    raw = OUT / f'_raw_{f:04d}.exr'  # one file per frame: Windows can refuse to overwrite a just-read EXR
    sc.render.filepath = str(raw)
    bpy.ops.render.render(write_still=True)
    S.grade(raw, OUT / f'frame_{f:04d}.png', bloom_gain(f), exposure(f))
    try:
        raw.unlink()
    except OSError:
        pass
    meta = {'frame': f, 'lanterns': {
        emo: S.project(cam, ob.matrix_world @ Vector((0, 0, 1.44))) + [round(glow_at(emo, f), 3), dict(S.EMOTIONS)[emo]]
        for emo, ob in lanterns.items()}}
    (OUT / f'meta_{f:04d}.json').write_text(json.dumps(meta))
    print('FRAME', f, flush=True)
