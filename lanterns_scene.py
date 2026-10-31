"""Emotion Lanterns: mockup frame for the emotion-detection LinkedIn video (not a game asset).

Run with Blender 5.2:
  blender -b --factory-startup --python lanterns_scene.py -- \
      --shot hero --out renders

Writes <shot>.png (graded frame, no text) and <shot>.json (lantern screen positions) for
compose_frame.py. Shading reimplements the folio-2025 tinted-shadow model; models are our own
(see STYLE.md). Probabilities are made-up placeholders until the real model is run.
"""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Quaternion, Vector

ROOT = Path(__file__).resolve().parent
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default):
    return args[args.index(name) + 1] if name in args else default


SHOT = arg('--shot', 'hero')
OUT = Path(arg('--out', str(ROOT / 'renders')))
SAMPLES = int(arg('--samples', '64'))
W, H = 1080, 1350
OUT.mkdir(parents=True, exist_ok=True)
FONT = ROOT / 'fonts/BarlowCondensed-Bold.ttf'

PAL = {
    'stone': '#8c87a6', 'wood': '#e2a36b', 'dark': '#4a3233', 'moss': '#b9ae4c',
    'path': '#efc49c', 'rock': '#9c7e93', 'letter': '#fff1e2', 'bush': '#8f9a3c',
}
DUSK = {'light': '#ffa38a', 'intensity': 1.15, 'shadow': '#3f1a8f',
        'fog_a': '#4a4fd8', 'fog_b': '#f25fb8', 'fog_near': 52.0, 'fog_far': 95.0}
FAMILY = {'warm': '#ffb03a', 'blue': '#4f8bff', 'teal': '#4ff0d0', 'white': '#ffffff'}
EMOTIONS = [  # ring order, grouped so colours read as arcs
    ('admiration', 'warm'), ('amusement', 'warm'), ('approval', 'warm'), ('caring', 'warm'),
    ('desire', 'warm'), ('excitement', 'warm'), ('gratitude', 'warm'), ('joy', 'warm'),
    ('love', 'warm'), ('optimism', 'warm'), ('pride', 'warm'), ('relief', 'warm'),
    ('confusion', 'teal'), ('curiosity', 'teal'), ('realization', 'teal'), ('surprise', 'teal'),
    ('anger', 'blue'), ('annoyance', 'blue'), ('disappointment', 'blue'), ('disapproval', 'blue'),
    ('disgust', 'blue'), ('embarrassment', 'blue'), ('fear', 'blue'), ('grief', 'blue'),
    ('nervousness', 'blue'), ('remorse', 'blue'), ('sadness', 'blue'), ('neutral', 'white'),
]
# Made-up placeholder scores (owner's instruction, 2026-10-31). Replace with real model output.
SHOTS = {
    'hero': {'text': 'thank you', 'front': 6.0,
             'probs': {'gratitude': .93, 'caring': .46, 'love': .31}},
    'nerves': {'text': 'see you at 5', 'front': 25.5,  # the honest beat: a calm line read as nervous
               'probs': {'nervousness': .41, 'neutral': .52}},
}
probs = SHOTS[SHOT]['probs']


