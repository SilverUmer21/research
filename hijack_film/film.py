"""THE HIJACK - a 30-second Afterlight story film that ends on the blitzedo reveal.

Story (HIJACK TWELVE in one move):
  0-4 s      COLD     Vesper sits dead and grey on the Barah Goti board; Glacier (cyan) and
                      Cinder (orange) idle, alive. The 12-notch Switch ring fills. A failing heartbeat.
  4-6.6 s    SWITCH   The ring completes. Vesper's heart slams; a magenta hook races to Glacier.
  6.6-14.5 s STEAL    Cyan drains out of Glacier and floods Vesper from the nose; then orange from
                      Cinder, from the tail. Rivals go grey; Vesper's lava and heart turn prism.
  14.5-17.5  IGNITE   Petals open; pops in cyan, orange and magenta; prism ignition.
  17.5-21 s  CAPTURE  Slow-motion boost-jump over Glacier, which dissolves into cyan embers.
  21-24.4 s  OWN IT   Hard landing; prism floods the whole board from the landing point.
  24.4-30 s  BLITZEDO Lava races ahead and the blitzedo letters erupt from the floor.

Reuses the unchanged Afterlight cars (afterlight/) and Vesper's artery paths (vesper/veins_plus.py).
"""
import sys, math, argparse, subprocess, time
import ctypes as C
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'afterlight')); sys.path.insert(0, str(ROOT.parent / 'vesper'))
import showcase  # noqa: E402
from engine import GL, Mesh, trans, rot, scale, normalize, lookat, perspective, ortho, smooth  # noqa: E402
from styles import STYLES, recolor  # noqa: E402
from veins_plus import build_veins  # noqa: E402

FONT = str(ROOT.parent / 'afterlight' / 'fonts' / 'BarlowCondensed-Bold.ttf')
FPS = 30; DURATION = 30.0
S = 6.0                     # board point spacing (m)
CINDER, GLACIER, VESPER = 0, 1, 2
LOGO_X, LOGO_W, LOGO_T = 22.0, 14.0, .7
MAG, CYA, ORA = (1., .04, .58), (.02, .90, 1.), (1., .36, .02)


def shader(name):
    return (ROOT / 'shaders' / name).read_text().replace('#include "common.glsl"', (ROOT / 'shaders' / 'common.glsl').read_text())


def sm(t, a, b):
    return smooth((t - a) / (b - a))


def gauss(t, c, w):
    return math.exp(-((t - c) / w) ** 2)


def lin(c):
    c = np.array(c, float); return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


# ------------------------------------------------------------------ story timeline
SWITCH = 4.0
POPS = (15.30, 15.70, 16.05)
IGNITION = 16.45
JUMP0, JUMP1 = 17.5, 21.0
LAND = JUMP1
LOGO0 = 25.0
FAIL_BEATS = (0.9, 2.1, 3.15)


def vesper_motion(t):
    """x, y, pitch and horizontal speed of Vesper."""
    if t < JUMP0:
        return 0., 0., 0., 0.
    if t < JUMP1:
        u = (t - JUMP0) / (JUMP1 - JUMP0)
        s = u + .8 * math.sin(2 * math.pi * u) / (2 * math.pi)        # fast-slow-fast: slow motion at the apex
        ds = (1 + .8 * math.cos(2 * math.pi * u)) / (JUMP1 - JUMP0)
        x = 2 * S * s; y = 11.2 * s * (1 - s)
        pitch = .75 * math.atan(11.2 * (1 - 2 * s) / (2 * S))
        return x, y, pitch, 2 * S * ds
    u = min(1., (t - JUMP1) / 1.6)
    x = 2 * S + 2.2 * (1 - (1 - u) ** 3)
    y = -.10 * gauss(t, LAND + .03, .08)
    return x, y, -.05 * gauss(t, LAND + .06, .12), 2.2 * 3 * (1 - u) ** 2 / 1.6 if u < 1 else 0.


_T = np.linspace(0, DURATION + 1, 31001); _DT = _T[1] - _T[0]


def v_boost(t):
    b = sum(a * gauss(t, p, .06) for p, a in zip(POPS, (.35, .45, .55)))
    if t > IGNITION - .1:
        b = max(b, .05 + .95 * sm(t, IGNITION - .05, IGNITION + .55))
    return b * (1 - sm(t, 21.3, 22.8))


_FLOW = np.cumsum([.74 + .9 * v_boost(x) for x in _T]) * _DT
_VX = np.cumsum([vesper_motion(x)[3] for x in _T]) * _DT


def flow_phase(t):
    return float(np.interp(t, _T, _FLOW))


