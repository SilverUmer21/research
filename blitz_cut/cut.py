"""BLITZ CUT - a 30-second, beat-synced edit at 128 BPM that ends on the blitzedo slam.

Slow first: cinematic shots behind the cars and their boosters. Then the build, the drop
and a fast edit: launch, whip pans, crash zooms, a top-down spin, chase, pass-by, barrel roll,
overtake, fly-over, a glitch montage, a slow-motion speed ramp and the logo.

Reuses the story film's renderer (hijack_film/film.py) and the unchanged Afterlight cars.
Every cut sits on the beat grid below, and score.py builds the track on the same grid.
"""
import sys, math, argparse, subprocess, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'hijack_film'))
import film as F  # noqa: E402
from engine import trans, rot, smooth  # noqa: E402

F.ROOT = ROOT                      # load this cut's shaders
FPS = 30; DURATION = 30.0
BPM = 128.; BEAT = 60 / BPM; BAR = 4 * BEAT
CINDER, GLACIER, VESPER = F.CINDER, F.GLACIER, F.VESPER
LANE = {CINDER: -3.4, VESPER: 0., GLACIER: 3.4}
DROP = 8 * BAR                     # 15.0 s
BUILD = 6 * BAR                    # 11.25 s
RAMP0, RAMP1 = 13 * BAR, 14 * BAR  # slow-motion bar 24.375-26.25 s
LOGO_T = 14 * BAR                  # 26.25 s, the slam
FONT = F.FONT


def bar(n, beat=0.):
    """Time of bar n (1-based) plus beats."""
    return (n - 1) * BAR + beat * BEAT


def sm(t, a, b):
    return smooth((t - a) / (b - a))


def gauss(t, c, w):
    return math.exp(-((t - c) / w) ** 2)


# ------------------------------------------------------------------ the beat grid
INTRO_KICKS = [bar(b, k) for b in range(1, 7) for k in (0, 2)]                     # half-time
BUILD_KICKS = [bar(7, k) for k in range(4)] + [bar(8, k) for k in range(3)]
DROP_KICKS = [DROP + k * BEAT for k in range(int((RAMP0 - DROP) / BEAT))]
KICKS = INTRO_KICKS + BUILD_KICKS + DROP_KICKS


def last_kick(t):
    k = [x for x in KICKS if x <= t]
    return k[-1] if k else -9.


def beat_pulse(t):
    return math.exp(-(t - last_kick(t)) * 9.) * (1. if t >= BUILD else .45)


# ------------------------------------------------------------------ story time (slow-motion ramp)
_W = np.linspace(0, DURATION + 1, 31001); _DW = _W[1] - _W[0]
_RATE = np.array([1 - .80 * sm(w, RAMP0, RAMP0 + .25) * (1 - sm(w, RAMP0 + 1.25, RAMP1)) for w in _W])
_TAU = np.concatenate([[0.], np.cumsum(_RATE[:-1]) * _DW])


def tau(t):
    return float(np.interp(t, _W, _TAU))


TAU_RAMP0 = tau(RAMP0); TAU_LOGO = tau(LOGO_T)


def speed(s):                       # s is story time; m/s along the highway
    return 38. * sm(s, DROP + .05, DROP + 1.1) * (1 - sm(s, TAU_RAMP0 + .4, TAU_LOGO - .05))


_S = np.linspace(0, DURATION + 1, 31001); _DS = _S[1] - _S[0]
_TRAVEL = np.cumsum([speed(x) for x in _S]) * _DS


def travel(s):
    return float(np.interp(s, _S, _TRAVEL))


def boost(s):
    pilot = .06 + .03 * math.sin(s * 23) + .05 * beat_pulse(s) * (s < DROP)
    pre = .25 * sum(gauss(s, bar(8, k), .05) for k in range(3))
    full = sm(s, DROP - .03, DROP + .35) * (1 - sm(s, TAU_RAMP0 + .6, TAU_LOGO + .3))
    return max(pilot * (s > 1.0) * sm(s, 6.56, 7.2) + pre, full)


_FLOW = np.cumsum([.74 + .9 * boost(x) for x in _S]) * _DS


def flow_phase(s):
    return float(np.interp(s, _S, _FLOW))


