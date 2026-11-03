"""Find a real "hijack trap" from simulated Switch games and draw it.

A trap = you step ONE rival bead during the Switch, the rival is then FORCED to capture
(Barah Goti's mandatory capture), and your reply wins more beads back. The script plays
`swap_guard` games (the recommended Switch) with the same bots as switch_sim.py, keeps the hijack with the biggest
net swing over the next two turns, prints it in notation and saves a board picture.
"""
import argparse, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import switch_sim as S
from barahai.engine.board import rc, square_name

HERE = Path(__file__).resolve().parent
FONT = str(HERE.parent / 'afterlight' / 'fonts' / 'BarlowCondensed-Bold.ttf')


def swing(trace, i, me):
    a = trace[i - 1] if i else (12, 12); b = trace[min(i + 2, len(trace) - 1)]
    return (b[me] - b[1 - me]) - (a[me] - a[1 - me])


def hunt(games, seed):
    rng = random.Random(seed); best = None
    for g in range(games):
        bots = [S.Bot(2, .05, rng), S.Bot(2, .05, rng)]
        v = S.V(S.GameState.new(S.STANDARD)); states = [v]; trace = []
        while not v.gs.is_terminal:
            v = rng.choice(S.children(v, S.RECOMMENDED)) if v.gs.turn_no < 4 else bots[v.gs.turn].pick(v, S.RECOMMENDED)
            states.append(v); trace.append((v.gs.count(0), v.gs.count(1)))
        for i, st in enumerate(states[1:]):
            if not st.hijack or i + 2 >= len(states) - 1:
                continue
            me = states[i].gs.turn; sw = swing(trace, i, me)
            nxt, rep = states[i + 2], states[i + 3]
            if nxt.hijack or rep.hijack:
                continue  # the rival's reply must be a normal (forced) move, not their own Switch
            forced = any(states[i + 1].gs.is_capture(a) for a in states[i + 1].gs.legal_actions()) and nxt.gs.count(me) < states[i + 1].gs.count(me)
            if forced and (best is None or sw > best[0]):
                best = (sw, states[i].gs, states[i + 1].gs, states[i + 2].gs, states[i + 3].gs, me)
    return best


def diff(a, b, side):
    gone = a.bb[side] & ~b.bb[side]; new = b.bb[side] & ~a.bb[side]
    return [square_name(s) for s in S.iter_bits(gone)], [square_name(s) for s in S.iter_bits(new)]


def draw(states, me, path):
    W, H = 1500, 560; im = Image.new('RGB', (W, H), '#07040e'); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 30); fs = ImageFont.truetype(FONT, 22)
    titles = ['1  SWITCH: you step a rival bead', '2  rival is FORCED to capture', '3  your chain capture']
    you = '#ff3dc8'; rival = '#2fe6ff'; line = '#5a2a6e'
    for k, (a, b) in enumerate(zip(states, states[1:])):
        ox = 40 + k * 490; oy = 110; s = 92
        d.text((ox, 30), titles[k], font=f, fill='#f2d9ff')
        P = lambda sq: (ox + rc(sq)[1] * s + 20, oy + rc(sq)[0] * s + 10)
        for r in range(5):
            for c in range(5):
                x, y = ox + c * s + 20, oy + r * s + 10
                if c < 4: d.line((x, y, x + s, y), fill=line, width=3)
                if r < 4: d.line((x, y, x, y + s), fill=line, width=3)
                if (r + c) % 2 == 0 and r < 4 and c < 4: d.line((x, y, x + s, y + s), fill=line, width=3)
                if (r + c) % 2 == 0 and r < 4 and c > 0: d.line((x, y, x - s, y + s), fill=line, width=3)
        for side in (0, 1):
            col = you if side == me else rival
            for sq in S.iter_bits(b.bb[side]):
                x, y = P(sq); d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=col)
            for sq in S.iter_bits(a.bb[side] & ~b.bb[side]):
                x, y = P(sq); d.ellipse((x - 22, y - 22, x + 22, y + 22), outline=col, width=3)
            for sq in S.iter_bits(b.bb[side] & ~a.bb[side]):
                x, y = P(sq); d.ellipse((x - 30, y - 30, x + 30, y + 30), outline='#ffffff', width=3)
        if k == 0:
            for sq in S.iter_bits(b.bb[1 - me] & ~a.bb[1 - me]):
                x, y = P(sq); d.text((x - 40, y + 30), 'hijacked', font=fs, fill='#ffffff')
    d.text((40, H - 40), 'Magenta = you · cyan = rival · hollow = where a bead was · white ring = where it arrived. Real position from a bot game (switch_sim.py, variant "swap_guard").', font=fs, fill='#b8a6cc')
    im.save(path)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--games', type=int, default=60); p.add_argument('--seed', type=int, default=5)
    a = p.parse_args()
    sw, s0, s1, s2, s3, me = hunt(a.games, a.seed)
    print('net swing for the hijacker:', sw, 'beads')
    for name, x, y, side in [('switch (rival bead)', s0, s1, 1 - me), ('rival forced capture', s1, s2, 1 - me), ('your reply', s2, s3, me)]:
        g, n = diff(x, y, side); print(f'{name}: {"/".join(g)} -> {"/".join(n)}; beads now {y.count(me)} v {y.count(1 - me)}')
    print(s0); print(s1); print(s2); print(s3)
    draw([s0, s1, s2, s3], me, HERE / 'hijack_example.png'); print('WROTE', HERE / 'hijack_example.png')


if __name__ == '__main__':
    main()
