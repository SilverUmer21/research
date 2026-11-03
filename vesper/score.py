"""Original score and sound design for VESPER / 09 - MAGENTA CUT.

Synthesised with NumPy only and locked to the picture timeline in magenta.py:
heartbeat -> lava crackle as the veins flood -> lamp clunk -> petal ticks ->
sputter pops -> ignition boom and roar (follows the boost curve) -> pass-by
whooshes on the cuts -> cooling pings -> plucked notes as the Barah Goti lattice
lights (F Lydian, the scale of Raag Yaman) -> last heartbeat.
"""
from pathlib import Path
import wave
import numpy as np
import magenta as m

ROOT = Path(__file__).resolve().parent
SR = 48000; N = int(m.DURATION * SR)
rng = np.random.default_rng(909)
out = np.zeros((N, 2))
F = 43.654  # F1


def add(t, s, vol=1., pan=0.):
    i = round(t * SR); n = min(len(s), N - i)
    if n <= 0 or i < 0:
        return
    x = np.asarray(s[:n]) * vol; p = np.clip(pan, -1, 1)
    out[i:i + n, 0] += x * np.sqrt((1 - p) * .5); out[i:i + n, 1] += x * np.sqrt((1 + p) * .5)


def secs(d):
    return np.arange(round(d * SR)) / SR


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def thump(t, v=.5, hz=52., d=.45):
    q = secs(d); f = hz * (1 + 1.6 * np.exp(-q * 28))
    add(t, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-q * 9) * (1 - np.exp(-q * 400)), v)


def noise_burst(t, d, v, k=5, decay=40., pan=0.):
    q = secs(d); add(t, lowpass(rng.normal(size=len(q)), k) * np.exp(-q * decay), v, pan)


def tick(t, hz, v=.05, pan=0.):
    q = secs(.09); add(t, (np.sin(2 * np.pi * hz * q) + .4 * np.sin(2 * np.pi * hz * 1.7 * q)) * np.exp(-q * 60), v, pan)


def pad(t, d, notes, v):
    q = secs(d); env = np.minimum(q / 1.8, 1) * np.minimum((d - q) / 1.5, 1)
    for k, hz in enumerate(notes):
        s = np.sin(2 * np.pi * hz * q) + .3 * np.sin(2 * np.pi * hz * 1.003 * q + k) + .12 * np.sin(2 * np.pi * hz * 2 * q)
        add(t, s * env, v / len(notes), -.5 if k % 2 else .5)


def pluck(t, hz, v=.12, d=2.2, pan=0.):
    """Karplus-Strong string, like the sitar-ish phrases in the BarahAI client."""
    n = round(d * SR); p = max(2, round(SR / hz)); buf = rng.uniform(-1, 1, p); y = np.empty(n)
    for i in range(n):
        y[i] = buf[i % p]; buf[i % p] = .996 * .5 * (buf[i % p] + buf[(i + 1) % p])
    add(t, y * np.minimum(np.arange(n) / 200, 1), v, pan)


