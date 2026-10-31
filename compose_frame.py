"""Overlay caption and lantern score labels on a rendered Emotion Lanterns frame.

  python compose_frame.py hero

Reads renders/<shot>.png and renders/<shot>.json from lanterns_scene.py, writes renders/<shot>_final.png.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE / 'fonts/BarlowCondensed-Bold.ttf'
INK = (255, 244, 232)
SHADOW = (63, 26, 143)
FAMILY = {'warm': (255, 176, 58), 'blue': (79, 139, 255), 'teal': (79, 240, 208), 'white': (255, 255, 255)}

shot = sys.argv[1] if len(sys.argv) > 1 else 'hero'
meta = json.loads((HERE / 'renders' / f'{shot}.json').read_text())
im = Image.open(HERE / 'renders' / f'{shot}.png').convert('RGB')
d = ImageDraw.Draw(im)


def font(size):
    return ImageFont.truetype(str(FONT), size)


def text(xy, s, f, fill=INK, anchor='la', shadow=4):
    x, y = xy
    d.text((x + shadow * .6, y + shadow), s, font=f, fill=SHADOW, anchor=anchor)  # tinted drop, never grey
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)


W, H = im.size
text((W / 2, 150), f'“{meta["text"]}”', font(124), anchor='ma', shadow=7)
text((W / 2, 300), '28 EMOTIONS  ·  ONE SENTENCE', font(40), anchor='ma')

lit = sorted(((v[2], k, v) for k, v in meta['lanterns'].items() if v[2] > 0), reverse=True)
for p, emo, (x, y, _, fam) in lit:
    below = y > H * .62  # front row: label under the lantern so it never covers the dais letters
    ly = y + 250 if below else y - 120
    d.line([(x, y + 150), (x, ly - 58)] if below else [(x, y - 28), (x, ly + 52)], fill=INK, width=3)
    text((x, ly), f'{round(p * 100)}%', font(58 if p > .5 else 46), fill=FAMILY[fam], anchor='mb')
    text((x, ly + 4), emo.upper(), font(30), anchor='ma', shadow=3)

if meta.get('placeholder_scores'):
    text((W - 28, 28), 'MOCKUP · SCORES ARE PLACEHOLDERS', font(22), anchor='ra', shadow=2)
im.save(HERE / 'renders' / f'{shot}_final.png')
print('WROTE', HERE / 'renders' / f'{shot}_final.png')