def x_offset(v, s):
    """Positions within the pack (the overtakes)."""
    if v == VESPER:
        return 1.5 * sm(s, DROP + .2, DROP + 3.) + 5.0 * sm(s, bar(12), bar(12, 1.6))
    if v == CINDER:
        return 3.0 * sm(s, DROP + .2, DROP + 2.2) - .5 * sm(s, bar(12), bar(12, 2))
    return -1.5 * sm(s, DROP + .2, DROP + 2.5) + 1.0 * math.sin(s * .7) * sm(s, DROP, DROP + 3)


LAMP_ON = {GLACIER: bar(6), CINDER: bar(6, 1), VESPER: bar(6, 2)}


def car_state(v, s):
    st = dict(boost=boost(s), flash=0., deploy=.05 + .95 * sm(s, bar(4, 2), bar(4, 3.2)), dissolve=0., cool=0., drain=99., fill=99.,
              fronts=(-99., 99.), alive=1., desat=0.)
    st['mixW'] = {VESPER: (1., 1., 1.), GLACIER: (0., 1., 0.), CINDER: (0., 0., 1.)}[v]
    bp = beat_pulse(s)
    st['heart'] = .55 + .55 * bp + .3 * st['boost'] + .9 * gauss(s, DROP, .25)
    st['charge'] = .35 + .65 * sm(s, 0., bar(5))
    st['lamp'] = 0. if s < LAMP_ON[v] else (1. if s > LAMP_ON[v] + .1 else .4)
    st['flash'] = gauss(s, DROP, .06) + .4 * sum(gauss(s, bar(8, k), .04) for k in range(3))
    sp = speed(s); x = x_offset(v, s)
    vib = .004 * (sp / 38) * math.sin(s * 61 + v) + .003 * st['boost'] * math.sin(s * 15 + v)
    accel = (speed(s + .05) - speed(s - .05)) / .1
    weave = .25 * math.sin(s * 1.3 + v * 2.) * (sp / 38)
    st['pose'] = trans(x, -.035 * st['boost'] + vib, LANE[v] + weave) @ rot(.0016 * accel + .012 * st['boost'], 'z') @ rot(.02 * math.cos(s * 1.3 + v * 2.) * (sp / 38), 'y')
    st['spin'] = -(travel(s) + x) / .435
    return st


# ------------------------------------------------------------------ the light-painted blitzedo
T_WRITE0, T_WRITE1 = BEAT, 4 * BEAT - .07        # seconds after LOGO_T: write on beats 2-4
T_FILL0, T_FILL1 = 4 * BEAT, 5 * BEAT              # crystallise on the bar-16 downbeat
T_SWEEP0, T_SWEEP1 = 5.4 * BEAT, 7. * BEAT
T_HEART = 6.5 * BEAT
T_RED0, T_RED1 = 4.6 * BEAT, 5.6 * BEAT          # the glass bleeds into brand red


def logo_clock():
    return WALL[0] - LOGO_T


def logo_state(s):
    tn = logo_clock()
    I = .45 * sm(tn, 0., T_WRITE1) + 1.1 * sm(tn, T_FILL0, T_FILL1) if tn > 0 else 0.
    return dict(time=-1., I=I, settle=0., sweep=0.)    # time < 0 retires the old voxel logo


# ------------------------------------------------------------------ the shots
# (start, end, name, whip-in yaw in degrees, cut flash)
SHOTS = [
    (0., bar(3), 'rear_dolly', 0, 0), (bar(3), bar(5), 'rear_orbit', 0, 0),
    (bar(5), bar(6), 'nozzle_macro', 0, .3),
    (bar(6, 0), bar(6, 1), 'card_glacier', 0, .5), (bar(6, 1), bar(6, 2), 'card_cinder', 20, .5),
    (bar(6, 2), bar(6, 3), 'card_vesper', -20, .5), (bar(6, 3), bar(7), 'three_front', 0, .4),
    (bar(7, 0), bar(7, 1), 'heart_cu', 0, .6), (bar(7, 1), bar(7, 2), 'cinder_rear', 25, .5),
    (bar(7, 2), bar(7, 3), 'glacier_front', -25, .5), (bar(7, 3), bar(8, 0), 'vesper_face', 25, .5)]
_strobe = ['nozzle_cu', 'wheel_cu', 'heart_cu', 'three_rear', 'vesper_face', 'cinder_rear']
for k in range(6):
    SHOTS.append((bar(8, k * .5), bar(8, (k + 1) * .5), _strobe[k], 0, .9))
