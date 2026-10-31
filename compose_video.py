"""Text pass for the Emotion Lanterns video: one quiet caption at a time, small score labels,
a short fact card and the end card.

  python compose_video.py [first last]

Reads renders/video/frame_####.png, meta_####.json and timeline.json from lanterns_video.py and
writes renders/video/final_####.png. The letter slam is the only loud beat (owner feedback,
2026-10-31): the 3D letters are the reveal, and overlays only fade.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
VID = HERE / 'renders/video'
FONT = HERE / 'fonts/BarlowCondensed-Bold.ttf'
INK = (255, 244, 232)
SHADOW = (63, 26, 143)
FAMILY = {'warm': (255, 176, 58), 'blue': (130, 175, 255), 'teal': (79, 240, 208), 'white': (255, 255, 255)}
REPO = 'github.com/SilverUmer21/emotion-detection-in-text'
TEAM = 'Muhammad Umer  ·  Muhammad Ahmed Bajwa  ·  Muhammad Shayan Qadir'

T = json.loads((VID / 'timeline.json').read_text())
W, H = 1080, 1350
_fonts = {}


def font(size):
    size = max(6, int(size))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(str(FONT), size)
    return _fonts[size]


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def fade(f, start, end=None, ramp=12):
    a = smooth((f - start) / ramp)
    if end is not None:
        a *= smooth((end - f) / ramp)
    return a


class Layer:
    def __init__(self):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, s, size, alpha=1.0, fill=INK, anchor='ma', rise=0.0):
        """Fade in while drifting up a few pixels; tinted drop shadow, never grey."""
        if alpha <= 0:
            return
        x, y = xy[0], xy[1] + rise * (1 - alpha)
        sh = max(2, size * .05)
        a = int(255 * alpha)
        self.d.text((x + sh * .6, y + sh), s, font=font(size), fill=(*SHADOW, int(a * .85)), anchor=anchor)
        self.d.text((x, y), s, font=font(size), fill=(*fill, a), anchor=anchor)


def labels(layer, f, meta, seg, end):
    """One small line under each lit lantern; the number counts up with the light."""
    for emo, f0, target in seg['ignite']:
        x, y, p, fam = meta['lanterns'][emo]
        alpha = fade(f, f0 + 4, end, 14)
        value = target * smooth((f - f0) / 22)
        layer.text((x, y + 128), f'{emo.upper()}  {round(value * 100)}%', 30, alpha, FAMILY[fam], rise=10)


def compose(f):
    base = Image.open(VID / f'frame_{f:04d}.png').convert('RGBA')
    meta = json.loads((VID / f'meta_{f:04d}.json').read_text())
    L = Layer()
    hero, nerves = T['hero'], T['nerves']
    fa, fb = T['fact']

    labels(L, f, meta, hero, hero['exit'])
    labels(L, f, meta, nerves, fa)
    L.text((W / 2, 200), '28 EMOTIONS  ·  IT HEARD 3', 44, fade(f, 90, hero['exit']), rise=12)
    L.text((W / 2, 200), 'A CALM LINE. IT STILL HEARD NERVES.', 44, fade(f, 276, fa), rise=12)

    L.text((W / 2, 400), '9 IN 10', 210, fade(f, fa + 10, fb - 6, 16), rise=20)
    L.text((W / 2, 640), 'OF ITS “NERVOUS” CALLS ARE WRONG', 50, fade(f, fa + 28, fb - 6, 16), rise=12)
    L.text((W / 2, 1270), 'GoEmotions test set  ·  nervousness precision 0.10', 24, fade(f, fa + 28, fb - 6, 16))

    e = 492  # end card
    L.text((W / 2, 180), 'EMOTION DETECTION', 104, fade(f, e, ramp=16), rise=16)
    L.text((W / 2, 290), 'IN TEXT', 104, fade(f, e + 6, ramp=16), rise=16)
    L.text((W / 2, 430), 'DeBERTa-v3  ·  28 emotions  ·  macro F1 0.49', 40, fade(f, e + 22, ramp=16), rise=10)
    L.text((W / 2, 520), TEAM, 28, fade(f, e + 34, ramp=16))
    L.text((W / 2, 570), REPO, 32, fade(f, e + 42, ramp=16), FAMILY['warm'])

    if T.get('placeholder_scores'):
        L.text((W - 28, 28), 'MOCKUP · SCORES ARE PLACEHOLDERS', 20, .8, anchor='ra')

    out = Image.alpha_composite(base, L.im)
    flash = sum(.45 * math.exp(-(f - f0) / 2.2) for f0, amp in T['slams'] if amp > 1 and f >= f0)
    if flash > .01:
        out = Image.blend(out, Image.new('RGBA', (W, H), (255, 240, 225, 255)), min(.6, flash))
    out.convert('RGB').save(VID / f'final_{f:04d}.png')


if __name__ == '__main__':
    first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, T['frames'] - 1)
    for f in range(first, last + 1):
        if (VID / f'frame_{f:04d}.png').exists():
            compose(f)
    print('composed', first, last)
