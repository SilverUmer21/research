"""Trailer-hybrid score and sound design for THE HIJACK, locked to film.py's timeline.

Everything is synthesised here (NumPy + SciPy): braams, sub drops, impacts, risers,
reverse swells, energy siphons, a pulsing ostinato, hybrid drums with a sidechained bass,
glassy capture shatter, lava rumble and a Yaman-scale letter cascade for the blitzedo reveal.
A synthetic stereo hall (convolution) sits on a send bus. master.py sets the final loudness.
"""
from pathlib import Path
import math, wave
import numpy as np
from scipy import signal
import film as F

ROOT = Path(__file__).resolve().parent
SR = 48000; N = int(F.DURATION * SR)
rng = np.random.default_rng(1209)
dry = np.zeros((N, 2)); send = np.zeros((N, 2)); duck = np.ones(N)
bass_bus = np.zeros((N, 2))
NOTE = lambda n: 440. * 2 ** ((n - 69) / 12)        # MIDI note -> Hz
Fn = 29                                               # F1


def secs(d):
    return np.arange(int(d * SR)) / SR


def place(buf, t, s, g=1., pan=0.):
    i = int(t * SR)
    if i >= N:
        return
    if i < 0:
        s = s[-i:]; i = 0
    n = min(len(s), N - i)
    if n <= 0:
        return
    s = np.asarray(s[:n]) * g
    if s.ndim == 1:
        p = np.clip(pan, -1, 1); s = np.stack([s * math.sqrt((1 - p) / 2), s * math.sqrt((1 + p) / 2)], 1)
    buf[i:i + n] += s


def add(t, s, g=1., pan=0., rev=.2):
    place(dry, t, s, g, pan); place(send, t, s, g * rev, pan)


def env(d, a=.005, r=None, curve=4.):
    q = secs(d); e = np.minimum(q / max(a, 1e-4), 1)
    return e * (np.exp(-q * curve / d) if r is None else np.minimum((d - q) / r, 1).clip(0))


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR * .45), 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR * .45)], 'band', fs=SR, output='sos'), x)


def sweep_lp(x, fc_curve, block=256):
    """Time-varying low-pass, block by block with carried state."""
    fc_curve = np.broadcast_to(np.asarray(fc_curve, float), x.shape); out = np.zeros_like(x); zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(fc_curve[min(i, len(fc_curve) - 1)], 30, SR * .45))
        sos = signal.butter(2, fc, 'low', fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return out


def sweep_bp(x, fc_curve, q=1.2, block=256):
    fc_curve = np.broadcast_to(np.asarray(fc_curve, float), x.shape); out = np.zeros_like(x); zi = None
    for i in range(0, len(x), block):
        fc = float(np.clip(fc_curve[min(i, len(fc_curve) - 1)], 60, SR * .4))
        sos = signal.butter(1, [fc / (1 + 1 / q), min(fc * (1 + 1 / q), SR * .45)], 'band', fs=SR, output='sos')
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + block], zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
    return out


def saw(freq, d, detune=0., harm=60):
    """Band-limited additive saw; freq may be a curve."""
    q = secs(d); f = np.broadcast_to(np.asarray(freq, float), q.shape) * (1 + detune)
    ph = 2 * np.pi * np.cumsum(f) / SR; out = np.zeros_like(q); fmax = float(np.max(f))
    for k in range(1, harm + 1):
        if k * fmax > 16000:
            break
        out += np.sin(k * ph) / k
    return out * .6


def sine(freq, d):
    q = secs(d); f = np.broadcast_to(np.asarray(freq, float), q.shape); return np.sin(2 * np.pi * np.cumsum(f) / SR)


def noise(d):
    return rng.normal(size=int(d * SR))


# ----------------------------------------------------------------- instruments
def braam(t, root, g=1., d=3.2, bright=1800., pan=0., chord=(0, 7, 12, 15)):
    s = np.zeros(int(d * SR))
    for k, iv in enumerate(chord):
        for det in (-.004, .0, .0045):
            s += saw(NOTE(root + iv), d, det, harm=40) * (1. if iv < 12 else .6)
    q = secs(d); fc = 160 + bright * np.exp(-q * 1.6) * np.minimum(q / .06, 1) + 220
    s = sweep_lp(s, fc); s = np.tanh(s * 1.8) * env(d, .02, curve=3.2)
    add(t, s, .22 * g, pan, rev=.55)