SHOTS += [(bar(8, 3), DROP, 'black', 0, 0),
          (DROP, bar(9, 2), 'launch', 0, 1.6), (bar(9, 2), bar(10), 'side_track', 40, .3),
          (bar(10, 0), bar(10, 1), 'wheel_crash', 0, .6), (bar(10, 1), bar(10, 2), 'top_spin', -45, .3),
          (bar(10, 2), bar(10, 3), 'front_chase', 45, .3), (bar(10, 3), bar(11), 'passby', 0, .3),
          (bar(11, 0), bar(11, 2), 'barrel', 0, .8), (bar(11, 2), bar(11, 3), 'nozzle_speed', -40, .3),
          (bar(11, 3), bar(12), 'heart_speed', 40, .3),
          (bar(12, 0), bar(12, 2), 'overtake', 0, .8), (bar(12, 2), bar(13), 'flyover', -35, .3)]
_montage = ['three_rear', 'wheel_cu', 'top_spin', 'nozzle_cu', 'front_chase', 'heart_cu', 'side_track', 'vesper_face']
for k in range(8):
    SHOTS.append((bar(13, k * .5), bar(13, (k + 1) * .5), _montage[k], 30 * (1 if k % 2 else -1), .5))
SHOTS += [(RAMP0, RAMP1, 'slowmo', 0, 1.0), (LOGO_T, bar(16), 'logo_write', 0, .8), (bar(16), DURATION, 'logo_reveal', 0, 1.3)]
GLITCH = [(bar(8), bar(8, 3)), (bar(13), RAMP0)]


def shot_index(t):
    for i, sh in enumerate(SHOTS):
        if t < sh[1]:
            return i
    return len(SHOTS) - 1


WALL = [0.]                         # wall-clock time of the frame being drawn (cameras and overlays)


def car_pos(v, s, p=(0, 0, 0)):
    return (car_state(v, s)['pose'] @ np.array([*p, 1.]))[:3]


def orbit(target, dist, az, el):
    return F.orbit(target, dist, az, el)