def lin(hexvalue):
    h = hexvalue.lstrip('#')
    out = []
    for i in (0, 2, 4):
        v = int(h[i:i + 2], 16) / 255
        out.append(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
    return out


def rgba(hexvalue):
    return (*lin(hexvalue), 1.0)


# ---------------------------------------------------------------- materials
_mats = {}


def node(t, kind, loc=(0, 0), **inputs):
    n = t.nodes.new(kind)
    n.location = loc
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def math_node(t, op, a, b=None, loc=(0, 0)):
    n = t.nodes.new('ShaderNodeMath')
    n.operation = op
    n.location = loc
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            t.links.new(v, n.inputs[i])
    return n.outputs[0]


def mix_rgb(t, fac, a, b, blend='MIX', loc=(0, 0)):
    n = t.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    n.location = loc
    for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = v
        else:
            t.links.new(v, sock)
    return n.outputs[2]


def toon(key, root_shadow=False):
    """Folio-style shading: one sun, wrapped core shadow merged with cast shadow into one tint,
    fake ground bounce near the floor, fog toward the screen-space sky gradient."""
    name = f'toon_{key}_{root_shadow}'
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    base = rgba(PAL.get(key, key))
    out = node(t, 'ShaderNodeOutputMaterial', (1400, 0))
    # light amount (includes cast shadows) from a white diffuse probe
    diff = node(t, 'ShaderNodeBsdfDiffuse', (-900, 300), Color=(1, 1, 1, 1))
    s2r = node(t, 'ShaderNodeShaderToRGB', (-700, 300))
    t.links.new(diff.outputs[0], s2r.inputs[0])
    bw = node(t, 'ShaderNodeRGBToBW', (-500, 300))
    t.links.new(s2r.outputs['Color'], bw.inputs[0])
    core = node(t, 'ShaderNodeMapRange', (-300, 300))
    core.interpolation_type = 'SMOOTHSTEP'
    core.inputs['From Min'].default_value = -0.25
    core.inputs['From Max'].default_value = 1.0
    core.inputs['To Min'].default_value = 1.0
    core.inputs['To Max'].default_value = 0.0
    # a strength-1 sun gives a white diffuse 1/pi, so rescale to N.L x shadow
    t.links.new(math_node(t, 'MULTIPLY', bw.outputs[0], math.pi), core.inputs['Value'])
    shade = core.outputs['Result']
    geo = node(t, 'ShaderNodeNewGeometry', (-900, -200))
    sep = node(t, 'ShaderNodeSeparateXYZ', (-700, -200))
    t.links.new(geo.outputs['Position'], sep.inputs[0])
    if root_shadow:  # grass: root pushed fully into the shadow tint
        root = node(t, 'ShaderNodeMapRange', (-300, 100))
        root.interpolation_type = 'SMOOTHSTEP'
        root.inputs['From Min'].default_value = 0.0
        root.inputs['From Max'].default_value = 0.2
        root.inputs['To Min'].default_value = 0.55
        root.inputs['To Max'].default_value = 0.0
        t.links.new(sep.outputs['Z'], root.inputs['Value'])
        shade = math_node(t, 'MAXIMUM', shade, root.outputs['Result'], (-100, 200))
    # ground bounce: downward faces near the floor pick up the moss colour
    sepn = node(t, 'ShaderNodeSeparateXYZ', (-700, -400))
    t.links.new(geo.outputs['Normal'], sepn.inputs[0])
    orient = node(t, 'ShaderNodeMapRange', (-500, -400))
    orient.interpolation_type = 'SMOOTHSTEP'
    orient.inputs['From Min'].default_value = 1.0
    orient.inputs['From Max'].default_value = -1.0
    t.links.new(sepn.outputs['Z'], orient.inputs['Value'])
    near = math_node(t, 'SUBTRACT', 1.0, math_node(t, 'DIVIDE', math_node(t, 'MAXIMUM', sep.outputs['Z'], 0.0), 1.5))
    near = math_node(t, 'POWER', math_node(t, 'MAXIMUM', near, 0.0), 2.0)
    bounce = math_node(t, 'MULTIPLY', orient.outputs['Result'], near, (-300, -300))
    bounce = math_node(t, 'MULTIPLY', bounce, 0.6)
    lit_base = mix_rgb(t, bounce, base, rgba(PAL['moss']), loc=(-100, -100))
    light = tuple(c * DUSK['intensity'] for c in lin(DUSK['light'])) + (1.0,)
    lit = mix_rgb(t, 1.0, lit_base, light, 'MULTIPLY', (100, -100))
    shadow = mix_rgb(t, 1.0, base, rgba(DUSK['shadow']), 'MULTIPLY', (100, 100))
    col = mix_rgb(t, shade, lit, shadow, loc=(350, 0))
    # fog toward the diagonal screen gradient
    tc = node(t, 'ShaderNodeTexCoord', (-300, -700))
    length = node(t, 'ShaderNodeVectorMath', (-100, -700))
    length.operation = 'LENGTH'
    sepw = node(t, 'ShaderNodeSeparateXYZ', (-200, -850))
    t.links.new(tc.outputs['Window'], sepw.inputs[0])
    comb = node(t, 'ShaderNodeCombineXYZ', (-100, -850))
    t.links.new(sepw.outputs['X'], comb.inputs['X'])
    t.links.new(sepw.outputs['Y'], comb.inputs['Y'])
    t.links.new(comb.outputs[0], length.inputs[0])
    gsm = node(t, 'ShaderNodeMapRange', (100, -700))
    gsm.interpolation_type = 'SMOOTHSTEP'
    gsm.inputs['From Max'].default_value = 1.414
    t.links.new(length.outputs['Value'], gsm.inputs['Value'])
    fogcol = mix_rgb(t, gsm.outputs['Result'], rgba(DUSK['fog_a']), rgba(DUSK['fog_b']), loc=(350, -600))
    cam = node(t, 'ShaderNodeCameraData', (100, -400))
    fog = node(t, 'ShaderNodeMapRange', (300, -400))
    fog.interpolation_type = 'SMOOTHSTEP'
    fog.inputs['From Min'].default_value = DUSK['fog_near']
    fog.inputs['From Max'].default_value = DUSK['fog_far']
    t.links.new(cam.outputs['View Distance'], fog.inputs['Value'])
    final = mix_rgb(t, fog.outputs['Result'], col, fogcol, loc=(700, 0))
    em = node(t, 'ShaderNodeEmission', (1000, 0), Strength=1.0)
    t.links.new(final, em.inputs['Color'])
    t.links.new(em.outputs[0], out.inputs['Surface'])
    _mats[name] = m
    return m


def glow_values(family, p):
    """Emissive glass colour and strength; colour normalised by luminance so all hues bloom
    equally. p <= 0 is unlit dark tinted glass; p blends smoothly from unlit to lit."""
    c = lin(FAMILY[family])
    lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    c = [v / lum for v in c]
    dim = [0.015 + 0.03 * v / max(c) for v in c]
    on = min(1.0, max(0.0, p / .05))  # fade in over the first few percent
    col = [d * (1 - on) + v * on for d, v in zip(dim, c)]
    return (*col, 1), 1.0 * (1 - on) + (0.35 + p * 4.2) * on


def glow(family, p, name=None):
    name = name or f'glow_{family}_{p:.2f}'
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    out = node(t, 'ShaderNodeOutputMaterial', (300, 0))
    col, k = glow_values(family, p)
    em = node(t, 'ShaderNodeEmission', (0, 0), Color=col, Strength=k)
    em.name = 'glow'
    t.links.new(em.outputs[0], out.inputs['Surface'])
    _mats[name] = m
    return m


def set_glow(mat, family, p):
    col, k = glow_values(family, p)
    em = mat.node_tree.nodes['glow']
    em.inputs['Color'].default_value = col
    em.inputs['Strength'].default_value = k


# ---------------------------------------------------------------- geometry
def taper_box(name, wb, db, wt, dt, h, z0=0.0, mat=None, parent=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x * (wb if z == 0 else wt) / 2, y * (db if z == 0 else dt) / 2, z0 + z))
          for z in (0, h) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([vs[i] for i in f])
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def box(name, w, d, h, z0=0.0, x=0.0, y=0.0, **kw):
    ob = taper_box(name, w, d, w, d, h, z0, **kw)
    ob.location = (x, y, 0)
    return ob