def sub_drop(t, f0=70., f1=26., d=1.8, g=1.):
    q = secs(d); f = f1 + (f0 - f1) * np.exp(-q * 3.)
    add(t, np.tanh(1.6 * sine(f, d)) * env(d, .004, curve=2.6), .7 * g, rev=.05)


def impact(t, g=1., pan=0., bright=1.):
    n = noise(.5)
    crack = hp(n, 1800) * env(.5, .001, curve=18)
    body = lp(n, 900) * env(.5, .002, curve=10)
    q = secs(1.2); ring = sum(np.sin(2 * np.pi * 180 * r * q) * np.exp(-q * (3 + 2 * r)) for r in (1, 2.76, 5.4, 8.93))
    add(t, crack, .5 * g * bright, pan, rev=.5); add(t, body, .6 * g, pan, rev=.4); add(t, ring, .05 * g * bright, pan, rev=.6)
    sub_drop(t, 80, 30, 1.4, .7 * g)


def reverse_swell(t_hit, d=1.6, g=1., hue=0):
    n = noise(d) * np.linspace(0, 1, int(d * SR)) ** 3
    f = np.linspace(400, 5000 + 2000 * hue, int(d * SR))
    s = sweep_bp(n, f, 1.5) + .4 * saw(np.linspace(NOTE(Fn + 12), NOTE(Fn + 24), int(d * SR)), d, 0, 20) * np.linspace(0, 1, int(d * SR)) ** 2
    add(t_hit - d, s, .35 * g, 0, rev=.6)


def riser(t0, t1, g=1.):
    d = t1 - t0; L = int(d * SR); x = np.linspace(0, 1, L)
    n = sweep_bp(noise(d), 200 + 7000 * x ** 2, 2.)
    tone = sum(saw(NOTE(Fn + 24 + iv) * 2 ** (x * 1.0), d, det, 12) for iv in (0, 7) for det in (-.003, .003))
    tone = sweep_lp(tone, 300 + 6000 * x ** 2)
    add(t0, (n * .9 + tone * .5) * x ** 2.2, .30 * g, 0, rev=.5)


def heartbeat(t, g=1.):
    for dt, gg, f in ((0., 1., 55.), (.17, .55, 48.)):
        q = secs(.5); fr = f * (1 + 1.5 * np.exp(-q * 30))
        add(t + dt, np.tanh(2.5 * sine(fr, .5)) * np.exp(-q * 9) * (1 - np.exp(-q * 500)), .45 * g * gg, rev=.15)


def tick(t, hz, g=.08, pan=0.):
    q = secs(.25); s = (np.sin(2 * np.pi * hz * q) + .5 * np.sin(2 * np.pi * hz * 2.41 * q)) * np.exp(-q * 30)
    s += hp(noise(.25), 3000) * np.exp(-q * 120) * .6
    add(t, s, g, pan, rev=.45)


def hum(t0, d, f, die_at, die_d, pan, g=.05):
    q = secs(d); dying = np.clip((q - (die_at - t0)) / die_d, 0, 1)
    fr = f * (1 - .45 * dying ** 1.5) * (1 + .004 * np.sin(2 * np.pi * 5.3 * q))
    s = saw(fr, d, 0, 18) + .7 * sine(fr * .5, d)
    s = lp(s, 900) * (1 - dying) ** 1.3 * (.8 + .2 * np.sin(2 * np.pi * 7 * q)) * np.minimum(q / .8, 1)
    add(t0, s, g, pan, rev=.25)


