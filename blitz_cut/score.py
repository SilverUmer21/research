"""BLITZ CUT track: 128 BPM, F minor, built on the same beat grid as cut.py.

Bars 1-4  dark half-time intro: pad, heartbeat kick, sub, high arp, petal ticks
Bars 5-6  the groove arrives: backbeat, hats, sidechained bass, lamp clunks per beat
Bar 7     build: kick on every beat, eighth snares, riser, a hit on every cut
Bar 8     roll to 32nds, countdown hits on 3-2-1, then a dead-silent beat
Bars 9-13 THE DROP: four-on-the-floor, reese bass, offbeat chord stabs, roar, whooshes on cuts,
          a pass-by, then a stutter glitch on the montage
Bar 14    tape stop into slow motion: heartbeat and drone only
Bars 15-16 blitzedo: impact, braam, letters on 16ths, final chord and sweep
"""
from pathlib import Path
import math, wave
import numpy as np
from scipy import signal
import synth as Y
import cut as C
from synth import add, place, saw, sine, noise, lp, hp, bp, sweep_lp, sweep_bp, secs, NOTE, SR, N

ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(2024)
Fn = 29; B = C.BEAT; bar = C.bar


def stab(t, notes, d=.16, g=.035, pan=0., cutoff=3000.):
    s = sum(saw(NOTE(n), d, det, 24) for n in notes for det in (-.004, .004))
    q = secs(d); add(t, lp(s, cutoff) * np.exp(-q * 12) * np.minimum(q / .004, 1), g, pan, rev=.35)


def bass_note(t, n, d, g=.15, cutoff=900.):
    q = secs(d)
    b = np.tanh(2.0 * (saw(NOTE(n), d, 0, 25) + saw(NOTE(n), d, .008, 25) + 1.3 * sine(NOTE(n - 12), d)))
    place(Y.bass_bus, t, lp(b, cutoff) * np.minimum(q / .008, 1) * np.minimum((d - q) / .02, 1), g)


def whoosh(t, d=.35, g=.25, pan=0., up=True):
    q = secs(d); x = q / d
    f = (500 + 6000 * x ** 2) if up else (6500 - 6000 * x ** .5)
    s = sweep_bp(noise(d), f, 2.) * np.sin(np.pi * x) ** 2
    add(t, s, g, pan, rev=.25)


def snare(t, g=.5, pan=0.):
    q = secs(.25); s = bp(noise(.25), 1200, 7000) * np.exp(-q * 30) + np.sin(2 * np.pi * 200 * q) * np.exp(-q * 30) * .6
    add(t, s, .22 * g, pan, rev=.35)


# ================================================================= PART A (until the tape stop)
# Bars 1-4: intro
d = 2 * C.BAR * 2 + .5; q = secs(d)
pad = sum(saw(NOTE(Fn + 12 + iv), d, det, 30) for iv in (0, 3, 7, 10, 14) for det in (-.003, .003))
pad = sweep_lp(pad, 220 + 900 * (q / d) ** 1.5) * np.minimum(q / 2., 1) * np.minimum((d - q) / .3, 1)
add(0., pad, .03, rev=.6)
for t in C.INTRO_KICKS:
    Y.heartbeat(t, .55 if t < bar(5) else .6)
for b0, n in ((1, Fn), (3, Fn - 4), (4, Fn + 3)):
    dd = C.BAR * (2 if b0 == 1 else 1); qq = secs(dd)
    add(bar(b0), lp(saw(NOTE(n), dd, 0, 12), 180) * np.minimum(qq / .3, 1) * np.minimum((dd - qq) / .2, 1) + .6 * sine(NOTE(n), dd) * np.minimum(qq / .3, 1) * np.minimum((dd - qq) / .2, 1), .07, rev=.2)
arp = [0, 7, 12, 15, 19, 15, 12, 7]
for k in range(int(2 * C.BAR / (B / 2))):
    t = bar(3) + k * B / 2; n = Fn + 36 + arp[k % 8]
    Y.pluck_bell(t, NOTE(n), .018 + .012 * k / 16, -.5 if k % 2 else .5)
Y.reverse_swell(bar(3), 1.2, .6); Y.reverse_swell(bar(5), 1.5, .9)
for k in range(6):                                          # petals open on bar 4, beats 3-4
    Y.tick(bar(4, 2) + k * B / 4, 900 + 80 * (k % 2), .07, -.3 if k % 2 else .3)
for v, f, pan in ((C.CINDER, 82.4, -.5), (C.VESPER, 98., 0.), (C.GLACIER, 110., .5)):
    Y.hum(0., C.DROP, f, 99., 1., pan, .02)