def car_state(v, t):
    st = dict(boost=0., flash=0., deploy=.05, lamp=0., dissolve=0., cool=0., drain=99., fill=99., fronts=(-99., 99.))
    if v == VESPER:
        cyan = sm(t, 7.6, 10.0); orange = sm(t, 11.4, 13.8)
        st['alive'] = .10 + .90 * sm(t, SWITCH, SWITCH + .6)
        st['fill'] = 0. if t < SWITCH else 3.6 * (1 - (1 - min(1., (t - SWITCH) / 2.2)) ** 2)
        st['mixW'] = (1., 1. if t > 7.6 else 0., 1. if t > 11.4 else 0.)
        st['fronts'] = (3. - 6. * cyan, -3. + 6. * orange)
        st['desat'] = max(0., .92 - .45 * sm(t, SWITCH, SWITCH + 1.) - .25 * cyan - .22 * orange)
        h = .10 + .06 * math.sin(t * 13) * math.sin(t * 7.3)
        h += sum(a * gauss(t, b, .07) for b, a in zip(FAIL_BEATS, (.45, .30, .18)))
        h += 1.7 * gauss(t, SWITCH, .09) + .8 * gauss(t, SWITCH + .2, .08)
        h += .55 * sm(t, SWITCH, SWITCH + .5) + .5 * gauss(t, 10.0, .25) + .6 * gauss(t, 13.8, .25)
        h += .25 * v_boost(t) + .9 * gauss(t, IGNITION, .3) + .7 * gauss(t, LAND, .2)
        st['heart'] = h
        st['charge'] = .05 + .95 * sm(t, SWITCH, 13.8)
        if t > 13.9:
            st['lamp'] = .6 if t < 13.97 else (.05 if t < 14.05 else 1.)
        st['deploy'] = .05 + .95 * sm(t, 14.6, 15.4)
        st['boost'] = v_boost(t)
        st['flash'] = gauss(t, IGNITION, .07) + .35 * sum(gauss(t, p, .04) for p in POPS) + .35 * gauss(t, LAND, .06)
        x, y, pitch, _ = vesper_motion(t)
        b = st['boost']; ground = 1. if (t < JUMP0 or t > JUMP1) else 0.
        recoil = -.06 * gauss(t, IGNITION, .16)
        vib = (.003 * b * math.sin(t * 15)) * ground
        st['pose'] = trans(x + recoil * ground, y - .035 * b * ground + vib, 0) @ rot(pitch + .012 * b * ground, 'z')
        st['spin'] = -float(np.interp(t, _T, _VX)) / .435
        return st
    t0 = 7.0 if v == GLACIER else 10.8
    st['alive'] = 1 - .97 * sm(t, t0, t0 + 2.9)
    st['mixW'] = (0., 1., 0.) if v == GLACIER else (0., 0., 1.)
    st['drain'] = 99. if t < t0 else 3.3 - 3.3 * sm(t, t0, t0 + 2.9)
    st['desat'] = .85 * (1 - st['alive'])
    st['heart'] = (.55 + .2 * math.sin(t * 6 + v)) * st['alive']
    st['charge'] = .9 * st['alive'] + .1
    st['lamp'] = .85 * st['alive']
    if v == GLACIER:
        st['dissolve'] = sm(t, 18.7, 20.3)
        st['pose'] = trans(S, 0, 0) @ rot(-math.pi / 2, 'y')
    else:
        st['pose'] = trans(0, 0, -S)
    st['spin'] = 0.
    return st


def streams(t):
    """Up to four energy streams racing along board lines: (a, b, rgb, head, tail, intensity, width, prism)."""
    out = []
    def add(a, b, col, t0, t1, fade0, fade1, inten, width, prism=0.):
        if t0 <= t <= fade1:
            out.append((a, b, col, sm(t, t0, t1), sm(t, fade0, fade1) if fade0 < fade1 else 0., inten, width, prism))
    if t < 10.0:
        add((0, 0), (S, 0), MAG, SWITCH + .15, SWITCH + .9, 9.6, 9.95, 1.1 - .5 * sm(t, 6.4, 7.0), .12)
        add((S, 0), (0, 0), CYA, 6.6, 7.6, 9.6, 10.2, 1.3, .17)
    elif t < 14.3:
        add((0, 0), (0, -S), MAG, 10.0, 10.6, 13.5, 13.9, 1.1 - .5 * sm(t, 10.6, 11.0), .12)
        add((0, -S), (0, 0), ORA, 10.8, 11.4, 13.6, 14.2, 1.3, .17)
    elif 24.3 < t < 26.4:
        for z, col, pr in ((-2.4, MAG, 0.), (-.8, CYA, 0.), (.8, ORA, 0.), (2.4, MAG, 1.)):
            add((15.2, z), (LOGO_X - .2, z), col, 24.4, 25.0, 25.6, 26.2, 1.4, .13, pr)
    return out[:4]


def beams(t, poses):
    """3D arcs of stolen energy: (start, end, rgb, head, tail, intensity, arch)."""
    heart = lambda v: (poses[v] @ np.array([-.24, 1.23, 0, 1.]))[:3]
    at = lambda v, p: (poses[v] @ np.array([*p, 1.]))[:3]
    out = []
    def add(a, b, col, t0, t1, f0, f1, inten, arch):
        if t0 <= t <= f1:
            out.append((a, b, col, sm(t, t0, t1), sm(t, f0, f1), inten, arch))
    add(heart(VESPER), heart(GLACIER), MAG, SWITCH + .15, SWITCH + .8, 9.4, 9.9, 1. - .5 * sm(t, 6.4, 7.), 1.6)
    add(heart(GLACIER), at(VESPER, (2.0, .95, 0)), CYA, 6.6, 7.5, 9.6, 10.2, 1.25, 2.3)
    add(heart(VESPER), heart(CINDER), MAG, 10.0, 10.6, 13.4, 13.9, 1. - .5 * sm(t, 10.6, 11.), 1.6)
    add(heart(CINDER), at(VESPER, (-2.2, 1.05, 0)), ORA, 10.8, 11.6, 13.6, 14.2, 1.25, 2.3)
    return out