def siphon(t0, t1, hue_hz, pan0, pan1, g=1.):
    """Energy being pulled along the arc: rising tonal whoosh, crackle, and a pitch climb."""
    d = t1 - t0; L = int(d * SR); x = np.linspace(0, 1, L)
    n = sweep_bp(noise(d), 300 + 4500 * x, 3.) * np.sin(np.pi * x) ** .8
    cr = (rng.random(L) < .002 + .01 * x) * rng.normal(size=L); cr = bp(np.convolve(cr, np.exp(-np.arange(120) / 12.), 'same'), 1500, 9000)
    tone = sum(sine(hue_hz * r * (1 + .9 * x), d) for r in (1, 1.5, 2.01)) * x ** 1.4 * .3
    s = n * .45 + cr * .6 + tone * 1.6
    for k in range(8):                                   # pan glides along the arc
        a, b = int(L * k / 8), int(L * (k + 1) / 8)
        place(dry, t0 + a / SR, s[a:b] * np.hanning(b - a) * 2, .14 * g, pan0 + (pan1 - pan0) * (k + .5) / 8)
    place(send, t0, s, .12 * g, (pan0 + pan1) / 2)


def zap(t, d=.7, pan0=-.5, pan1=.5, g=1.):
    x = np.linspace(0, 1, int(d * SR)); car = sine(300 + 2400 * x ** 1.5, d); mod = sine(57 + 300 * x, d)
    s = np.sin(2 * np.pi * np.cumsum(300 + 2400 * x ** 1.5) / SR + 3 * mod) * np.sin(np.pi * x) ** .5
    s += hp(noise(d), 4000) * .3 * np.sin(np.pi * x)
    for k in range(4):
        a, b = int(len(x) * k / 4), int(len(x) * (k + 1) / 4)
        place(dry, t + a / SR, s[a:b] * np.hanning(b - a) * 2, .12 * g, pan0 + (pan1 - pan0) * (k + .5) / 4)
    place(send, t, s, .1 * g)


def kick(t, g=1.):
    q = secs(.45); f = 45 + 110 * np.exp(-q * 35)
    s = np.tanh(2 * sine(f, .45)) * np.exp(-q * 7) + hp(noise(.45), 3000) * np.exp(-q * 300) * .4
    add(t, s, .7 * g, rev=.08)
    i = int(t * SR); n = min(int(.28 * SR), N - i)
    if n > 0:
        duck[i:i + n] = np.minimum(duck[i:i + n], 1 - .75 * np.exp(-np.arange(n) / SR * 14))


def clap(t, g=1.):
    s = np.zeros(int(.5 * SR))
    for k, dt in enumerate((0, .011, .022)):
        i = int(dt * SR); q = secs(.5 - dt); s[i:] += bp(noise(.5 - dt), 900, 5000) * np.exp(-q * (60 if k < 2 else 14))
    q = secs(.5); s += np.sin(2 * np.pi * 185 * q) * np.exp(-q * 25) * .5
    add(t, s, .35 * g, rev=.45)


def hat(t, g=1., pan=.3):
    q = secs(.08); add(t, hp(noise(.08), 7000) * np.exp(-q * 70), .12 * g, pan, rev=.1)


def taiko(t, g=1., pan=0.):
    q = secs(1.); f = 58 + 30 * np.exp(-q * 18)
    s = np.tanh(1.8 * sine(f, 1.)) * np.exp(-q * 4.5) + lp(noise(1.), 500) * np.exp(-q * 30) * .5
    add(t, s, .5 * g, pan, rev=.45)


def shatter(t0, d, g=1.):
    for k in range(70):
        t = t0 + rng.random() ** 1.6 * d; hz = 1800 + rng.random() * 6500; q = secs(.35)
        add(t, np.sin(2 * np.pi * hz * q) * np.exp(-q * (18 + rng.random() * 30)), .03 * g, rng.uniform(-.8, .8), rev=.6)
    for k in range(10):
        t = t0 + rng.random() * d * .7; add(t, hp(noise(.12), 2500) * np.exp(-secs(.12) * 40), .14 * g, rng.uniform(-.6, .6), rev=.5)


def pluck_bell(t, hz, g=.1, pan=0.):
    q = secs(2.4)
    bell = sum(np.sin(2 * np.pi * hz * r * q) * np.exp(-q * (1.2 + 1.5 * r)) / r for r in (1, 2.0, 3.01, 4.2, 5.43))
    n = int(2.4 * SR); p = max(2, round(SR / hz)); buf = rng.uniform(-1, 1, p); ks = np.empty(n)
    for i in range(n):
        ks[i] = buf[i % p]; buf[i % p] = .996 * .5 * (buf[i % p] + buf[(i + 1) % p])
    add(t, bell * .6 + ks * .5, g, pan, rev=.55)