q = secs(C.DROP - 6.6); add(6.6, hp(noise(C.DROP - 6.6), 4000) * np.minimum(q / 1., 1), .012, 0, rev=.2)   # pilot hiss
# Bars 5-6: the groove arrives
for b0 in (5, 6):
    for k in range(4):
        t = bar(b0, k)
        if k == 2:
            Y.clap(t, .7)
        Y.hat(t + B / 2, .45, .3 if k % 2 else -.3)
        bass_note(t, Fn + 12, B * .9, .10, 500)
for k in range(4):                                          # the nozzle core pulses on the beat
    t = bar(5, k); qq = secs(.3); add(t, sine(NOTE(Fn + 48 + 7 * (k % 2)), .3) * np.exp(-qq * 12), .03, rev=.5)
for k, pan in enumerate((.5, -.5, 0.)):                     # lamps fire with the name cards
    t = bar(6, k); add(t, lp(noise(.1), 2200) * np.exp(-secs(.1) * 45), .3, pan, rev=.3); Y.taiko(t, .35, pan); whoosh(t - .05, .25, .12, -pan)
Y.impact(bar(6, 3), .5, 0, .6)
# Bar 7: build
for k in range(4):
    t = bar(7, k); Y.kick(t, .8); Y.taiko(t, .5, (-.4, .4, -.2, .2)[k]); whoosh(t - .06, .2, .15, (-.6, .6, -.6, .6)[k])
    for h in range(2):
        snare(t + h * B / 2, .4 + .1 * k)
    bass_note(t, Fn + 12 + (0, 0, 3, 5)[k], B * .9, .12, 600 + 200 * k)
Y.riser(bar(7), bar(8, 3), 1.3)
# Bar 8: countdown 3-2-1, the roll, a dead beat
for k in range(3):
    t = bar(8, k)
    Y.braam(t, Fn + (0, 3, 5)[k], .5, B * 1.1, 2200.); Y.impact(t, .6, 0, .7); Y.kick(t, .9)
    n_hits = (4, 8, 8)[k]
    for j in range(n_hits):
        snare(t + j * B / n_hits, .45 + .4 * j / n_hits, .2 if j % 2 else -.2)