def prism(name, r_bot, r_top, h, sides, z0=0.0, mat=None, jitter=0.0, seed=0):
    rnd = random.Random(seed)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bot, top = [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        j = 1 + rnd.uniform(-jitter, jitter)
        bot.append(bm.verts.new((math.cos(a) * r_bot * j, math.sin(a) * r_bot * j, z0)))
        top.append(bm.verts.new((math.cos(a) * r_top * j, math.sin(a) * r_top * j, z0 + h)))
    bm.faces.new(bot[::-1])
    bm.faces.new(top)
    for i in range(sides):
        k = (i + 1) % sides
        bm.faces.new((bot[i], bot[k], top[k], top[i]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def lantern(emotion, glass_mat, pos, face_angle, rnd):
    """Our lantern: tapered plinth, cap band, post, collar, framed glass head, hip roof, finial."""
    root = bpy.data.objects.new(f'lantern_{emotion}', None)
    bpy.context.scene.collection.objects.link(root)
    root.location = (*pos, 0)
    root.scale = (LANTERN_SCALE,) * 3
    root.rotation_euler = Euler((math.radians(rnd.uniform(-2, 2)), math.radians(rnd.uniform(-2, 2)),
                                 face_angle + math.radians(rnd.uniform(-4, 4))))
    stone, wood, dark = toon('stone'), toon('wood'), toon('dark')
    taper_box('plinth', .56, .56, .40, .40, .30, 0, stone, root)
    taper_box('plinth_cap', .48, .48, .46, .46, .07, .30, stone, root)
    taper_box('post', .16, .16, .13, .13, .86, .37, wood, root)
    taper_box('collar', .26, .26, .24, .24, .09, .62, dark, root)
    taper_box('head_floor', .46, .46, .44, .44, .06, 1.20, dark, root)
    taper_box('glass', .30, .30, .30, .30, .36, 1.26, glass_mat, root)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        bar = taper_box('bar', .06, .06, .06, .06, .36, 1.26, dark, root)
        bar.location = (sx * .18, sy * .18, 0)
    taper_box('roof_eave', .62, .62, .58, .58, .05, 1.62, stone, root)
    taper_box('roof', .58, .58, .14, .14, .22, 1.67, stone, root)
    taper_box('finial', .09, .09, .07, .07, .10, 1.89, dark, root)
    return root


def clump(x, y, seed):
    """Smooth 0..1 blob noise so grass grows in tufts with bare patches between them."""
    v = 0.0
    for k in range(5):
        r = random.Random(seed * 31 + k)
        fx, fy, px, py = r.uniform(.6, 1.4), r.uniform(.6, 1.4), r.uniform(0, 6.3), r.uniform(0, 6.3)
        v += math.sin(x * fx + px) * math.sin(y * fy + py)
    return min(1.0, max(0.0, .5 + v / 4))


def grass_patch(name, count, r_in, r_out, seed, exclude=()):
    """Folio-style carpet: many short wide blades, clumped, all leaning with one wind,
    normals pointing up so every blade shades like the ground under it, no cast shadows."""
    rnd = random.Random(seed)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    wind = (.05, .035)
    while len(bm.faces) < count:
        a = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(rnd.uniform(r_in ** 2, r_out ** 2))
        x, y = math.cos(a) * r, math.sin(a) * r
        c = clump(x, y, seed)
        if rnd.random() > c * c * 1.3:
            continue
        if any((x - ex) ** 2 + (y - ey) ** 2 < er ** 2 for ex, ey, er in exclude):
            continue
        h = (.08 + rnd.random() * .14) * (.55 + .6 * c)
        ang = rnd.uniform(0, math.pi)
        dx, dy = math.cos(ang) * .065, math.sin(ang) * .065
        v = [bm.verts.new((x - dx, y - dy, 0)), bm.verts.new((x + dx, y + dy, 0)),
             bm.verts.new((x + wind[0] + rnd.uniform(-.03, .03), y + wind[1] + rnd.uniform(-.03, .03), h))]
        bm.faces.new(v)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.normals_split_custom_set_from_vertices([(0, 0, 1)] * len(me.vertices))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.visible_shadow = False
    me.materials.append(toon('moss', root_shadow=True))
    return ob


def rock(name, size, loc, seed):
    ob = prism(name, size, size * .6, size * .8, 6, 0, toon('rock'), jitter=.25, seed=seed)
    ob.location = loc
    ob.rotation_euler = (0, 0, seed)
    return ob


def bush(name, size, loc, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (1, 1, .78)
    rnd = random.Random(seed)
    for v in ob.data.vertices:
        v.co *= 1 + rnd.uniform(-.12, .12)
    ob.data.materials.append(toon('bush'))
    return ob




# ---------------------------------------------------------------- scene
RING_R = 5.7
LANTERN_SCALE = 1.3
CAM_AZ = math.radians(-45)
TARGET = Vector((0, 0, 3.2))  # high target pushes the island down, leaving sky for the caption


def lantern_angle(i, front_index):
    return CAM_AZ + 2 * math.pi * (i - front_index) / len(EMOTIONS)


def build_island(front_index, glass_for):
    """Island, path, dais, lanterns, grass, rocks and bushes, all parented to one 'island' empty
    (so the video can spin and bounce it). glass_for(emotion, family) returns the glass material."""
    sc = bpy.context.scene
    rnd = random.Random(7)
    before = set(bpy.data.objects)
    prism('island_top', 8.0, 8.0, .22, 18, -.22, toon('moss'), jitter=.04, seed=1)
    prism('cliff', 7.4, 7.9, 2.6, 18, -2.82, toon('rock'), jitter=.06, seed=1)
    prism('cliff_low', 4.4, 7.3, 1.6, 12, -4.4, toon('rock'), jitter=.1, seed=2)
    for k in range(56):  # path slabs under the ring
        a = 2 * math.pi * (k + .5) / 56
        slab = taper_box(f'slab{k}', .62, .5, .58, .46, .05, 0, toon('path'))
        slab.location = (math.cos(a) * RING_R, math.sin(a) * RING_R, 0)
        slab.rotation_euler = (0, 0, a + math.radians(rnd.uniform(-6, 6)))
    prism('dais', 2.5, 2.35, .28, 16, 0, toon('path'))
    prism('dais_top', 2.2, 2.1, .1, 16, .28, toon('stone'))
    for k in range(8):  # spokes of slabs from dais to ring
        a = 2 * math.pi * k / 8 + math.pi / 8
        for d in (3.2, 4.0, 4.8):
            s = taper_box(f'spoke{k}_{d}', .5, .44, .46, .40, .05, 0, toon('path'))
            s.location = (math.cos(a) * d, math.sin(a) * d, 0)
            s.rotation_euler = (0, 0, a + math.radians(rnd.uniform(-8, 8)))
    lanterns = {}
    for i, (emo, fam) in enumerate(EMOTIONS):
        a = lantern_angle(i, front_index)
        lanterns[emo] = lantern(emo, glass_for(emo, fam), (math.cos(a) * RING_R, math.sin(a) * RING_R), a, rnd)
    exclude = [(math.cos(2 * math.pi * k / 56) * RING_R, math.sin(2 * math.pi * k / 56) * RING_R, .5)
               for k in range(56)]
    grass_patch('grass_outer', 9000, 6.3, 7.9, 3, exclude)
    grass_patch('grass_inner', 7000, 2.6, 5.1, 4)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        rock(f'rock{k}', rnd.uniform(.25, .55), (math.cos(a) * 7.6, math.sin(a) * 7.6, -.05), k + 10)
    for k in range(6):
        a = 2 * math.pi * k / 6 + .4
        bush(f'bush{k}', rnd.uniform(.45, .7), (math.cos(a) * 7.0, math.sin(a) * 7.0, .25), k)
    root = bpy.data.objects.new('island', None)
    sc.collection.objects.link(root)
    for ob in set(bpy.data.objects) - before:
        if ob.parent is None and ob is not root:
            ob.parent = root
    return root, lanterns


def sentence(text, parent=None):
    """Chunky extruded letters standing on the dais, facing the camera."""
    cu = bpy.data.curves.new('sentence', 'FONT')
    cu.body = text
    cu.font = bpy.data.fonts.load(str(FONT), check_existing=True)
    cu.size = 1.5
    cu.extrude = .22
    cu.bevel_depth = .03
    cu.bevel_resolution = 1
    cu.align_x = 'CENTER'
    txt = bpy.data.objects.new('sentence', cu)
    bpy.context.scene.collection.objects.link(txt)
    txt.data.materials.append(toon('letter'))
    txt.rotation_euler = (math.radians(90), 0, CAM_AZ + math.radians(90))
    txt.location = (0, 0, .38)
    txt.parent = parent
    return txt


def sun_and_world():
    """One sun, no lamps; the world is black because the sky is composited in the grade."""
    sc = bpy.context.scene
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = 1.0
    sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(55), 0, math.radians(-25))  # low sun from camera-left
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.0


def make_camera():
    """Telephoto diorama camera, 25 deg vertical FOV."""
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.lens = cam.data.sensor_height / 2 / math.tan(math.radians(12.5))
    cam.data.clip_end = 400
    cam.rotation_mode = 'QUATERNION'
    sc.camera = cam
    return cam


def place_camera(cam, az=CAM_AZ, elev=math.radians(34), dist=40.0, target=TARGET, roll=0.0, shake=(0, 0, 0)):
    dirv = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), math.sin(elev)))
    cam.location = target + dirv * dist + Vector(shake)
    cam.rotation_quaternion = (-dirv).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)