# ----------------------------------------------------------------- the cue sheet
# 0-4 s COLD: dark drone, rival idles, failing heart, ring notch ticks, reverse swell into SWITCH.
d0 = 4.4; q = secs(d0)
drone = sum(saw(NOTE(n), d0, det, 30) for n in (Fn + 1, Fn + 13, Fn + 20) for det in (-.003, .003))
drone = sweep_lp(drone, 120 + 260 * (q / d0) ** 2) * np.minimum(q / 1.2, 1) * np.minimum((d0 - q) / .15, 1)
add(0., drone, .055, rev=.4)
hi = sum(sine(NOTE(Fn + 48 + iv) * (1 + .003 * np.sin(2 * np.pi * .3 * q + iv)), d0) for iv in (0, 1, 7)) * (q / d0) ** 2 * .3
add(0., hi, .012, rev=.8)
hum(0., 14.5, 110., 7.0, 2.9, .45, .03)     # Glacier, right of frame early on
hum(0., 14.5, 82.4, 10.8, 2.9, -.45, .03)   # Cinder
for b, gg in zip(F.FAIL_BEATS, (.8, .55, .35)):
    heartbeat(b, gg)
for k in range(4):
    tick(.6 + 3.35 * (k + 1) / 4 - .01, 1400 + 180 * k, .09, -.3 + .2 * k)
reverse_swell(F.SWITCH, 1.4, 1.1)
# 4.0 SWITCH
braam(F.SWITCH, Fn, 1.2); impact(F.SWITCH, 1.1); heartbeat(F.SWITCH, 1.5)
zap(F.SWITCH + .15, .7, -.4, .5)
# 6.6-14.2 THE STEAL: siphons, arrivals, ostinato building underneath
siphon(6.6, 10.0, 523., .55, -.45, 1.)
zap(10.0, .6, -.2, -.6, .8)
siphon(10.8, 13.8, 392., -.55, .45, 1.)
braam(10.0, Fn + 3, .7, 2.4, 1200., .2); impact(10.0, .5, .2, .6); heartbeat(10.0, .8)
reverse_swell(13.8, 1.2, .9); braam(13.8, Fn + 5, .9, 2.6, 1600., -.2); impact(13.8, .7, -.2, .8); heartbeat(13.8, .9)
bpm = 128.; e8 = 60 / bpm / 2; t = 6.6; k = 0
ost = [Fn + 12, Fn + 12, Fn + 15, Fn + 12, Fn + 19, Fn + 12, Fn + 17, Fn + 15]
while t < 17.4:
    build = min(1., (t - 6.6) / 9.8); dn = e8 * .9; q = secs(dn)
    s = sweep_lp(saw(NOTE(ost[k % 8]), dn, 0, 30) + saw(NOTE(ost[k % 8]), dn, .006, 30), 300 + 2600 * build ** 2)
    add(t, s * np.exp(-q * 6), .055 + .05 * build, .15 * (1 if k % 2 else -1), rev=.25)
    if t > 12.0 and k % 2 == 0:
        hat(t, .3 + .4 * build, .3 if k % 4 else -.3)
    if t > 11.4 and k % 4 == 0:
        taiko(t, .4 + .5 * build, -.2)
    t += e8; k += 1
# 13.9 lamps, 14.6 petals, pops, riser, 16.45 IGNITION
for tt in (13.90, 14.05):
    add(tt, lp(noise(.1), 2000) * np.exp(-secs(.1) * 50), .2, rev=.3)
for k in range(6):
    tick(14.6 + k * .14, 900 + 70 * (k % 2), .07, -.3 if k % 2 else .3)
for p, gg in zip(F.POPS, (.6, .8, 1.)):
    impact(p, .45 * gg, 0, .5); taiko(p, .6 * gg)
