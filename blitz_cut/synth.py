"""Synth and sound-design library shared by the blitzedo films (taken from hijack_film/score.py).

Importing it creates empty buses: dry, send, duck and bass_bus, 30 s at 48 kHz.
"""
from pathlib import Path
import math, wave
import numpy as np
from scipy import signal


ROOT = Path(__file__).resolve().parent
SR = 48000; N = int(30.0 * SR)
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


