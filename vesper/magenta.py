"""VESPER / 09 - MAGENTA CUT.

A 30-second motion piece built on the Afterlight renderer, rebuilt around the
magenta Vesper alone. Same car geometry; new energy story and effects:

  heart wakes -> veins flood outward -> lamps -> nozzles, sputter, ignition ->
  launch and run -> chase -> cool-down, energy drains home, Barah Goti lattice.

Upgrades over afterlight/showcase.py (see README.md for the full list):
  * vein pulses are real moving lights (up to 24 per frame), not fixed junction lights
  * magenta temperature ramp (crust plates, glowing cracks, white-hot flood front)
  * three-shell plumes with stationary shock diamonds, sputter pops and shock rings
  * embers with gravity that skip on the wet floor
  * streaming wet floor (panel seams, wet patches, ripples) sells speed on a mirror
  * two bloom radii, anamorphic streak, heat haze, chromatic fringe, grain
  * sub-frame motion blur and camera shake driven by speed and ignition
"""
import os, sys, math, argparse, subprocess, time
import ctypes as C
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'afterlight'))
import showcase  # noqa: E402  (applies Afterlight's colour table, provides mesh helpers)
import engine as e  # noqa: E402
from engine import GL, Mesh, trans, rot, scale, normalize, lookat, perspective, ortho, smooth  # noqa: E402
from styles import STYLES, recolor  # noqa: E402
from veins_plus import build_veins  # noqa: E402

FONT = str(ROOT.parent / 'afterlight' / 'fonts' / 'BarlowCondensed-Bold.ttf')
FPS = 30
DURATION = 30.0
VESPER = 2
BOARD = 3.0  # Barah Goti point spacing on the floor (m)


def shader(name):
    return (ROOT / 'shaders' / name).read_text().replace('#include "common.glsl"', (ROOT / 'shaders' / 'common.glsl').read_text())


def sm(t, a, b):
    return smooth((t - a) / (b - a))


def gauss(t, c, w):
    return math.exp(-((t - c) / w) ** 2)


# ---------------------------------------------------------------- timeline
POPS = (13.90, 14.35, 14.75)
IGNITION = 15.15
BEATS = (0.70, 1.45, 2.05, 2.50, 2.85)


def heart(t):
    h = .04 + .52 * sm(t, 2.6, 3.6)
    for b in BEATS:  # lub-dub, accelerating
        h += .85 * gauss(t, b, .07) + .42 * gauss(t, b + .17, .06)
    h += .55 * gauss(t, IGNITION, .30) + .25 * boost(t)
    h *= 1 - .70 * sm(t, 26.6, 29.0)
    h += .65 * gauss(t, 29.15, .08) + .30 * gauss(t, 29.32, .07)  # last beat
    return h


def fill_front(t):
    return 0. if t < 3.0 else 3.6 * (1 - (1 - min(1., (t - 3.0) / 4.6)) ** 2)


def drain_front(t):
    return 99. if t < 26.8 else 3.3 - 3.0 * sm(t, 26.8, 29.3)


def cool(t):
    return .65 * sm(t, 26.8, 29.3)


def charge(t):
    return sm(t, 2.8, 7.8) * (1 - .55 * sm(t, 27.0, 29.5))


def lamp(t):
    if t < 8.40:
        return 0.
    if t < 8.47:
        return .6
    if t < 8.55:
        return .05
    return (.55 + .45 * sm(t, 8.55, 8.9)) * (1 - .45 * sm(t, 27.5, 29.5))


def deploy(t):
    return .05 + .95 * sm(t, 12.2, 13.5) * (1 - sm(t, 27.0, 28.6))


def boost(t):
    b = sum(a * gauss(t, p, .06) for p, a in zip(POPS, (.35, .45, .55)))
    if t > IGNITION - .1:
        b = max(b, .05 + .95 * sm(t, IGNITION - .05, IGNITION + .55))
    return b * (1 - sm(t, 25.8, 27.2))


def flash(t):
    return gauss(t, IGNITION, .07) + .35 * sum(gauss(t, p, .04) for p in POPS)


def speed(t):  # virtual travel speed in m/s
    return 38. * sm(t, IGNITION + .1, 18.2) * (1 - sm(t, 25.5, 28.6))