def ring_n(t):
    if t < 6.6:
        return 8 + math.floor(4 * min(1., max(0., (t - .6) / 3.35)))
    return min(12., math.floor((t - 6.6) / 1.4))


def flood(t):
    return (2 * S, 0., 0. if t < LAND else 46. * (1 - (1 - min(1., (t - LAND) / 2.8)) ** 2))


def shock_rings(t):
    ev = [(p, (-2.95, 0.)) for p in POPS] + [(IGNITION, (-2.95, 0.)), (LAND, (2 * S - 0., 0.))]
    out = [(x, z, t - te) for te, (x, z) in ev if 0 <= t - te < 1.6]
    return out[-4:]


def logo_state(t):
    return dict(time=t - LOGO0, I=sm(t, 24.9, 25.5), settle=sm(t, 26.2, 27.9), sweep=(t - 27.5) / .9)


# ------------------------------------------------------------------ cameras
SHOTS = [(0., 4., 'cold'), (4., 6.6, 'switch'), (6.6, 8.8, 'stealC'), (8.8, 10.4, 'hood'), (10.4, 12.4, 'stealO'),
         (12.4, 14.5, 'heart'), (14.5, 17.5, 'ignite'), (17.5, 21., 'jump'), (21., 24.4, 'land'), (24.4, 30., 'logo')]


def shot_index(t):
    for i, (a, b, _) in enumerate(SHOTS):
        if t < b:
            return i
    return len(SHOTS) - 1


def orbit(target, dist, az, el):
    az = math.radians(az); el = math.radians(el)
    return np.array(target, float) + dist * np.array([math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el)])


def camera(t, shot):
    a0, a1, name = SHOTS[shot]; q = smooth((t - a0) / (a1 - a0)); roll = 0.; fov = 32
    vpose = car_state(VESPER, t)['pose']
    local = lambda p: (vpose @ np.array([*p, 1.]))[:3]
    if name == 'cold':
        eye = np.array([-7.0 + 1.2 * q, 1.2 + .2 * q, 5.6 - 1.0 * q]); tgt = np.array([1.0, 1.0, -1.5]); fov = 34
    elif name == 'switch':
        eye = np.array([-8 + 1.5 * q, 9 + 1 * q, 9 - 1 * q]); tgt = np.array([2.0, .5, -2.0]); fov = 38
    elif name == 'stealC':
        eye = np.array([4.2 + .6 * q, 3.0 - .4 * q, 10.6 - 1.4 * q]); tgt = np.array([3., 1.1, 0]); fov = 36
    elif name == 'hood':
        tgt = local((1.0 + .3 * q, .88, .05)); eye = orbit(tgt, 4.2 - .4 * q, 22 + 40 * q, 46 - 10 * q); fov = 32
    elif name == 'stealO':
        eye = np.array([-11 + 1.2 * q, 2.4, -3.2]); tgt = np.array([0., 1.0, -3.]); fov = 40
    elif name == 'heart':
        tgt = local((-.24, 1.18, 0)); eye = orbit(tgt, 3.3 - .8 * q, 64 - 12 * q, 22 - 4 * q); fov = 24
    elif name == 'ignite':
        tgt = local((-2.15, .64, 0)); eye = orbit(tgt, 6.3 - .8 * q, 142 + 14 * q, 9 + 3 * q); fov = 30
    elif name == 'jump':
        x, y, _, _ = vesper_motion(t)
        tgt = np.array([x * .6 + S * .4, .6 + y * .55, 0.]); eye = np.array([4.5 + 2.0 * q, .5 + .8 * q, 8.2 - .8 * q]); fov = 44
    elif name == 'land':
        x, y, _, _ = vesper_motion(t)
        tgt = np.array([x, .8, 0.]); eye = np.array([20.5 - 1.0 * q, .9 + 1.6 * q, 4.2 + 1.2 * q]); fov = 32
    else:
        tgt = np.array([LOGO_X, 1.8 + .2 * q, -.6]); eye = np.array([5.0 + 2.5 * q, 2.3 + 1.3 * q, 4.6 - .4 * q]); fov = 38 - 2 * q
    amp = .07 * math.exp(-max(0., t - IGNITION) / .22) * (t > IGNITION - .02) + .015 * sum(gauss(t, p, .05) for p in POPS)
    amp += .08 * math.exp(-max(0., t - LAND) / .25) * (t > LAND - .02) + .05 * gauss(t, SWITCH, .12)
    amp += .010 * car_state(VESPER, t)['boost'] * (1 if JUMP0 < t < 22 else 0)
    amp += .06 * math.exp(-max(0., t - (LOGO0 + .3)) / .4) * (t > LOGO0 + .28)
    n = lambda k: math.sin(t * 23.1 + k) * .6 + math.sin(t * 37.7 + 2 * k) * .4
    eye = eye + amp * np.array([n(0), n(1), n(2)]); roll += amp * .5 * n(3)
    return eye, tgt, fov, roll, amp