riser(15.0, F.IGNITION, 1.2)
braam(F.IGNITION, Fn, 1.4, 3.0, 2400.); impact(F.IGNITION, 1.3); sub_drop(F.IGNITION, 90, 24, 2.4, 1.)
# Vesper's roar follows the boost curve; muffled during the slow-motion jump.
t0 = 15.2; d = 8.; q = secs(d)
boost = np.interp(q, q[::480], [F.v_boost(t0 + x) for x in q[::480]])
n = noise(d); roar = lp(n, 220) * 2.2 + bp(n, 300, 2400) * .45
roar += np.tanh(2 * saw(42 + 18 * boost, d, 0, 25)) * .5
slow = np.array([1. if not (F.JUMP0 + .1 < t0 + x < F.JUMP1 - .15) else .25 for x in q[::480]])
slow = np.interp(q, q[::480], slow); fc = 400 + 3600 * slow
roar = sweep_lp(roar, fc) * boost * (.3 + .7 * slow)
add(t0, roar, .22, -.1, rev=.15); add(t0 + .013, roar, .2, .1, rev=.0)
# 16.45-17.5 the drums wake; 17.5 takeoff whoosh; slow motion = the world goes underwater.
for k in range(8):
    tt = F.IGNITION + .1 + k * e8 * 2
    if tt < F.JUMP0:
        kick(tt, .8); taiko(tt + e8, .5, .3)
q = secs(.9); add(F.JUMP0 - .1, sweep_bp(noise(.9), 300 + 5000 * np.linspace(0, 1, len(q)), 2) * np.sin(np.pi * q / .9), .35, rev=.4)
d = F.JUMP1 - F.JUMP0; q = secs(d)
pad = sum(sine(NOTE(Fn + 36 + iv) * (1 + .002 * np.sin(2 * np.pi * (.2 + .1 * j) * q)), d) for j, iv in enumerate((0, 7, 12, 16, 19)))
add(F.JUMP0, pad * np.sin(np.pi * q / d) ** 1.5, .035, rev=.9)
heartbeat(18.3, .9); heartbeat(19.5, 1.)
shatter(18.75, 1.6, 1.)
reverse_swell(F.LAND, 1.0, 1.2)
# 21.0 LANDING: the drop.
braam(F.LAND, Fn, 1.6, 3.4, 2600.); impact(F.LAND, 1.5); sub_drop(F.LAND, 100, 22, 2.8, 1.2)
t = F.LAND; k = 0; beat = 60 / bpm
bassline = [Fn + 12, Fn + 12, Fn + 15, Fn + 12, Fn + 19, Fn + 17, Fn + 15, Fn + 12]
while t < 24.3:
    if k % 2 == 0:
        kick(t, 1.)
    else:
        clap(t, .9)
    for h in range(2):
        hat(t + h * beat / 2, .5 + .3 * h, .35 if h else -.35)
    dn = beat * .95; q = secs(dn); bn = bassline[k % 8]
    b = np.tanh(2.2 * (saw(NOTE(bn), dn, 0, 25) + saw(NOTE(bn), dn, .007, 25) + 1.2 * sine(NOTE(bn - 12), dn)))
    place(bass_bus, t, lp(b, 700) * np.minimum(q / .01, 1) * np.minimum((dn - q) / .03, 1), .16)
    if k % 2 == 0:                                       # prism stabs
        for iv in (0, 7, 14):
            st = saw(NOTE(Fn + 36 + iv + (2 if k % 4 else 0)), .18, .004, 20) * np.exp(-secs(.18) * 14)
            add(t + beat / 2, st, .03, .4 if iv == 7 else -.3, rev=.4)
    t += beat; k += 1
for j in range(16):                                     # board flood arpeggio
    pluck_bell(21.2 + j * .14, NOTE(Fn + 36 + [0, 4, 7, 11, 12, 16, 19, 23][j % 8] + (12 if j >= 8 else 0)), .035, -.7 + 1.4 * j / 15)
L = int(3.4 * SR); tq = np.arange(L) / SR
ir = np.stack([rng.normal(size=L), rng.normal(size=L)], 1) * np.exp(-tq * 2.3)[:, None]
for c in range(2):
    ir[:, c] = lp(ir[:, c], 5000) * .6 + lp(ir[:, c], 1500) * .4