def whoosh(t, d, v, down=True):
    q = secs(d); n = rng.normal(size=len(q)); env = np.sin(np.pi * q / d) ** 2
    lo = lowpass(n, 40); hi = n - lowpass(n, 6)
    mix = (lo * (1 - q / d) + hi * .35 * (q / d)) if down else (lo * (q / d) + hi * .35 * (1 - q / d))
    add(t, mix * env, v, -.6 + 1.2 * (q[len(q) // 2] / d))


# 0-3.2 s: the heart wakes in the dark.
pad(0., 8.5, [F * 2, F * 3, F * 4.8], .10)
for b in m.BEATS:
    thump(b, .55); thump(b + .17, .30, 46.)
# 3-7.6 s: lava floods the arteries - crackle density follows the fill front.
q = secs(4.8); dens = np.clip(q / 3.5, 0, 1) ** 1.5
cr = (rng.random(len(q)) < dens * .004) * rng.normal(size=len(q))
cr = np.convolve(cr, np.exp(-np.arange(200) / 25.), 'same')
add(3.0, cr, .32)
q = secs(4.6); f = 110 + 330 * (q / 4.6) ** 2
add(3.0, np.sin(2 * np.pi * np.cumsum(f) / SR) * (q / 4.6) ** 1.5 * np.minimum((4.6 - q) / .3, 1), .045)
add(3.0, lowpass(rng.normal(size=len(q)), 9) * (q / 4.6) ** 2, .06)
for k, hz in enumerate([F * 8, F * 12, F * 16, F * 18, F * 24]):
    pluck(3.4 + k * .8, hz, .05, 1.6, (-.4 if k % 2 else .4))
# 8.4 s: lamps - a fluorescent double clunk and hum.
for tt in (8.40, 8.55):
    noise_burst(tt, .08, .10, 3, 70.); thump(tt, .18, 120., .2)
q = secs(3.6); add(8.55, np.sin(2 * np.pi * 100 * q) * .5 * np.exp(-q * .6), .012)
pad(8.0, 7.5, [F * 2, F * 3, F * 4, F * 6], .10)
for k in range(8):
    pluck(8.6 + k * .42, [F * 8, F * 12, F * 9.5, F * 12][k % 4], .045, 1.2, np.sin(k) * .5)
# 12.2-13.5 s: nozzle petals deploy.
for k in range(6):
    tick(12.25 + k * .2, 640 + 60 * (k % 2), .05, -.3 if k % 2 else .3)
# 13.9-14.75 s: sputter pops, then the charge sweep into ignition.
for p, a in zip(m.POPS, (.25, .32, .40)):
    noise_burst(p, .25, a, 7, 18.); thump(p, a * .8, 60.)
q = secs(.9); f = 80 + 600 * (q / .9) ** 3
add(m.IGNITION - .9, np.sin(2 * np.pi * np.cumsum(f) / SR) * (q / .9) ** 2, .08)
add(m.IGNITION - .9, lowpass(rng.normal(size=len(q)), 4) * (q / .9) ** 3, .12)
# 15.15 s: ignition boom, then a roar driven by the same boost curve as the plumes.
thump(m.IGNITION, .9, 38., 1.4); noise_burst(m.IGNITION, 1.2, .5, 25, 4.)
t0 = m.IGNITION - .1; q = secs(m.DURATION - t0)
env = np.interp(q, q[::480], [m.boost(t0 + x) for x in q[::480]])
spd = np.interp(q, q[::480], [m.speed(t0 + x) / 38 for x in q[::480]])
n = rng.normal(size=len(q)); lo = lowpass(n, 90); mid = lowpass(n, 8) - lo
roar = (lo * 1.5 + mid * (.15 + .2 * spd)) * env * (.85 + .1 * np.sin(2 * np.pi * 7.7 * q))
add(t0, roar, .40, -.2); add(t0 + .011, roar, .37, .2)
ph = 2 * np.pi * np.cumsum(55 + 35 * env + 70 * spd) / SR
add(t0, (np.sin(ph) + .15 * np.sin(2.01 * ph)) * env, .07)
whine = 2 * np.pi * np.cumsum(420 + 900 * spd) / SR
add(t0, np.sin(whine) * env * spd * .5, .02)
# Driving pulse while the car runs: F minor bass in eighths at 128 bpm.
beat = 60 / 128 / 2; bass = [F * 2, F * 2, F * 2.4, F * 3]
t = m.IGNITION + .5; k = 0
while t < 25.6:
    hz = bass[(k // 2) % 4]; q2 = secs(beat * .95)
    add(t, np.tanh(2.2 * np.sin(2 * np.pi * hz * q2)) * np.exp(-q2 * 5), .09)
    if k % 4 == 0:
        thump(t, .25, 50., .3)
    if k % 4 == 2:
        noise_burst(t, .05, .05, 2, 90., .3)
    t += beat; k += 1
# Cuts into the run and the chase get pass-by whooshes.
whoosh(16.7, .9, .35); whoosh(22.1, 1.1, .42)
# 25.8-29.6 s: cool-down. Roar collapses, hot metal ticks, the board lights.
q = secs(1.6); f = 400 * np.exp(-q * 1.6) + 60
add(25.8, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-q * 1.5), .06)
for k in range(14):
    tick(26.9 + rng.random() * 2.4, 2400 + rng.random() * 1800, .018, rng.uniform(-.7, .7))
pad(26.8, 3.2, [F * 2, F * 3, F * 4 * 1.25, F * 6], .11)
yaman = [1, 9 / 8, 5 / 4, 45 / 32, 3 / 2, 5 / 3, 15 / 8, 2]  # F G A B C D E F (sharp fourth)
for k, r in enumerate(yaman):
    pluck(27.45 + k * .19, F * 8 * r, .09, 2.4, -.6 + 1.2 * k / 7)
for r in (1, 3 / 2, 5 / 4 * 2):
    pluck(28.95, F * 8 * r, .07, 1.6)
thump(29.15, .45); thump(29.32, .25, 46.)

q = np.arange(N) / SR
out *= (np.minimum(q / .25, 1) * np.clip((m.DURATION - q) / .5, 0, 1))[:, None]
out = np.tanh(out * 1.4) * .9
with wave.open(str(ROOT / 'VESPER_score.wav'), 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes(np.int16(np.clip(out, -1, 1) * 32767).tobytes())
print('SCORE COMPLETE', ROOT / 'VESPER_score.wav')