def camera_for(name, q, t, s, a0):
    """Eye, target, fov, roll for a shot at local progress q (wall time t, story time s)."""
    V = lambda p=(0, 0, 0): car_pos(VESPER, s, p)
    roll = 0.; fov = 32
    if name == 'rear_dolly':        # creeping up between Vesper's nozzles, almost on the floor
        tgt = V((-2.6, .55, 0)); eye = V((-11.5 + 4.5 * q, .32 + .12 * q, .35 - .2 * q)); fov = 28
    elif name == 'rear_orbit':      # slow arc behind the three-car grid; the petals open
        tgt = V((-1.8, .8, 0)); eye = orbit(tgt, 12.5 - 2.5 * q, 152 + 56 * q, 9 + 3 * q); fov = 30
    elif name in ('nozzle_macro', 'nozzle_cu', 'nozzle_speed'):
        tgt = V((-2.75, .48, .53)); eye = V((-3.75 - .25 * q, .66 + .05 * q, 1.45 - .35 * q)); fov = 26 if name == 'nozzle_macro' else 32
        if name == 'nozzle_speed':
            eye = V((-4.6 + .4 * q, .9, 1.9)); tgt = V((-4.0, .48, .3)); fov = 40
    elif name.startswith('card_'):  # each car's nose as its lamps fire on the beat
        v = {'card_glacier': GLACIER, 'card_cinder': CINDER, 'card_vesper': VESPER}[name]; sd = {GLACIER: 1, CINDER: -1, VESPER: 1}[v]
        tgt = car_pos(v, s, (1.2, .7, 0)); eye = car_pos(v, s, (6.6 - .9 * q, .55, sd * (2.7 if v != VESPER else 2.0))); fov = 30
    elif name == 'three_front':
        tgt = np.array([0., .8, 0.]); eye = np.array([11.5 - 1.5 * q, .8, .3]); fov = 34
    elif name == 'heart_cu':
        tgt = V((-.24, 1.18, 0)); eye = orbit(tgt, 2.9 - .6 * q, 60 + 25 * q, 24); fov = 26
    elif name == 'heart_speed':
        tgt = V((-.24, 1.18, 0)); eye = orbit(tgt, 3.4 - .4 * q, 110 - 30 * q, 30); fov = 30
    elif name == 'cinder_rear':
        tgt = car_pos(CINDER, s, (-2.4, .6, 0)); eye = car_pos(CINDER, s, (-6.5 + 1. * q, .9, -2.2)); fov = 30
    elif name == 'glacier_front':
        tgt = car_pos(GLACIER, s, (1.5, .7, 0)); eye = car_pos(GLACIER, s, (6.8 - 1. * q, .45, 2.4)); fov = 30
    elif name == 'vesper_face':
        tgt = V((1.6, .75, 0)); eye = V((7.0 - 1.4 * q, .5, -1.6 + .5 * q)); fov = 30
    elif name == 'wheel_cu':
        tgt = V((1.38, .44, 1.0)); eye = V((2.8, .55, 3.0)); fov = 30
    elif name == 'three_rear':
        tgt = V((-1., .8, 0)); eye = V((-13. + 2. * q, 2.0, 0.)); fov = 34
    elif name == 'black':
        tgt = V((0, 0, 0)); eye = V((0, 50, 1)); fov = 1.
    elif name == 'launch':          # a camera fixed to the floor: the pack blasts away from it
        d0 = travel(tau(a0)); d = travel(s) - d0
        eye = np.array([-9. - d, .45, .9]); tgt = np.array([-2.5 - d * .5, .7, 0.]); fov = 32 + 8 * q
    elif name == 'side_track':
        tgt = V((-.5, .7, 0)); eye = V((-1.5 - 1.5 * q, .9, 9.0 - 1.5 * q)); fov = 34
    elif name == 'wheel_crash':     # crash zoom onto the front wheel
        tgt = V((1.38, .44, 1.0)); eye = V((4.2, .6, 4.8)); fov = 52 - 34 * smooth(q * 1.4)
    elif name == 'top_spin':
        tgt = V((-1.5, 0, 0)); eye = V((-1.5, 15. - 2. * q, .01)); fov = 46; roll = math.radians(-70 + 90 * q)
    elif name == 'front_chase':
        tgt = V((1.5, .7, 0)); eye = V((9.5 - 1.6 * q, .5, 1.2 - .6 * q)); fov = 36
    elif name == 'passby':          # a floor camera between the lanes; the pack tears past
        d0 = travel(tau(a0)); d = travel(s) - d0
        eye = np.array([14. - d, .35, 1.7]); tgt = eye + np.array([-1., .02, -.35]); fov = 44
    elif name == 'barrel':          # a full orbit around Vesper with a camera roll
        tgt = V((-.3, .7, 0)); eye = orbit(tgt, 6.4, 200 + 200 * q, 14 + 12 * math.sin(q * math.pi)); fov = 34; roll = math.radians(25 * math.sin(q * 2 * math.pi))
    elif name == 'overtake':
        tgt = car_pos(CINDER, s, (0, .7, 0)) * .5 + V((0, .7, 0)) * .5; eye = car_pos(CINDER, s, (1.0, 1.0, -8.5)); fov = 38
    elif name == 'flyover':         # drone from behind and above, diving over the pack to the front
        tgt = V((1.5 + 3. * q, .6, 0)); eye = V((-10. + 14. * q, 6. - 3.5 * q, 2.)); fov = 40
    elif name == 'slowmo':          # slow arc from the rear quarter to the side, in slow motion
        tgt = V((-1.2, .75, 0)); eye = orbit(tgt, 7.5 - 1.2 * q, 150 - 50 * q, 8 + 4 * q); fov = 30
    elif name == 'logo_write':      # behind the pack: comets loop out of the nozzles and write ahead
        tgt = np.array([F.LOGO_X - 4. + 4. * smooth(q), 2.4 + .5 * q, -1. + 1. * smooth(q)]); eye = np.array([V()[0] - 6.0 + 7.5 * smooth(q), 1.4 + 1.3 * q, 4.4 - 2.0 * q]); fov = 50 - 12 * smooth(q)
    else:                           # logo_reveal: frontal hero with a slow parallax drift through the glass
        tgt = np.array([F.LOGO_X, 2.9, 0.]); eye = np.array([6.8 + 1.4 * q, 2.6 + .25 * q, 2.2 - 2.4 * q]); fov = 36 - 2. * q
    return np.asarray(eye, float), np.asarray(tgt, float), fov, roll