_T = np.linspace(0, DURATION + 1, 31001)
_DT = _T[1] - _T[0]
_TRAVEL = np.cumsum([speed(x) for x in _T]) * _DT
_FLOW = np.cumsum([.74 + .9 * boost(x) + .012 * speed(x) for x in _T]) * _DT


def travel(t):
    return float(np.interp(t, _T, _TRAVEL))


def flow_phase(t):
    return float(np.interp(t, _T, _FLOW))


def board(t):
    return sm(t, 27.2, 29.6)


def car_pose(t):
    b = boost(t); s = speed(t)
    accel = (speed(t + .05) - speed(t - .05)) / .1
    pitch = .0016 * accel  # nose lifts on launch, dives on braking
    recoil = -.06 * gauss(t, IGNITION, .16)
    vib = .004 * (s / 38) * math.sin(t * 61) + .003 * b * math.sin(t * 15)
    return trans(recoil, -.035 * b + vib, 0) @ rot(.012 * b + pitch, 'z') @ rot(.006 * math.sin(t * .6) * b, 'y')


# ---------------------------------------------------------------- shots
SHOTS = [  # (start, end, name)
    (0.0, 3.2, 'heart'), (3.2, 8.0, 'flood'), (8.0, 12.0, 'lamps'), (12.0, 17.0, 'ignition'),
    (17.0, 22.4, 'run'), (22.4, 26.4, 'chase'), (26.4, 30.0, 'board')]


def shot_index(t):
    for i, (a, b, _) in enumerate(SHOTS):
        if t < b:
            return i
    return len(SHOTS) - 1


def camera(t, shot):
    a0, a1, name = SHOTS[shot]
    q = smooth((t - a0) / (a1 - a0)); roll = 0.
    if name == 'heart':
        tgt = (-.24, 1.18, 0); dist = 3.5 - .9 * q; az = 62 - 10 * q; el = 22 - 4 * q; fov = 24
    elif name == 'flood':
        tgt = (1.05 + .25 * q, .88, .05); dist = 4.5 - .5 * q; az = 18 + 58 * q; el = 50 - 15 * q; fov = 32
    elif name == 'lamps':
        tgt = (.4, .62, 0); dist = 8.3 - 1.2 * q; az = 12 + 18 * q; el = 3.5 + 2.5 * q; fov = 27
    elif name == 'ignition':
        tgt = (-2.15, .64, 0); dist = 6.3 - .8 * q; az = 142 + 14 * q; el = 9 + 3 * q; fov = 30
    elif name == 'run':
        tgt = (-1.0, .70, 0); dist = 9.6 - 1.8 * q; az = 118 - 22 * q; el = 5 + 3 * q; fov = 30; roll = -.02 * q
    elif name == 'chase':
        tgt = (.6, .70, 0); dist = 7.6 - 1.6 * q; az = 24 - 38 * q; el = 4 + 3 * q; fov = 34; roll = .015
    else:
        tgt = (0, .2, 1.4 * q); dist = 9.5 + 22 * q; az = 40 + 22 * q; el = 20 + 38 * q; fov = 30 + 4 * q
    az = math.radians(az); el = math.radians(el); tgt = np.array(tgt, dtype=float)
    eye = tgt + dist * np.array([math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el)])
    # Shake: speed rumble plus an ignition kick, from smooth noise so it reads as a rig.
    amp = .010 * speed(t) / 38 + .07 * math.exp(-max(0., t - IGNITION) / .22) * (t > IGNITION - .02) + .015 * sum(gauss(t, p, .05) for p in POPS)
    n = lambda k: math.sin(t * 23.1 + k) * .6 + math.sin(t * 37.7 + 2 * k) * .4
    eye = eye + amp * np.array([n(0), n(1), n(2)])
    roll += amp * .5 * n(3)
    return eye, tgt, fov, roll, amp