ir[:int(.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))


def render_bus():
    wet = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    return dry + wet * .55 + bass_bus * duck[:, None]


qq = np.arange(N) / SR
gate = np.clip(1 - (qq - 24.30) / .07, 0, 1) * .97 + .03 * np.exp(-np.clip(qq - 24.37, 0, None) * 3)
part1 = render_bus() * gate[:, None]
dry[:] = 0; send[:] = 0; bass_bus[:] = 0
# 24.35 silence ... lava races ahead ... 25.0 eruption, letter cascade, final chord, light sweep.
q = secs(1.2)
add(24.62, lp(noise(1.2), 90) * np.minimum(q / .4, 1) ** 2 * np.exp(-q * .5), .5, rev=.2)
for k, pan in enumerate((-.6, -.2, .2, .6)):
    qq = secs(.8); add(24.42 + k * .04, sweep_bp(noise(.8), np.linspace(400, 3000, len(qq)), 2) * np.sin(np.pi * qq / .8) ** 2, .12, pan, rev=.3)
reverse_swell(F.LOGO0, .8, 1.)
impact(F.LOGO0, 1.2); sub_drop(F.LOGO0, 80, 24, 3., 1.)
q = secs(4.5); rumble = lp(noise(4.5), 160) * np.exp(-q * .7) * 2.
lava = bp((rng.random(len(q)) < .004) * rng.normal(size=len(q)), 500, 4000) * np.exp(-q * .4)
add(F.LOGO0, rumble, .35, rev=.3); add(F.LOGO0, lava, .5, rev=.4)
yaman = [0, 2, 4, 6, 7, 9, 11, 12]                       # F Lydian = Raag Yaman on F
for i in range(8):
    tl = F.LOGO0 + (i + .5) / 8 * .9 + .12
    pluck_bell(tl, NOTE(Fn + 36 + yaman[i]), .07, -.7 + 1.4 * i / 7)
    add(tl, hp(noise(.15), 1500) * np.exp(-secs(.15) * 35), .12, -.7 + 1.4 * i / 7, rev=.4)
    taiko(tl, .25, -.7 + 1.4 * i / 7)
braam(26.0, Fn, 1.5, 4.0, 3000., 0, chord=(0, 7, 12, 16, 18, 23))
for iv in (0, 7, 16, 18, 23):
    qd = secs(4.); add(26.0, sine(NOTE(Fn + 36 + iv), 4.) * np.exp(-qd * .6) * np.minimum(qd / .3, 1), .03, rev=.8)
q = secs(1.2); x = np.linspace(0, 1, len(q))                 # the light sweep across the letters
shing = sweep_bp(noise(1.2), 2000 + 9000 * x, 4) * np.sin(np.pi * x) + sine(3000 + 4000 * x, 1.2) * np.sin(np.pi * x) * .15
for k in range(6):
    a, b = int(len(q) * k / 6), int(len(q) * (k + 1) / 6)
    place(dry, 27.45 + a / SR, shing[a:b] * np.hanning(b - a) * 2, .14, -.7 + 1.4 * (k + .5) / 6)
place(send, 27.45, shing, .1)
heartbeat(29.15, .7)

# ----------------------------------------------------------------- mix
mix = part1 + render_bus()
mix = hp(mix.T, 22).T
# Gentle glue: smooth peak follower with 3:1 above -6 dBFS, then soft clip.
peak = signal.lfilter([1 - .9995], [1, -.9995], np.abs(mix).max(1))
thr = .5; gain = np.where(peak > thr, (thr + (peak - thr) / 3) / np.maximum(peak, 1e-9), 1.)
mix *= gain[:, None]
mix = np.tanh(mix * 1.6) / 1.6
q = np.arange(N) / SR; mix *= (np.minimum(q / .05, 1) * np.clip((F.DURATION - q) / .6, 0, 1))[:, None]
mix /= max(1e-9, np.abs(mix).max()) / .89
with wave.open(str(ROOT / 'HIJACK_score.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes(np.int16(np.clip(mix, -1, 1) * 32767).tobytes())
print('SCORE COMPLETE', ROOT / 'HIJACK_score.wav')