def camera(s, shot):
    t = WALL[0]; a0, a1, name, whip, _ = SHOTS[shot]
    q = min(1., max(0., (t - a0) / (a1 - a0)))
    eye, tgt, fov, roll = camera_for(name, q, t, s, a0)
    # Whip-in: the view swings in from the side over the first 0.12 s (sub-frames smear it).
    if whip:
        w = math.radians(whip) * (1 - smooth((t - a0) / .12)) ** 2
        d = tgt - eye; c, sn = math.cos(w), math.sin(w)
        tgt = eye + np.array([c * d[0] - sn * d[2], d[1], sn * d[0] + c * d[2]])
    # Beat punch: a small zoom on every kick in the fast part.
    fov *= 1 - .06 * beat_pulse(t) * (t >= DROP and t < RAMP0)
    amp = .05 * gauss(t, DROP, .18) + .012 * speed(s) / 38 + .02 * beat_pulse(t) * (t >= BUILD) + .06 * math.exp(-max(0., t - LOGO_T) / .3) * (t > LOGO_T - .02)
    n = lambda k: math.sin(t * 23.1 + k) * .6 + math.sin(t * 37.7 + 2 * k) * .4
    eye = eye + amp * np.array([n(0), n(1), n(2)]); roll += amp * .6 * n(3)
    return eye, tgt, fov, roll, amp


def post(t):
    """Per-frame finishing driven by the edit: (cut flash, glitch, zoom blur, pump, tint)."""
    i = shot_index(t); a0, a1, name, whip, fl = SHOTS[i]
    flash = fl * math.exp(-(t - a0) * 45.)        # a crisp two-frame flash
    glitch = 0.
    for g0, g1 in GLITCH:
        if g0 <= t < g1:
            glitch = .35 + .65 * math.exp(-((t - a0) % BEAT) * 10)
    zb = 0.
    if name in ('wheel_crash', 'launch'):
        zb = .9 * math.exp(-(t - a0) * 5.)
    zb += .6 * gauss(t, DROP, .1) + .35 * math.exp(-max(0., t - bar(16)) * 7) * (t >= bar(16))
    pump = .8 * beat_pulse(t) * (t >= BUILD)
    hue = [(1., .55, .9), (.6, .95, 1.), (1., .75, .55)][i % 3]
    if name == 'black':
        flash = 0.
    return flash, glitch, zb, pump, hue


# ------------------------------------------------------------------ hooking the story renderer
F.car_state = car_state
F.flow_phase = flow_phase
F.logo_state = logo_state
F.camera = camera
F.beams = lambda t, poses: []
F.streams = lambda t: []
F.ring_n = lambda t: 0.
F.flood = lambda t: (0., 0., 0. if t < DROP else 60. * sm(t, DROP, DROP + 1.4))
F.shock_rings = lambda t: [(-2.95, 0., t - DROP)] if 0 <= t - DROP < 1.6 else []
F.SHOTS = SHOTS
F.shot_index = shot_index
_orig_uniforms = F.Renderer.uniforms


def uniforms(self, p, t, eye, st, reflection=0.):
    _orig_uniforms(self, p, t, eye, st, reflection)
    w = WALL[0]; fl, gl, zb, pump, hue = post(w)
    for k, v in (('travel', travel(t)), ('speed', speed(t)), ('beatPulse', beat_pulse(w)), ('ringOn', 0.),
                 ('brandRed', sm(w - LOGO_T, T_RED0, T_RED1)), ('cutFlash', fl * .22), ('glitch', gl), ('zoomBlur', zb), ('pump', pump), ('flashTint', hue)):
        self.g.u(p, k, v)


F.Renderer.uniforms = uniforms


def frame_at(r, t, subframes=3, shutter=.5):
    i = shot_index(t); a, b = SHOTS[i][0], SHOTS[i][1]; acc = None
    if SHOTS[i][2] == 'black':
        return overlay(Image.new('RGB', (r.w, r.h), (3, 2, 8)), t)
    for k in range(subframes):
        off = ((k + .5) / subframes - .5) * shutter / FPS if subframes > 1 else 0.
        w = min(max(t + off, a), b - 1e-4); WALL[0] = w
        im = r.render(tau(w), i, seed=t * 7.1 + k)
        acc = im if acc is None else acc + im
    WALL[0] = t
    return overlay(Image.fromarray(np.clip(acc / subframes, 0, 255).astype(np.uint8)), t)


def subframes_for(t, base):
    i = shot_index(t); a0, a1, name, whip, _ = SHOTS[i]
    fast = DROP <= t < RAMP0 or (BUILD <= t < DROP)
    return base + (4 if whip and t - a0 < .14 else 0) + (2 if fast else 0)