# ------------------------------------------------------------------ world
def build_logo():
    font = ImageFont.truetype(FONT, 420); text = 'blitzedo'
    bb = font.getbbox(text); im = Image.new('L', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), 0)
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), text, font=font, fill=255)
    cols = 600; rows = round(im.height * cols / im.width); cell = LOGO_W / cols
    g = np.array(im.resize((cols, rows), Image.BOX)) > 110
    H = rows * cell; m = Mesh(); m.name = 'logo'
    z0 = -LOGO_W / 2; x0 = LOGO_X; x1 = LOGO_X + LOGO_T

    def quad(pts, n, mat, uvs):
        pts = np.array(pts, float)
        if np.dot(np.cross(pts[1] - pts[0], pts[2] - pts[0]), n) < 0:
            pts = pts[::-1]; uvs = uvs[::-1]
        m.face(pts, 'white', em=mat, uvs=uvs)

    Z = lambda i: z0 + i * cell
    Y = lambda j: (rows - j) * cell          # row 0 is the top
    UV = lambda z, y: ((z - z0) / LOGO_W, y / H)
    for j in range(rows):
        i = 0
        while i < cols:
            if not g[j, i]:
                i += 1; continue
            k = i
            while k < cols and g[j, k]:
                k += 1
            za, zb, ya, yb = Z(i), Z(k), Y(j + 1), Y(j)
            uvs = [UV(za, ya), UV(zb, ya), UV(zb, yb), UV(za, yb)]
            quad([(x0, ya, za), (x0, ya, zb), (x0, yb, zb), (x0, yb, za)], (-1, 0, 0), 0., uvs)
            quad([(x1, ya, za), (x1, ya, zb), (x1, yb, zb), (x1, yb, za)], (1, 0, 0), 1., uvs)
            for jj, yy, nn in ((j - 1, yb, 1), (j + 1, ya, -1)):     # top / bottom edges of the run
                s0 = i
                while s0 < k:
                    if 0 <= jj < rows and g[jj, s0]:
                        s0 += 1; continue
                    s1 = s0
                    while s1 < k and not (0 <= jj < rows and g[jj, s1]):
                        s1 += 1
                    a, b = Z(s0), Z(s1)
                    quad([(x0, yy, a), (x1, yy, a), (x1, yy, b), (x0, yy, b)], (0, nn, 0), 1., [UV(a, yy)] * 2 + [UV(b, yy)] * 2)
                    s0 = s1
            quad([(x0, ya, za), (x1, ya, za), (x1, yb, za), (x0, yb, za)], (0, 0, -1), 1., [UV(za, ya), UV(za, ya), UV(za, yb), UV(za, yb)])
            quad([(x0, ya, zb), (x1, ya, zb), (x1, yb, zb), (x0, yb, zb)], (0, 0, 1), 1., [UV(zb, ya), UV(zb, ya), UV(zb, yb), UV(zb, yb)])
            i = k
    return m, H