def setup_render(samples=SAMPLES):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.eevee.taa_render_samples = samples
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'


def project(cam, world_point):
    p = world_to_camera_view(bpy.context.scene, cam, world_point)
    return [round(p.x * W, 1), round((1 - p.y) * H, 1)]


# ---------------------------------------------------------------- grade: sky, bloom, tilt-shift
def blur(img, r):
    """Approximate gaussian with three box passes (cumulative sums), edges clamped."""
    out = img
    for _ in range(3):
        for axis in (0, 1):
            pad = [(0, 0)] * out.ndim
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode='edge'), axis=axis)
            n = out.shape[axis]
            hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
            lo = np.take(c, np.arange(0, n), axis=axis)
            out = (hi - lo) / (2 * r + 1)
    return out


_sky = None


def grade(raw, out_png, bloom_gain=0.6, exposure=1.0):
    """Composite the fog-gradient sky behind the render, add bloom from HDR emissives, then a
    tilt-shift band blur. Writes an sRGB PNG."""
    global _sky
    im = bpy.data.images.load(str(raw))
    px = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)  # bottom-up rows
    bpy.data.images.remove(im)
    rgb, a = px[..., :3], px[..., 3:4]
    if _sky is None:
        yy, xx = np.mgrid[0:H, 0:W]
        uv = np.stack([xx / (W - 1), yy / (H - 1)], -1)
        g = np.clip(np.linalg.norm(uv, axis=-1) / 1.414, 0, 1)
        g = (g * g * (3 - 2 * g))[..., None]
        sky = np.array(lin(DUSK['fog_a'])) * (1 - g) + np.array(lin(DUSK['fog_b'])) * g
        band = np.clip((np.abs(uv[..., 1:2] - .5) - .2) / .3, 0, 1)
        _sky = (sky.astype(np.float32), (band * band * (3 - 2 * band)).astype(np.float32))
    sky, band = _sky
    img = (rgb + sky * (1 - a)) * exposure  # film output is premultiplied
    bright = np.maximum(img - 1.0, 0)
    bloom = sum(blur(bright, r) for r in (3, 8, 18, 36, 70))
    img = img + bloom * bloom_gain
    img = img * (1 - band) + blur(img, 4) * band
    img = np.clip(img, 0, 1)
    srgb = np.where(img <= .0031308, img * 12.92, 1.055 * np.power(img, 1 / 2.4) - .055)
    outim = bpy.data.images.new('graded', W, H, alpha=True)
    outim.pixels[:] = np.concatenate([srgb, np.ones_like(a)], -1).ravel()
    outim.filepath_raw = str(out_png)
    outim.file_format = 'PNG'
    outim.save()
    bpy.data.images.remove(outim)


if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    island, lanterns = build_island(SHOTS[SHOT]['front'], lambda emo, fam: glow(fam, probs.get(emo, 0.0)))
    sentence(SHOTS[SHOT]['text'])
    sun_and_world()
    cam = make_camera()
    place_camera(cam)
    setup_render()
    raw = OUT / f'{SHOT}_raw.exr'
    sc.render.filepath = str(raw)
    bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.update()
    points = {emo: project(cam, ob.matrix_world @ Vector((0, 0, 1.44))) + [probs.get(emo, 0.0), dict(EMOTIONS)[emo]]
              for emo, ob in lanterns.items()}
    meta = {'shot': SHOT, 'text': SHOTS[SHOT]['text'], 'lanterns': points,
            'dais': project(cam, Vector((0, 0, .5))), 'placeholder_scores': True}
    (OUT / f'{SHOT}.json').write_text(json.dumps(meta, indent=1))
    grade(raw, OUT / f'{SHOT}.png')
    print('WROTE', OUT / f'{SHOT}.png')