# Bars 9-13: THE DROP
Y.braam(C.DROP, Fn, 1.5, 3.4, 3000.); Y.impact(C.DROP, 1.4); Y.sub_drop(C.DROP, 110, 24, 2.6, 1.2)
riff = [Fn + 12, Fn + 12, Fn + 24, Fn + 12, Fn + 15, Fn + 12, Fn + 19, Fn + 17]
chords = [(Fn + 36, Fn + 39, Fn + 43), (Fn + 32, Fn + 36, Fn + 39), (Fn + 34, Fn + 38, Fn + 41), (Fn + 36, Fn + 39, Fn + 43)]
for i, t in enumerate(C.DROP_KICKS):
    Y.kick(t, 1.)
    if i % 2 == 1:
        Y.clap(t, .95)
    Y.hat(t + B / 2, .9, .35 if i % 2 else -.35)
    for h in (1, 3):
        Y.hat(t + h * B / 4, .35, .2 if h == 1 else -.2)
    for h in range(2):
        bass_note(t + h * B / 2, riff[(2 * i + h) % 8], B / 2 * .9, .17, 1100)
    stab(t + B / 2, chords[(i // 8) % 4], .14, .04, .3 if i % 2 else -.3)
for b0 in (11, 12, 13):
    Y.impact(bar(b0), .7, 0, .8); Y.braam(bar(b0), Fn + (0, 3, 5)[b0 - 11], .5, 1.6, 2400.)
for sh in C.SHOTS:                                          # a whoosh on every whip cut
    a0, a1, name, whip, fl = sh
    if C.DROP < a0 < C.RAMP0 and whip:
        whoosh(a0 - .12, .3, .3, math.copysign(.7, whip))
t_pb = bar(10, 3); qq = secs(.9); x = qq / .9                # the pass-by, with doppler
pb = sine(260 * (1.25 - .5 * (np.tanh((x - .35) * 9) * .5 + .5)), .9) * np.exp(-((x - .35) / .25) ** 2)
pb = pb + sweep_bp(noise(.9), 4000 - 3000 * x, 2.) * np.exp(-((x - .35) / .3) ** 2)
for k in range(6):
    a, b = int(len(qq) * k / 6), int(len(qq) * (k + 1) / 6)
    place(Y.dry, t_pb + a / SR, pb[a:b] * np.hanning(b - a) * 2, .4, -.8 + 1.6 * (k + .5) / 6)
# Engine roar under the drop (sidechain-free so it carries the speed)
t0 = C.DROP - .1; d = C.RAMP0 - t0 + .5; q = secs(d)
bst = np.interp(q, q[::480], [C.boost(C.tau(t0 + x)) for x in q[::480]])
n = noise(d); roar = lp(n, 240) * 2.0 + bp(n, 300, 2600) * .5 + np.tanh(2 * saw(48 + 20 * bst, d, 0, 25)) * .45
add(t0, roar * bst, .16, -.1, rev=.1); add(t0 + .013, roar * bst, .15, .1, rev=0.)

# ---- render part A, then glitch the montage and tape-stop into slow motion
L = int(3.0 * SR); tq = np.arange(L) / SR
ir = np.stack([rng.normal(size=L), rng.normal(size=L)], 1) * np.exp(-tq * 2.6)[:, None]
for c in range(2):
    ir[:, c] = lp(ir[:, c], 5000) * .6 + lp(ir[:, c], 1500) * .4
ir[:int(.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))


def render_bus():
    wet = np.stack([signal.fftconvolve(Y.send[:, c], ir[:, c])[:N] for c in range(2)], 1)
    return Y.dry + wet * .5 + Y.bass_bus * Y.duck[:, None]


A = render_bus()
# Stutter: over the last two beats of the montage, every sixteenth repeats the start of its beat.
st0 = bar(13, 2); s16 = int(B / 4 * SR)
for k in range(8):
    i = int((st0 + k * B / 4) * SR); src = int((st0 + (k // 2) * B / 2) * SR)
    if k % 2:
        A[i:i + s16] = A[src:src + s16] * np.linspace(1, .7, s16)[:, None]
# Silence on the countdown's last beat.
i0, i1 = int(bar(8, 3) * SR), int(C.DROP * SR)
A[i0:i1] *= np.concatenate([np.linspace(1, .02, 900), np.full(i1 - i0 - 900, .02)])[:, None]
# Tape stop: playback rate falls from 1 to 0 over 0.75 s.
i0 = int(C.RAMP0 * SR); Lt = int(.75 * SR); rate = (1 - np.arange(Lt) / Lt) ** 1.4
pos = i0 + np.cumsum(rate)
ts = np.stack([np.interp(pos, np.arange(len(A)), A[:, c]) for c in range(2)], 1)
A[i0:i0 + Lt] = ts * np.linspace(1, .2, Lt)[:, None]; A[i0 + Lt:] = 0
Y.dry[:] = 0; Y.send[:] = 0; Y.bass_bus[:] = 0; Y.duck[:] = 1

# ================================================================= PART B (slow motion and the logo)
# The countdown's silent beat sucks inward into the drop (on this bus, so the silence gate leaves it).
qq = secs(B); add(bar(8, 3), Y.sweep_bp(noise(B), np.linspace(800, 9000, len(qq)), 2) * (qq / B) ** 3, .25, rev=.1)
d = C.LOGO_T - C.RAMP0 + .3; q = secs(d)
drone = sum(saw(NOTE(Fn + iv), d, det, 20) for iv in (0, 12, 19) for det in (-.003, .003))
add(C.RAMP0 + .3, lp(drone, 260) * np.minimum(q / .4, 1) * np.minimum((d - q) / .2, 1), .07, rev=.5)
Y.heartbeat(C.RAMP0 + .55, 1.); Y.heartbeat(C.RAMP0 + 1.35, .9)
qq = secs(d); add(C.RAMP0 + .3, sine(NOTE(Fn + 48) * (1 + .002 * np.sin(qq * 3)), d) * (qq / d) ** 2, .03, rev=.8)
Y.reverse_swell(C.LOGO_T, 1.3, 1.2)
# ---- the light-painted blitzedo: launch, writing, crystallise, sweep, heartbeat
L0 = C.LOGO_T; W0, W1 = L0 + C.T_WRITE0, L0 + C.T_WRITE1
Y.impact(L0, .8, 0, .7); Y.sub_drop(L0, 80, 26, 1.6, .7)
for cid, pan in ((0, 0.), (1, .6), (2, -.6)):               # three comets leave the nozzles
    Y.zap(L0 + .02 * cid, C.T_WRITE0 + .1, pan * .3, pan, .9)
    Y.reverse_swell(W0, .45, .35)
import logo_vec as LV
pens = {0: (NOTE(Fn + 52), -.6, -.25), 1: (NOTE(Fn + 55), -.15, .25), 2: (NOTE(Fn + 51), .35, .7)}
for cid, (hz, p0, p1) in pens.items():                       # the laser pens, panning as they write
    d = W1 - W0; q = secs(d); x = q / d
    tone = np.sin(2 * np.pi * np.cumsum(hz * (1 + .012 * np.sin(2 * np.pi * 11 * q)) * (1 + .06 * x)) / SR)
    sizzle = bp(noise(d), 3000, 9000) * (.5 + .5 * np.sin(2 * np.pi * 23 * q) ** 2)
    cr = (rng.random(len(q)) < .006) * rng.normal(size=len(q)); cr = bp(np.convolve(cr, np.exp(-np.arange(90) / 9.), 'same'), 2000, 9000)
    sgn = (tone * .5 + sizzle * .35 + cr * .7) * np.minimum(x / .05, 1) * np.minimum((1 - x) / .05, 1)
    for k in range(8):
        a, b = int(len(q) * k / 8), int(len(q) * (k + 1) / 8)
        place(Y.dry, W0 + a / SR, sgn[a:b] * np.hanning(b - a) * 2, .09, p0 + (p1 - p0) * (k + .5) / 8)
    place(Y.send, W0, sgn, .05, (p0 + p1) / 2)
yaman = [0, 2, 4, 6, 7, 9, 11, 12]
for cid, letters in LV.COMETS.items():                       # a bell as each letter closes
    for j, li in enumerate(letters):
        tl = W0 + (W1 - W0) * (j + 1) / len(letters)
        Y.pluck_bell(tl, NOTE(Fn + 36 + yaman[li]), .06, -.7 + 1.4 * li / 7); Y.taiko(tl, .2, -.7 + 1.4 * li / 7)
q = secs(3.6); add(L0, lp(noise(3.6), 140) * np.exp(-q * .9) * 1.6, .22, rev=.3)
# Crystallise on the bar-16 downbeat.
Y.reverse_swell(bar(16), .9, 1.1)
Y.impact(bar(16), 1.5); Y.sub_drop(bar(16), 100, 22, 3.0, 1.2)
Y.braam(bar(16), Fn, 1.5, 3.4, 3400., 0, chord=(0, 7, 12, 16, 18, 23))
for k in range(70):                                          # crystal pings racing left to right with the fill
    tk = bar(16) + (k / 70) ** 1.2 * B * 1.1; hz = 2200 + rng.random() * 6000; qq = secs(.4)
    add(tk, np.sin(2 * np.pi * hz * qq) * np.exp(-qq * (14 + rng.random() * 20)), .028, -.8 + 1.6 * k / 70, rev=.6)
for iv in (0, 7, 16, 18, 23):
    qd = secs(3.); add(bar(16), sine(NOTE(Fn + 36 + iv), 3.) * np.exp(-qd * .7) * np.minimum(qd / .2, 1), .03, rev=.8)
q = secs(C.T_SWEEP1 - C.T_SWEEP0 + .3); x = np.linspace(0, 1, len(q))   # the light sweep
shing = sweep_bp(noise(len(q) / SR), 2000 + 9000 * x, 4) * np.sin(np.pi * x) + sine(3000 + 4000 * x, len(q) / SR) * np.sin(np.pi * x) * .15
for k in range(6):
    a, b = int(len(q) * k / 6), int(len(q) * (k + 1) / 6)
    place(Y.dry, L0 + C.T_SWEEP0 + a / SR, shing[a:b] * np.hanning(b - a) * 2, .14, -.7 + 1.4 * (k + .5) / 6)
th = L0 + C.T_HEART                                          # the heartbeat runs through every letter
Y.heartbeat(th, 1.1)
for iv in (0, 12, 19, 24, 28):
    qd = secs(1.4); add(th + .05, sine(NOTE(Fn + 36 + iv), 1.4) * np.exp(-qd * 1.6) * np.minimum(qd / .05, 1), .025, rev=.8)
Bmix = render_bus()

# ================================================================= master bus
mix = A + Bmix
mix = hp(mix.T, 22).T
peak = signal.lfilter([1 - .9995], [1, -.9995], np.abs(mix).max(1))
thr = .5; gain = np.where(peak > thr, (thr + (peak - thr) / 3) / np.maximum(peak, 1e-9), 1.)
mix *= gain[:, None]; mix = np.tanh(mix * 1.6) / 1.6
q = np.arange(N) / SR; mix *= (np.minimum(q / .05, 1) * np.clip((30. - q) / .6, 0, 1))[:, None]
mix /= max(1e-9, np.abs(mix).max()) / .89
with wave.open(str(ROOT / 'BLITZ_score.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes(np.int16(np.clip(mix, -1, 1) * 32767).tobytes())
print('SCORE COMPLETE', ROOT / 'BLITZ_score.wav')