class World:
    def __init__(self, g):
        self.cars = {}; self.ribbons = None
        from car_geometry import build_car
        from boosters import build_boosters
        for v in (CINDER, GLACIER, VESPER):
            parts = {}; self.cars[v] = parts

            def mesh(name, hero=False, parts=parts, v=v):
                m = Mesh(); m.name = name; m.hero = hero; m.variant = v; parts[name] = m; return m
            body, inside, wheel = build_car(mesh, showcase.ellipsoid, showcase.torus, showcase.wire, showcase.transform_new, style=v)
            rib = build_veins(mesh, body)
            if v == VESPER:
                self.ribbons = rib
            build_boosters(mesh, showcase.torus)
            jet = mesh('jets')
            for side in (-1, 1):
                for layer in (0., 1., 2.):
                    for i in range(96):
                        a = i / 96; b = (i + 1) / 96
                        for j in range(24):
                            t0 = j * 2 * math.pi / 24; t1 = (j + 1) * 2 * math.pi / 24
                            for u, q in [(a, t0), (b, t0), (b, t1), (a, t0), (b, t1), (a, t1)]:
                                jet.data.append([u, q, layer, 0, 1, 0, float(side), 0, 0, layer, u, q / (2 * math.pi)])
            sparks = mesh('boostSparks'); rng = np.random.default_rng(909 + v)
            for side in (-1, 1):
                for i in range(420):
                    r = rng.random(3); seed = rng.random()
                    for uv in [(-1, -1), (1, -1), (1, 1), (-1, -1), (1, 1), (-1, 1)]:
                        sparks.data.append([*r, 0, 1, 0, float(side), 0, 0, seed, *uv])
            for m in parts.values():
                recolor(m, v)
        burst = Mesh(); burst.name = 'burst'; rng = np.random.default_rng(77)
        for i in range(2600):
            r = rng.random(3); seed = rng.random()
            for uv in [(-1, -1), (1, -1), (1, 1), (-1, -1), (1, 1), (-1, 1)]:
                burst.data.append([*r, 0, 1, 0, 0, 0, 0, seed, *uv])
        self.burst = burst
        beam = Mesh(); beam.name = 'beam'
        for layer in (0., 1.):
            for i in range(80):
                a = i / 80; b = (i + 1) / 80
                for j in range(10):
                    t0 = j * 2 * math.pi / 10; t1 = (j + 1) * 2 * math.pi / 10
                    for u, q in [(a, t0), (b, t0), (b, t1), (a, t0), (b, t1), (a, t1)]:
                        beam.data.append([u, q, layer, 0, 1, 0, 0, 0, 0, layer, u, 0])
        self.beam = beam
        self.logo, self.logoH = build_logo()
        floor = Mesh(); floor.name = 'floor'
        floor.face([(-90, -.018, 90), (90, -.018, 90), (90, -.018, -90), (-90, -.018, -90)], '#080d18'); self.floor = floor
        allm = [m for parts in self.cars.values() for m in parts.values()] + [burst, beam, self.logo, floor]
        for m in allm:
            m.upload(g)
        print('Hijack geometry:', sum(m.count // 3 for m in allm), 'triangles; logo', self.logo.count // 3, 'triangles, height', round(self.logoH, 2), 'm', flush=True)

    def objects(self, v, st):
        m = self.cars[v]; pose = st['pose']; d = st['deploy']
        names = ['shell', 'interior', 'filament', 'frontlava', 'taillava', 'lavachannels', 'plasma', 'glass', 'veinBeds', 'veins', 'boosterHousing', 'boostercore']
        out = [(m[k], pose) for k in names]
        for xx in (-1.38, 1.38):
            for side in (-1, 1):
                out.append((m['wheel'], pose @ trans(xx, .44, side * .98 * STYLES[v]['width']) @ rot(st['spin'], 'z')))
        for side in (-1, 1):
            for j in range(6):
                a = j * math.pi / 3; r = .213 + d * .041
                q = (-2.62 - d * .12, .48 + math.cos(a) * r, side * .53 + math.sin(a) * r)
                out.append((m['petal'], pose @ trans(*q) @ rot(a, 'x') @ rot(d * .14, 'z')))
        return out

    def pulses(self, t, st):
        ff = st['fill']; ph = flow_phase(t); b = st['boost']; fc, fo = st['fronts']; w = st['mixW']
        found = []
        for r in self.ribbons:
            d = r['d']; M = r['phase']; lo, hi = d[0], d[-1]
            for k in range(-2, 40):
                x = (.5 + ph - M + k) / .48
                if x > hi:
                    break
                if x >= lo:
                    found.append((x, r, .75 + .55 * b))
            head = ff - M
            if lo < head < hi and ff < 3.4:
                found.append((head, r, 1.7))
        out = []
        for x, r, wgt in found:
            p = np.array([np.interp(x, r['d'], r['p'][:, k]) for k in range(3)])
            has = [w[0] * (x + r['phase'] <= ff), w[1] * (p[0] > fc), w[2] * (p[0] < fo)]
            if sum(has) <= 0:
                continue
            col = sum(lin(c) * h for c, h in zip((MAG, CYA, ORA), has)) / sum(has)
            out.append((wgt * st['alive'], (st['pose'] @ np.array([*p, 1.]))[:3], col))
        out.sort(key=lambda o: -o[0])
        return out[:24]


# ------------------------------------------------------------------ renderer
class Renderer:
    def __init__(self, w, h):
        self.w = w; self.h = h; self.g = g = GL(w, h)
        self.atlas = g.tex(1024, 512, showcase.atlas()); self.world = World(g)
        P = lambda v, f: g.program(shader(v), shader(f))
        self.main = P('object.vert', 'object.frag'); self.shadow = P('object.vert', 'shadow.frag')
        self.lava = P('object.vert', 'plasma.frag'); self.glass = P('object.vert', 'glass.frag')
        self.jet = P('jet.vert', 'jet.frag'); self.spark = P('spark.vert', 'spark.frag')
        self.vein = P('object.vert', 'vein.frag'); self.blaze = P('blaze.vert', 'blaze.frag')
        self.burstp = P('burst.vert', 'burst.frag'); self.logop = P('logo.vert', 'logo.frag'); self.beamp = P('beam.vert', 'beam.frag')
        self.sky = P('full.vert', 'sky.frag'); self.floor = P('object.vert', 'floor.frag')
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
        for nm in ('glUniform4fv', 'glUniform3fv'):
            fn = getattr(g.g, nm); fn.argtypes = [C.c_int, C.c_int, C.POINTER(C.c_float)]; fn.restype = None; setattr(g, nm, fn)
        self.lightdir = normalize((.3, .83, .50))

    def bindtex(self, unit, tex):
        self.g.glActiveTexture(0x84C0 + unit); self.g.glBindTexture(0x0DE1, tex)

    def sampler(self, p, name, unit):
        self.g.glUniform1i(self.g.glGetUniformLocation(p, name.encode()), unit)

    def arr(self, p, name, data, n):
        a = np.ascontiguousarray(np.array(data, np.float32).reshape(-1)); fn = self.g.glUniform4fv if n == 4 else self.g.glUniform3fv
        fn(self.g.glGetUniformLocation(p, name.encode()), len(a) // n, a.ctypes.data_as(C.POINTER(C.c_float)))

    def fs(self, p, fb, w, h):
        g = self.g; g.glBindFramebuffer(0x8D40, fb); g.glViewport(0, 0, w, h); g.glDisable(0x0B71); g.glUseProgram(p); g.glBindVertexArray(g.emptyvao); g.glDrawArrays(4, 0, 3)

    def uniforms(self, p, t, eye, st, reflection=0.):
        g = self.g; g.glUseProgram(p); fr = st['pose']; ls = logo_state(t)
        for k, v in [('time', t), ('eye', eye), ('charge', st['charge']), ('lightDir', self.lightdir), ('resolution', (self.w, self.h)),
                     ('boost', st['boost']), ('reflectionPass', reflection), ('flowPhase', flow_phase(t)), ('fillFront', st['fill']),
                     ('drainFront', st['drain']), ('heartI', st['heart']), ('lampI', st['lamp']), ('flash', st['flash']), ('cool', st['cool']),
                     ('alive', st['alive']), ('dissolve', st['dissolve']), ('desat', st['desat']), ('mixW', st['mixW']), ('fronts', st['fronts']),
                     ('carFrame', fr), ('carInverse', np.linalg.inv(fr)), ('logoI', ls['I'])]:
            g.u(p, k, v)

    def opaque(self, t, v, st, objs, vp, eye, mirror, ref):
        g = self.g
        self.uniforms(self.main, t, eye, st, ref); g.u(self.main, 'vp', vp); g.u(self.main, 'lightvp', self.lv)
        pl = self.pulse_list if v == VESPER else []
        self.arr(self.main, 'pulses', [(*p, w) for w, p, c in pl] + [(0, 0, 0, 0)] * (24 - len(pl)), 4)
        self.arr(self.main, 'pulseColors', [c for w, p, c in pl] + [(0, 0, 0)] * (24 - len(pl)), 3)
        g.glUniform1i(g.glGetUniformLocation(self.main, b'pulseCount'), len(pl))
        self.arr(self.main, 'logoLights', [(LOGO_X - .3, 1.6, z, 1.) for z in (-4.5, 0., 4.5)], 4)
        self.bindtex(0, self.sd); self.bindtex(1, self.atlas); self.sampler(self.main, 'shadowmap', 0); self.sampler(self.main, 'atlas', 1)
        special = ['plasma', 'glass', 'frontlava', 'taillava', 'lavachannels', 'boostercore', 'veins']
        for m, M in objs:
            if m.name not in special:
                m.draw(self.main, mirror @ M)
        self.uniforms(self.lava, t, eye, st, ref); g.u(self.lava, 'vp', vp)
        kinds = {'plasma': 0, 'frontlava': 1, 'taillava': 2, 'lavachannels': 3, 'boostercore': 4}
        for m, M in objs:
            if m.name in kinds:
                g.u(self.lava, 'lavaKind', kinds[m.name]); m.draw(self.lava, mirror @ M)
        self.uniforms(self.vein, t, eye, st, ref); g.u(self.vein, 'vp', vp)
        for m, M in objs:
            if m.name == 'veins':
                m.draw(self.vein, mirror @ M)

    def transparent(self, t, v, st, objs, vp, eye, view, mirror, ref):
        g = self.g; parts = self.world.cars[v]
        self.uniforms(self.glass, t, eye, st, ref); g.u(self.glass, 'vp', vp)
        g.glEnable(0x0BE2); g.glBlendFunc(0x0302, 0x0303); g.glDepthMask(0)
        for m, M in objs:
            if m.name == 'glass':
                m.draw(self.glass, mirror @ M)
        g.glBlendFunc(0x0302, 1)
        if st['boost'] > .002:
            self.uniforms(self.jet, t, eye, st, ref); g.u(self.jet, 'vp', vp); parts['jets'].draw(self.jet, mirror @ st['pose'])
        if st['alive'] > .05:
            self.uniforms(self.blaze, t, eye, st, ref); g.u(self.blaze, 'vp', vp); parts['blaze'].draw(self.blaze, mirror @ st['pose'])
        if not ref:
            if st['boost'] > .002:
                self.uniforms(self.spark, t, eye, st, 0); g.u(self.spark, 'vp', vp); g.u(self.spark, 'cameraRight', view[0, :3]); g.u(self.spark, 'cameraUp', view[1, :3])
                parts['boostSparks'].draw(self.spark, st['pose'])
            if v == GLACIER and t > 18.7:
                self.uniforms(self.burstp, t, eye, st, 0); g.u(self.burstp, 'vp', vp); g.u(self.burstp, 'cameraRight', view[0, :3]); g.u(self.burstp, 'cameraUp', view[1, :3])
                g.u(self.burstp, 'burstT', t - 18.7); self.world.burst.draw(self.burstp, st['pose'])
        g.glDepthMask(1); g.glDisable(0x0BE2)

    def scene(self, t, states, objs, vp, eye, view, reflection):
        mirror = scale(1, -1, 1) if reflection else np.eye(4, dtype=np.float32); ref = float(reflection)
        for v in (CINDER, GLACIER, VESPER):
            if states[v]['dissolve'] < .999:
                self.opaque(t, v, states[v], objs[v], vp, eye, mirror, ref)
        ls = logo_state(t)
        if ls['time'] > 0:
            g = self.g; p = self.logop; self.uniforms(p, t, eye, states[VESPER], ref); g.u(p, 'vp', vp); g.u(p, 'lightvp', self.lv)
            for k, val in (('logoTime', ls['time']), ('logoH', self.world.logoH), ('rise', min(1., ls['time'] / 1.6)), ('sweep', ls['sweep']), ('settle', ls['settle'])):
                g.u(p, k, val)
            self.world.logo.draw(p, mirror)
        for v in (CINDER, GLACIER, VESPER):
            if states[v]['dissolve'] < .999 or (v == GLACIER and t < 21.5):
                self.transparent(t, v, states[v], objs[v], vp, eye, view, mirror, ref)
        bl = beams(t, {v: states[v]['pose'] for v in states})
        if bl:
            g = self.g; p = self.beamp; self.uniforms(p, t, eye, states[VESPER], ref); g.u(p, 'vp', vp)
            g.glEnable(0x0BE2); g.glBlendFunc(0x0302, 1); g.glDepthMask(0)
            for a, b, col, head, tail, inten, arch in bl:
                for k, val in (('bA', tuple(a)), ('bB', tuple(b)), ('arch', arch), ('width', .045), ('beamColor', tuple(lin(col))),
                               ('head', head), ('tail', tail), ('inten', inten), ('prismMode', 0.)):
                    g.u(p, k, val)
                self.world.beam.draw(p, np.eye(4, dtype=np.float32))
            g.glDepthMask(1); g.glDisable(0x0BE2)

    def render(self, t, shot=None, seed=0.):
        g = self.g; shot = shot_index(t) if shot is None else shot
        eye, target, fov, roll, amp = camera(t, shot)
        view = lookat(eye, target, roll); vp = perspective(fov, self.w / self.h, .12, 220) @ view
        self.lightdir = normalize((.24 + .06 * math.sin(t * .16), .85, .48 + .07 * math.cos(t * .2)))
        c = np.array([target[0], 0, target[2]])
        self.lv = ortho(-17, 17, -14, 14, .1, 70) @ lookat(c + self.lightdir * 30, c)
        states = {v: car_state(v, t) for v in (CINDER, GLACIER, VESPER)}
        objs = {v: self.world.objects(v, states[v]) for v in states}
        self.pulse_list = self.world.pulses(t, states[VESPER])
        g.glEnable(0x0B71); g.glBindFramebuffer(0x8D40, self.sf); g.glViewport(0, 0, 3072, 3072); g.glClear(0x100)
        for v in states:
            self.uniforms(self.shadow, t, eye, states[v]); g.u(self.shadow, 'vp', self.lv); g.u(self.shadow, 'lightvp', self.lv)
            for m, M in objs[v]:
                if m.name not in ('glass', 'veins'):
                    m.draw(self.shadow, M)
        g.glBindFramebuffer(0x8D40, self.rf); g.glViewport(0, 0, self.w // 3, self.h // 3); g.glClearColor(0, 0, 0, 0); g.glClear(0x4000 | 0x100)
        self.scene(t, states, objs, vp, eye, view, True)
        g.glBindFramebuffer(0x8D40, self.fb); g.glViewport(0, 0, self.w, self.h); g.glClear(0x4000 | 0x100)
        vs = states[VESPER]
        self.uniforms(self.sky, t, eye, vs); self.fs(self.sky, self.fb, self.w, self.h); g.glEnable(0x0B71)
        f = self.floor; self.uniforms(f, t, eye, vs); g.u(f, 'vp', vp); g.u(f, 'lightvp', self.lv)
        g.u(f, 'boardSpacing', S); g.u(f, 'ringN', ring_n(t)); g.u(f, 'ringFlash', gauss(t, SWITCH + .1, .35)); g.u(f, 'vBoost', vs['boost']); g.u(f, 'vesperW', vs['mixW'])
        cars = []
        for v in (CINDER, GLACIER, VESPER):
            p = states[v]['pose'][:3, 3]; cars.append((p[0], p[2], states[v]['alive'] * (1 - states[v]['dissolve']), float(v)))
        self.arr(f, 'cars', cars, 4)
        sa, sb, sc = [], [], []
        for a, b, col, head, tail, inten, width, pr in streams(t):
            sa.append((*a, *b)); sb.append((*lin(col), head)); sc.append((tail, inten, width, pr))
        while len(sa) < 4:
            sa.append((0, 0, 0, 0)); sb.append((0, 0, 0, 0)); sc.append((0, 0, 0, 0))
        self.arr(f, 'streamA', sa, 4); self.arr(f, 'streamB', sb, 4); self.arr(f, 'streamC', sc, 4)
        g.u(f, 'flood', flood(t))
        rings = [(x, 0, z, age) for x, z, age in shock_rings(t)]
        rings = [((vs['pose'] @ np.array([x, 0, z, 1.]))[0], 0, (vs['pose'] @ np.array([x, 0, z, 1.]))[2], a) if x < 0 else (x, 0, z, a) for x, _, z, a in rings]
        rings += [(0, 0, 0, -1)] * (4 - len(rings)); self.arr(f, 'rings', rings, 4)
        nz = vs['pose'] @ np.array([-2.75, 0, 0, 1.]); dr = vs['pose'][:3, :3] @ np.array([-1., 0, 0])
        dxz = np.array([dr[0], dr[2]]); dxz /= max(np.linalg.norm(dxz), 1e-6)
        self.arr(f, 'nozzle', [(nz[0], nz[2], dxz[0], dxz[1])], 4)
        self.bindtex(0, self.sd); self.bindtex(2, self.rt); self.sampler(f, 'shadowmap', 0); self.sampler(f, 'reflectionMap', 2)
        self.world.floor.draw(f, np.eye(4, dtype=np.float32))
        self.scene(t, states, objs, vp, eye, view, False)
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
        cp = self.comp; self.uniforms(cp, t, eye, vs)
        self.bindtex(0, self.tex); self.bindtex(1, self.q2[1]); self.bindtex(3, self.e2[1]); self.bindtex(4, src[1])
        self.sampler(cp, 'src', 0); self.sampler(cp, 'glowA', 1); self.sampler(cp, 'glowB', 3); self.sampler(cp, 'streak', 4)
        g.u(cp, 'pixel', (1 / self.w, 1 / self.h)); g.u(cp, 'shake', amp * 10); g.u(cp, 'frameSeed', seed)
        g.u(cp, 'fade', min(1., t / .6) * (1 - sm(t, 29.5, 30.)))
        L = .2 + vs['boost'] * 3.6
        for i, side in enumerate((-1, 1)):
            for key, x in [('heatA', -2.75), ('heatB', -2.75 - L)]:
                p = vp @ vs['pose'] @ np.array([x, .48, side * .53, 1]); uv = p[:2] / p[3] * .5 + .5; g.u(cp, key + str(i), uv)
        self.fs(cp, 0, self.w, self.h)
        g.glReadPixels(0, 0, self.w, self.h, 0x1907, 0x1401, self.pixels.ctypes.data_as(C.c_void_p))
        return self.pixels[::-1].astype(np.float32)

    def frame_at(self, t, subframes=3, shutter=.5):
        shot = shot_index(t); a, b, _ = SHOTS[shot]; acc = None
        for k in range(subframes):
            off = ((k + .5) / subframes - .5) * shutter / FPS if subframes > 1 else 0.
            im = self.render(min(max(t + off, a), b - 1e-4), shot, seed=t * 7.1 + k)
            acc = im if acc is None else acc + im
        return overlay(Image.fromarray(np.clip(acc / subframes, 0, 255).astype(np.uint8)), t)


def overlay(im, t):
    w, h = im.size
    if SWITCH - .05 < t < SWITCH + 1.5:      # the word everyone will remember
        q = (t - SWITCH + .05) / 1.55; a = min(1., q * 8) * (1 - smooth((q - .6) / .4))
        f = ImageFont.truetype(FONT, round(h * .19 * (1.12 - .12 * smooth(q * 3))))
        lay = Image.new('RGBA', im.size); bb = f.getbbox('SWITCH'); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x = (w - tw) / 2 - bb[0]; y = h * .14 - bb[1]; off = round(h * .006 * (1 + 3 * (1 - smooth(q * 4))))
        for dx, col in ((-off, (0, 230, 255)), (off, (255, 92, 10)), (0, (255, 40, 200))):
            d = ImageDraw.Draw(lay); d.text((x + dx, y), 'SWITCH', font=f, fill=(*col, int(150 * a)))
        glow = lay.filter(ImageFilter.GaussianBlur(h * .02))
        ImageDraw.Draw(lay).text((x, y), 'SWITCH', font=f, fill=(255, 245, 255, int(235 * a)))
        im = Image.alpha_composite(Image.alpha_composite(im.convert('RGBA'), glow), lay).convert('RGB')
    lay = Image.new('RGBA', im.size); d = ImageDraw.Draw(lay)
    bar = round(h * .045); d.rectangle((0, 0, w, bar), fill='#04020a'); d.rectangle((0, h - bar, w, h), fill='#04020a')
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


STILLS = [(2.0, 'cold'), (4.4, 'switch'), (7.9, 'steal_cyan'), (9.6, 'hood'), (11.8, 'steal_orange'), (13.6, 'heart'),
          (17.2, 'ignite'), (19.2, 'capture'), (22.6, 'own'), (26.0, 'erupt'), (28.0, 'blitzedo')]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stills', action='store_true'); p.add_argument('--width', type=int, default=1920); p.add_argument('--height', type=int, default=1080)
    p.add_argument('--start', type=float, default=0.); p.add_argument('--seconds', type=float, default=DURATION)
    p.add_argument('--subframes', type=int, default=3); p.add_argument('--output', default=str(ROOT / 'HIJACK_picture.mp4'))
    p.add_argument('--outdir', default=str(ROOT / 'renders')); p.add_argument('--only', default='')
    a = p.parse_args(); r = Renderer(a.width, a.height)
    if a.stills:
        out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
        for t, name in STILLS:
            if a.only and name not in a.only.split(','):
                continue
            r.frame_at(t, a.subframes).save(out / f'{name}.png'); print('STILL', name, flush=True)
        return
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{a.width}x{a.height}', '-r', str(FPS), '-i', '-', '-an',
           '-vf', 'scale=1920:1080:flags=lanczos:out_color_matrix=bt709', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', a.output]
    out = subprocess.Popen(cmd, stdin=subprocess.PIPE); begin = time.time()
    f0 = round(a.start * FPS); n = round(a.seconds * FPS)
    for i in range(f0, f0 + n):
        t = i / FPS; fast = (JUMP0 - .2 < t < 22.5) or abs(t - IGNITION) < .4 or abs(t - SWITCH) < .3
        out.stdin.write(r.frame_at(t, a.subframes + (2 if fast else 0)).tobytes())
        if i % 30 == 0:
            print('FRAME', i, 'elapsed', round(time.time() - begin, 1), flush=True)
    out.stdin.close(); assert out.wait() == 0; print('PICTURE COMPLETE', a.output, flush=True)


if __name__ == '__main__':
    main()