# ------------------------------------------------------------------ motion-graphics overlays
CARDS = [(GLACIER, 'GLACIER / 08', (40, 236, 255)), (CINDER, 'CINDER / 07', (255, 120, 30)), (VESPER, 'VESPER / 09', (255, 60, 200))]


def overlay(im, t):
    w, h = im.size; lay = Image.new('RGBA', im.size); d = ImageDraw.Draw(lay)
    # Name cards: each car's card snaps in on the beat its lamps fire.
    if bar(6) <= t < bar(6, 3):
        k = min(2, int((t - bar(6)) / BEAT)); v, name, col = CARDS[k]
        q = smooth(min(1., (t - bar(6, k)) / .14))
        f = ImageFont.truetype(FONT, round(h * .085)); fs = ImageFont.truetype(FONT, round(h * .028))
        x = round(w * .06 - (1 - q) * w * .25); y = round(h * .70)
        d.rectangle((x, y - h * .012, x + w * .006, y + h * .11), fill=(*col, 255))
        d.text((x + w * .018, y - h * .02), name, font=f, fill=(255, 245, 255, int(255 * q)))
        d.text((x + w * .02, y + h * .075), 'AFTERLIGHT SERIES  ·  BLITZEDO', font=fs, fill=(*col, int(220 * q)))
    # Countdown on the strobe bar: 3, 2, 1 on the beats, then a black beat.
    if bar(8) <= t < bar(8, 3):
        k = int((t - bar(8)) / BEAT); q = (t - bar(8, k)) / BEAT
        txt = '321'[k]; f = ImageFont.truetype(FONT, round(h * .62 * (1.2 - .2 * smooth(q * 3))))
        bb = f.getbbox(txt); x = (w - (bb[2] - bb[0])) / 2 - bb[0]; y = (h - (bb[3] - bb[1])) / 2 - bb[1]
        a = int(255 * (1 - smooth((q - .55) / .45)))
        for dx, col in ((-12, (0, 230, 255)), (12, (255, 92, 10))):
            d.text((x + dx, y), txt, font=f, fill=(*col, a // 2))
        glow = lay.filter(ImageFilter.GaussianBlur(h * .02)); d = ImageDraw.Draw(lay)
        d.text((x, y), txt, font=f, fill=(255, 245, 255, a))
        lay = Image.alpha_composite(glow, lay); d = ImageDraw.Draw(lay)
    bar_h = round(h * .045); d.rectangle((0, 0, w, bar_h), fill='#04020a'); d.rectangle((0, h - bar_h, w, h), fill='#04020a')
    a_fade = 1 - min(1., t / .5) if t < .5 else smooth((t - 29.55) / .45) if t > 29.55 else 0.
    if a_fade > 0:
        d.rectangle((0, 0, w, h), fill=(4, 2, 10, int(255 * a_fade)))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')


STILLS = [(2.5, 'rear_dolly'), (6.6, 'rear_orbit'), (8.4, 'nozzle_macro'), (10.0, 'card_cinder'), (11.5, 'heart_cu'), (13.3, 'countdown'),
          (15.25, 'launch'), (16.3, 'side_track'), (17.15, 'wheel_crash'), (17.6, 'top_spin'), (18.1, 'front_chase'), (18.55, 'passby'),
          (19.4, 'barrel'), (20.1, 'nozzle_speed'), (21.2, 'overtake'), (22.0, 'flyover'), (23.1, 'montage'), (25.0, 'slowmo'),
          (26.6, 'comets'), (27.3, 'writing'), (27.9, 'written'), (28.3, 'crystal'), (28.9, 'sweep'), (29.45, 'heartbeat')]


def make_renderer(w, h):
    import logo_vec as LV
    r = F.Renderer(w, h); r.world.burst.count = 0     # no capture in this cut
    g = r.g; P = lambda vs, fs: g.program(F.shader(vs), F.shader(fs))
    r.glassp = P('object.vert', 'glasslogo.frag'); r.strokep = P('stroke.vert', 'stroke.frag'); r.lsparkp = P('lspark.vert', 'lspark.frag')
    letters, gl, info = LV.build(FONT.replace('BarlowCondensed-Bold.ttf', 'BarlowCondensed-Bold.ttf'), F.LOGO_X)
    s_end = tau(LOGO_T) + 5.
    nozzles = {0: car_pos(VESPER, s_end, (-2.75, .48, 0)), 1: car_pos(GLACIER, s_end, (-2.75, .48, 0)), 2: car_pos(CINDER, s_end, (-2.75, .48, 0))}
    paths = LV.comet_paths(gl, F.LOGO_X, nozzles, 0., T_WRITE0, T_WRITE1)
    r.letters = letters; r.strokes = LV.stroke_mesh(paths); r.lsparks = LV.spark_mesh(paths); r.logo_info = info
    for m in (r.letters, r.strokes, r.lsparks):
        m.upload(g)
    print('Light-painted logo:', r.letters.count // 3, 'glass triangles;', r.strokes.count // 3, 'stroke triangles', flush=True)
    return r


_orig_scene = F.Renderer.scene


def scene(self, t, states, objs, vp, eye, view, reflection):
    _orig_scene(self, t, states, objs, vp, eye, view, reflection)
    tn = logo_clock()
    if tn < 0 or not hasattr(self, 'letters'):
        return
    g = self.g; ref = float(reflection); mirror = F.scale(1, -1, 1) if reflection else np.eye(4, dtype=np.float32); vs = states[VESPER]
    beatP = math.exp(-(tn % BEAT) * 9.)
    common = (('tnow', tn), ('beatP', beatP), ('solid', sm(tn, T_FILL0 - .05, T_FILL1)))
    if tn > T_FILL0 - .02:
        p = self.glassp; self.uniforms(p, t, eye, vs, ref); g.u(p, 'vp', vp); g.u(p, 'lightvp', self.lv)
        for k, v in common + (('glassFill', sm(tn, T_FILL0, T_FILL1)), ('sweepPos', -2. + 18. * sm(tn, T_SWEEP0, T_SWEEP1)), ('heartWave', 1. if tn > T_HEART else 0.)):
            g.u(p, k, v)
        bw = [(u, vv - self.logo_info['base_y'], 0, 1.) for _, u, vv in self.logo_info['bowls']][:4]
        self.arr(p, 'bowls', bw + [(0, 0, 0, 0)] * (4 - len(bw)), 4)
        self.letters.draw(p, mirror)
    g.glEnable(0x0BE2); g.glBlendFunc(0x0302, 1); g.glDepthMask(0)
    for p, m in ((self.strokep, self.strokes), (self.lsparkp, self.lsparks)):
        self.uniforms(p, t, eye, vs, ref); g.u(p, 'vp', vp); g.u(p, 'cameraRight', view[0, :3]); g.u(p, 'cameraUp', view[1, :3])
        for k, v in common:
            g.u(p, k, v)
        m.draw(p, np.eye(4, dtype=np.float32))
    g.glDepthMask(1); g.glDisable(0x0BE2)


F.Renderer.scene = scene


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stills', action='store_true'); p.add_argument('--width', type=int, default=1920); p.add_argument('--height', type=int, default=1080)
    p.add_argument('--start', type=float, default=0.); p.add_argument('--seconds', type=float, default=DURATION)
    p.add_argument('--subframes', type=int, default=3); p.add_argument('--output', default=str(ROOT / 'BLITZ_picture.mp4'))
    p.add_argument('--outdir', default=str(ROOT / 'renders')); p.add_argument('--only', default='')
    a = p.parse_args(); r = make_renderer(a.width, a.height)
    if a.stills:
        out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
        for t, name in STILLS:
            if a.only and name not in a.only.split(','):
                continue
            frame_at(r, t, a.subframes).save(out / f'{name}.png'); print('STILL', name, flush=True)
        return
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{a.width}x{a.height}', '-r', str(FPS), '-i', '-', '-an',
           '-vf', 'scale=1920:1080:flags=lanczos:out_color_matrix=bt709', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', a.output]
    out = subprocess.Popen(cmd, stdin=subprocess.PIPE); begin = time.time()
    f0 = round(a.start * FPS); n = round(a.seconds * FPS)
    for i in range(f0, f0 + n):
        t = i / FPS
        out.stdin.write(frame_at(r, t, subframes_for(t, a.subframes)).tobytes())
        if i % 30 == 0:
            print('FRAME', i, 'elapsed', round(time.time() - begin, 1), flush=True)
    out.stdin.close(); assert out.wait() == 0; print('PICTURE COMPLETE', a.output, flush=True)


if __name__ == '__main__':
    main()