# ---------------------------------------------------------------- world
class World:
    def __init__(self, g):
        self.parts = parts = {}

        def mesh(name, hero=False):
            m = Mesh(); m.name = name; m.hero = hero; m.variant = VESPER; parts[name] = m; return m

        from car_geometry import build_car
        from boosters import build_boosters
        body, inside, wheel = build_car(mesh, showcase.ellipsoid, showcase.torus, showcase.wire, showcase.transform_new, style=VESPER)
        self.ribbons = build_veins(mesh, body)
        build_boosters(mesh, showcase.torus)
        # Replace the two-shell plume with three shells (core, sheath, haze).
        jet = mesh('jets')
        for side in (-1, 1):
            for layer in (0., 1., 2.):
                for i in range(96):
                    a = i / 96; b = (i + 1) / 96
                    for j in range(24):
                        t0 = j * 2 * math.pi / 24; t1 = (j + 1) * 2 * math.pi / 24
                        for u, q in [(a, t0), (b, t0), (b, t1), (a, t0), (b, t1), (a, t1)]:
                            jet.data.append([u, q, layer, 0, 1, 0, float(side), 0, 0, layer, u, q / (2 * math.pi)])
        sparks = mesh('boostSparks'); rng = np.random.default_rng(909)
        for side in (-1, 1):
            for i in range(420):
                r = rng.random(3); seed = rng.random()
                for uv in [(-1, -1), (1, -1), (1, 1), (-1, -1), (1, 1), (-1, 1)]:
                    sparks.data.append([*r, 0, 1, 0, float(side), 0, 0, seed, *uv])
        for m in parts.values():
            recolor(m, VESPER)
        bead = Mesh(); bead.name = 'bead'; bead.sphere((0, 0, 0), 1., 'white', n=32, m=16); self.bead = bead
        floor = Mesh(); floor.name = 'floor'
        floor.face([(-90, -.018, 90), (90, -.018, 90), (90, -.018, -90), (-90, -.018, -90)], '#080d18'); self.floor = floor
        for m in list(parts.values()) + [bead, floor]:
            m.upload(g)
        print('Vesper geometry:', sum(m.count // 3 for m in parts.values()), 'triangles;', len(self.ribbons), 'arteries', flush=True)

    def objects(self, t):
        m = self.parts; pose = car_pose(t); d = deploy(t)
        names = ['shell', 'interior', 'filament', 'frontlava', 'taillava', 'lavachannels', 'plasma', 'glass', 'veinBeds', 'veins', 'boosterHousing', 'boostercore']
        out = [(m[k], pose) for k in names]
        spin = -travel(t) / .435
        for xx in (-1.38, 1.38):
            for side in (-1, 1):
                steer = .02 * math.sin(t * .7) if xx > 0 else 0.
                out.append((m['wheel'], trans(xx, .44, side * .98 * STYLES[VESPER]['width']) @ rot(steer, 'y') @ rot(spin, 'z')))
        for side in (-1, 1):
            for j in range(6):
                a = j * math.pi / 3; r = .213 + d * .041
                q = (-2.62 - d * .12, .48 + math.cos(a) * r, side * .53 + math.sin(a) * r)
                out.append((m['petal'], pose @ trans(*q) @ rot(a, 'x') @ rot(d * .14, 'z')))
        return out, pose

    def pulses(self, t, pose):
        """World positions and strengths of the travelling vein pulses (and the flood heads)."""
        ff = fill_front(t); dr = drain_front(t); ph = flow_phase(t); cl = cool(t); b = boost(t)
        found = []
        for r in self.ribbons:
            d = r['d']; M = r['phase']; lo, hi = d[0], d[-1]
            for k in range(-2, 40):
                x = (.5 + ph - M + k) / .48
                if x > hi:
                    break
                if x < lo or x + M > ff or x > dr:
                    continue
                found.append((x, r, (.75 + .55 * b) * (1 - .6 * cl)))
            head = ff - M
            if lo < head < hi and ff < 3.4:
                found.append((head, r, 1.7))
        found.sort(key=lambda f: -f[2])
        out = []
        for x, r, w in found[:24]:
            p = np.array([np.interp(x, r['d'], r['p'][:, k]) for k in range(3)])
            wp = pose @ np.array([*p, 1.])
            out.append((*wp[:3], w))
        return out


BEADS = []  # (x, z, team) Barah Goti start: 12 a side, centre empty (the car sits there)
for row in range(5):
    for col in range(5):
        if (row, col) == (2, 2):
            continue
        team = 0 if (row < 2 or (row == 2 and col > 2)) else 1
        BEADS.append(((col - 2) * BOARD, (row - 2) * BOARD, team))


def bead_pop(t, i):
    x, z, _ = BEADS[i]
    start = 27.9 + math.hypot(x, z) / 16. * 1.2 + i * .006
    q = min(1., max(0., (t - start) / .35))
    return 0. if q <= 0 else 1 + 2.2 * (q - 1) ** 3 + 1.2 * (q - 1) ** 2  # back-out


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self, w, h):
        self.w = w; self.h = h; self.g = g = GL(w, h)
        self.atlas = g.tex(1024, 512, showcase.atlas()); self.world = World(g)
        P = lambda v, f: g.program(shader(v), shader(f))
        self.main = P('object.vert', 'object.frag'); self.shadow = P('object.vert', 'shadow.frag')
        self.lava = P('object.vert', 'plasma.frag'); self.glass = P('object.vert', 'glass.frag')
        self.jet = P('jet.vert', 'jet.frag'); self.spark = P('spark.vert', 'spark.frag')
        self.vein = P('object.vert', 'vein.frag'); self.blaze = P('blaze.vert', 'blaze.frag')
        self.sky = P('full.vert', 'sky.frag'); self.floor = P('object.vert', 'floor.frag')
        self.beadp = P('object.vert', 'bead.frag')
        self.bloom = P('full.vert', 'bloom.frag'); self.comp = P('full.vert', 'composite.frag')
        self.fb, self.tex = g.framebuffer(w, h, True)
        self.qw, self.qh = w // 4, h // 4; self.ew, self.eh = w // 8, h // 8
        self.q1 = g.framebuffer(self.qw, self.qh); self.q2 = g.framebuffer(self.qw, self.qh)
        self.e1 = g.framebuffer(self.ew, self.eh); self.e2 = g.framebuffer(self.ew, self.eh)
        self.s1 = g.framebuffer(self.qw, self.qh); self.s2 = g.framebuffer(self.qw, self.qh)
        self.rf, self.rt = g.framebuffer(w // 3, h // 3, True)
        self.sd = g.tex(3072, 3072, depth=True); f = C.c_uint(); g.glGenFramebuffers(1, C.byref(f)); self.sf = f.value
        g.glBindFramebuffer(0x8D40, self.sf); g.glFramebufferTexture2D(0x8D40, 0x8D00, 0x0DE1, self.sd, 0); g.glDrawBuffer(0); g.glReadBuffer(0)
        self.pixels = np.empty((h, w, 3), np.uint8)
        g.glBlendFunc = g.g.glBlendFunc; g.glBlendFunc.argtypes = [C.c_uint, C.c_uint]; g.glBlendFunc.restype = None
        g.glUniform4fv = g.g.glUniform4fv; g.glUniform4fv.argtypes = [C.c_int, C.c_int, C.POINTER(C.c_float)]; g.glUniform4fv.restype = None
        self.lightdir = normalize((.3, .83, .50)); self.frame = np.eye(4, dtype=np.float32)

    def bindtex(self, unit, tex):
        self.g.glActiveTexture(0x84C0 + unit); self.g.glBindTexture(0x0DE1, tex)

    def sampler(self, p, name, unit):
        self.g.glUniform1i(self.g.glGetUniformLocation(p, name.encode()), unit)

    def fs(self, p, fb, w, h):
        g = self.g; g.glBindFramebuffer(0x8D40, fb); g.glViewport(0, 0, w, h); g.glDisable(0x0B71); g.glUseProgram(p); g.glBindVertexArray(g.emptyvao); g.glDrawArrays(4, 0, 3)

    def uniforms(self, p, t, eye, reflection=0.):
        g = self.g; g.glUseProgram(p)
        for k, v in [('time', t), ('eye', eye), ('charge', charge(t)), ('lightDir', self.lightdir), ('resolution', (self.w, self.h)),
                     ('boost', boost(t)), ('reflectionPass', reflection), ('flowPhase', flow_phase(t)), ('fillFront', fill_front(t)),
                     ('drainFront', drain_front(t)), ('heartI', heart(t)), ('lampI', lamp(t)), ('speed', speed(t)), ('travel', travel(t)),
                     ('flash', flash(t)), ('board', board(t)), ('cool', cool(t)), ('carFrame', self.frame), ('carInverse', np.linalg.inv(self.frame)),
                     ('boardSpacing', BOARD)]:
            g.u(p, k, v)

    def set_pulses(self, p):
        g = self.g; arr = np.zeros((24, 4), np.float32)
        for i, q in enumerate(self.pulse_list):
            arr[i] = q
        g.glUniform4fv(g.glGetUniformLocation(p, b'pulses'), 24, arr.ctypes.data_as(C.POINTER(C.c_float)))
        g.glUniform1i(g.glGetUniformLocation(p, b'pulseCount'), len(self.pulse_list))

    def car(self, t, objects, vp, eye, view, reflection=False):
        g = self.g; parts = self.world.parts
        mirror = scale(1, -1, 1) if reflection else np.eye(4, dtype=np.float32); ref = float(reflection)
        self.uniforms(self.main, t, eye, ref); g.u(self.main, 'vp', vp); g.u(self.main, 'lightvp', self.lv); self.set_pulses(self.main)
        self.bindtex(0, self.sd); self.bindtex(1, self.atlas); self.sampler(self.main, 'shadowmap', 0); self.sampler(self.main, 'atlas', 1)
        special = ['plasma', 'glass', 'frontlava', 'taillava', 'lavachannels', 'boostercore', 'veins']
        for m, M in objects:
            if m.name not in special:
                m.draw(self.main, mirror @ M)
        self.uniforms(self.lava, t, eye, ref); g.u(self.lava, 'vp', vp)
        kinds = {'plasma': 0, 'frontlava': 1, 'taillava': 2, 'lavachannels': 3, 'boostercore': 4}
        for m, M in objects:
            if m.name in kinds:
                g.u(self.lava, 'lavaKind', kinds[m.name]); m.draw(self.lava, mirror @ M)
        self.uniforms(self.vein, t, eye, ref); g.u(self.vein, 'vp', vp)
        for m, M in objects:
            if m.name == 'veins':
                m.draw(self.vein, mirror @ M)
        # Beads of the final board.
        if board(t) > 0:
            self.uniforms(self.beadp, t, eye, ref); g.u(self.beadp, 'vp', vp)
            for i, (x, z, team) in enumerate(BEADS):
                s = bead_pop(t, i)
                if s <= 0:
                    continue
                g.u(self.beadp, 'beadCenter', (x, (.17 * s) * (-1 if reflection else 1), z)); g.u(self.beadp, 'beadTeam', float(team)); g.u(self.beadp, 'beadPop', min(1.2, s))
                self.world.bead.draw(self.beadp, mirror @ trans(x, .0, z) @ scale(.42 * s, .30 * s, .42 * s))
        self.uniforms(self.glass, t, eye, ref); g.u(self.glass, 'vp', vp)
        g.glEnable(0x0BE2); g.glBlendFunc(0x0302, 0x0303); g.glDepthMask(0)
        for m, M in objects:
            if m.name == 'glass':
                m.draw(self.glass, mirror @ M)
        self.uniforms(self.jet, t, eye, ref); g.u(self.jet, 'vp', vp); g.glBlendFunc(0x0302, 1)
        parts['jets'].draw(self.jet, mirror @ self.frame)
        self.uniforms(self.blaze, t, eye, ref); g.u(self.blaze, 'vp', vp); parts['blaze'].draw(self.blaze, mirror @ self.frame)
        if not reflection:
            self.uniforms(self.spark, t, eye, 0); g.u(self.spark, 'vp', vp); g.u(self.spark, 'cameraRight', view[0, :3]); g.u(self.spark, 'cameraUp', view[1, :3])
            parts['boostSparks'].draw(self.spark, self.frame)
        g.glDepthMask(1); g.glDisable(0x0BE2)

    def render(self, t, shot=None, seed=0.):
        g = self.g; shot = shot_index(t) if shot is None else shot
        eye, target, fov, roll, amp = camera(t, shot)
        view = lookat(eye, target, roll); vp = perspective(fov, self.w / self.h, .12, 200) @ view
        self.lightdir = normalize((.24 + .06 * math.sin(t * .16), .85, .48 + .07 * math.cos(t * .2)))
        self.lv = ortho(-13, 13, -11, 11, .1, 60) @ lookat(self.lightdir * 26, (0, .4, 0))
        objects, pose = self.world.objects(t); self.frame = pose
        self.pulse_list = self.world.pulses(t, pose)
        g.glEnable(0x0B71); g.glBindFramebuffer(0x8D40, self.sf); g.glViewport(0, 0, 3072, 3072); g.glClear(0x100)
        self.uniforms(self.shadow, t, eye); g.u(self.shadow, 'vp', self.lv); g.u(self.shadow, 'lightvp', self.lv)
        for m, M in objects:
            if m.name not in ('glass', 'veins'):
                m.draw(self.shadow, M)
        g.glBindFramebuffer(0x8D40, self.rf); g.glViewport(0, 0, self.w // 3, self.h // 3); g.glClearColor(0, 0, 0, 0); g.glClear(0x4000 | 0x100)
        self.car(t, objects, vp, eye, view, True)
        g.glBindFramebuffer(0x8D40, self.fb); g.glViewport(0, 0, self.w, self.h); g.glClear(0x4000 | 0x100)
        self.uniforms(self.sky, t, eye); self.fs(self.sky, self.fb, self.w, self.h); g.glEnable(0x0B71)
        self.uniforms(self.floor, t, eye); g.u(self.floor, 'vp', vp); g.u(self.floor, 'lightvp', self.lv)
        rings = np.full((4, 4), -1., np.float32)
        for i, p in enumerate(POPS + (IGNITION,)):
            if t >= p:
                rings[i] = (-2.95, 0., 0., t - p)
        g.glUniform4fv(g.glGetUniformLocation(self.floor, b'rings'), 4, rings.ctypes.data_as(C.POINTER(C.c_float)))
        self.bindtex(0, self.sd); self.bindtex(2, self.rt); self.sampler(self.floor, 'shadowmap', 0); self.sampler(self.floor, 'reflectionMap', 2)
        self.world.floor.draw(self.floor, np.eye(4, dtype=np.float32))
        self.car(t, objects, vp, eye, view, False)
        # Post: bloom at 1/4 and 1/8, an anamorphic streak from the hottest pixels.
        b = self.bloom; g.glUseProgram(b); self.sampler(b, 'src', 0)

        def blur(srcTex, dst, w, h, ext, step):
            self.bindtex(0, srcTex); g.glUseProgram(b); g.u(b, 'extract', ext); g.u(b, 'stepv', step); self.fs(b, dst, w, h)
        blur(self.tex, self.q1[0], self.qw, self.qh, 1., (1 / self.qw, 0)); blur(self.q1[1], self.q2[0], self.qw, self.qh, 0., (0, 1 / self.qh))
        blur(self.q2[1], self.q1[0], self.qw, self.qh, 0., (3 / self.qw, 0)); blur(self.q1[1], self.q2[0], self.qw, self.qh, 0., (0, 3 / self.qh))
        blur(self.tex, self.e1[0], self.ew, self.eh, 1.4, (2 / self.ew, 0)); blur(self.e1[1], self.e2[0], self.ew, self.eh, 0., (0, 2 / self.eh))
        blur(self.e2[1], self.e1[0], self.ew, self.eh, 0., (5 / self.ew, 0)); blur(self.e1[1], self.e2[0], self.ew, self.eh, 0., (0, 5 / self.eh))
        blur(self.tex, self.s1[0], self.qw, self.qh, 2.4, (1.5 / self.qw, 0))
        src, dst = self.s1, self.s2
        for k in (4., 9., 18., 30.):
            blur(src[1], dst[0], self.qw, self.qh, 0., (k / self.qw, 0)); src, dst = dst, src
        c = self.comp; self.uniforms(c, t, eye)
        self.bindtex(0, self.tex); self.bindtex(1, self.q2[1]); self.bindtex(3, self.e2[1]); self.bindtex(4, src[1])
        self.sampler(c, 'src', 0); self.sampler(c, 'glowA', 1); self.sampler(c, 'glowB', 3); self.sampler(c, 'streak', 4)
        g.u(c, 'pixel', (1 / self.w, 1 / self.h)); g.u(c, 'shake', amp * 10); g.u(c, 'frameSeed', seed)
        L = .2 + boost(t) * 3.4 * (1 + speed(t) * .01)
        for i, side in enumerate((-1, 1)):
            for key, x in [('heatA', -2.75), ('heatB', -2.75 - L)]:
                p = vp @ pose @ np.array([x, .48, side * .53, 1]); uv = p[:2] / p[3] * .5 + .5; g.u(c, key + str(i), uv)
        self.fs(c, 0, self.w, self.h)
        g.glReadPixels(0, 0, self.w, self.h, 0x1907, 0x1401, self.pixels.ctypes.data_as(C.c_void_p))
        return self.pixels[::-1].astype(np.float32)

    def frame_at(self, t, subframes=3, shutter=.5):
        """Average sub-frames across an open shutter (never across a cut)."""
        shot = shot_index(t); a, b, _ = SHOTS[shot]
        acc = None
        for k in range(subframes):
            off = ((k + .5) / subframes - .5) * shutter / FPS if subframes > 1 else 0.
            tt = min(max(t + off, a), b - 1e-4)
            im = self.render(tt, shot, seed=t * 7.1 + k)
            acc = im if acc is None else acc + im
        return overlay(Image.fromarray(np.clip(acc / subframes, 0, 255).astype(np.uint8)), t)


def overlay(im, t):
    w, h = im.size; lay = Image.new('RGBA', im.size); d = ImageDraw.Draw(lay)
    bar = round(h * .045); d.rectangle((0, 0, w, bar), fill='#04020a'); d.rectangle((0, h - bar, w, h), fill='#04020a')
    if t > 28.4:
        a = int(255 * smooth((t - 28.4) / .5) * (1 - smooth((t - 29.55) / .4)))
        f1 = ImageFont.truetype(FONT, round(h * .070)); f2 = ImageFont.truetype(FONT, round(h * .024))
        x = round(w * .055); y = round(h * .74)
        for k in range(40):  # soft dark backing so the title sits above the lattice
            d.rectangle((0, y - h * .06 + k * h * .006, w * .42, y - h * .06 + (k + 1) * h * .006), fill=(4, 2, 10, int(a * .35 * math.sin(math.pi * k / 40))))
        d.text((x, y), 'VESPER / 09', font=f1, fill=(255, 107, 242, a))
        d.text((x + 3, y + round(h * .085)), 'AFTERLIGHT  ·  MAGENTA CUT', font=f2, fill=(214, 190, 255, int(a * .85)))
    if t < .5:
        d.rectangle((0, 0, w, h), fill=(4, 2, 10, int(255 * (1 - smooth(t / .5)))))
    if t > 29.55:
        d.rectangle((0, 0, w, h), fill=(4, 2, 10, int(255 * smooth((t - 29.55) / .45))))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


STILLS = [(1.45, 'heart'), (5.0, 'flood'), (9.6, 'lamps'), (13.0, 'deploy'), (15.3, 'ignition'), (19.5, 'run'),
          (24.5, 'chase'), (27.6, 'cooldown'), (29.0, 'board')]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stills', action='store_true'); p.add_argument('--width', type=int, default=1920); p.add_argument('--height', type=int, default=1080)
    p.add_argument('--start', type=float, default=0.); p.add_argument('--seconds', type=float, default=DURATION)
    p.add_argument('--subframes', type=int, default=3); p.add_argument('--output', default=str(ROOT / 'VESPER_picture.mp4'))
    p.add_argument('--outdir', default=str(ROOT / 'renders'))
    a = p.parse_args()
    r = Renderer(a.width, a.height)
    if a.stills:
        out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
        for t, name in STILLS:
            r.frame_at(t, a.subframes).save(out / f'{name}.png'); print('STILL', name, flush=True)
        return
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{a.width}x{a.height}', '-r', str(FPS), '-i', '-', '-an',
           '-vf', 'scale=1920:1080:flags=lanczos:out_color_matrix=bt709', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', a.output]
    out = subprocess.Popen(cmd, stdin=subprocess.PIPE); begin = time.time()
    f0 = round(a.start * FPS); n = round(a.seconds * FPS)
    for i in range(f0, f0 + n):
        t = i / FPS; sf = a.subframes + (2 if speed(t) > 4 or abs(t - IGNITION) < .4 else 0)
        out.stdin.write(r.frame_at(t, sf).tobytes())
        if i % 30 == 0:
            print('FRAME', i, 'elapsed', round(time.time() - begin, 1), flush=True)
    out.stdin.close(); assert out.wait() == 0; print('PICTURE COMPLETE', a.output, flush=True)


if __name__ == '__main__':
    main()
