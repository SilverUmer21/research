"""Barah Goti with a switch: bot-vs-bot experiments for the HIJACK TWELVE concept.

Uses the real BarahAI rules engine (SilverUmer21/12_beads_RL_mlops, src/barahai) and
adds the build-wreck "switch": for one turn, you move one of the RIVAL's beads.

Variants (see HIJACK-TWELVE.md for the reasoning):
  classic       plain Barah Goti, the BarahAI standard ruleset
  swap          every 12 turns a two-turn Switch window: each player in turn moves ONE rival bead
                one step (never a capture) INSTEAD of their own move
  swap_plus     same window, but the hijack step comes ON TOP of your own move
  place         same window, but you lift one rival bead and set it on any empty point
                within 2 rows/columns (the owner's "decide which enemy bead to place where")
  earned        no schedule: each time you lose beads you charge one Switch (max 1), which you
                may spend instead of a move (swap-style). A catch-up mechanic
  swap_guard    swap, plus "anchored" beads: a bead that moved last turn cannot be hijacked (RECOMMENDED)
  *_alt         the Switch opener alternates per window (default: whoever's turn it is at turn 12n)
  *_behind      the player behind in beads opens the window (level: alternate)

Usage:
  python switch_sim.py --games 120 --out results.json
  BARAHAI_SRC=/path/to/12_beads_RL_mlops/src python switch_sim.py
"""
from __future__ import annotations
import argparse, json, math, os, random, sys, time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = os.environ.get('BARAHAI_SRC', str(HERE.parents[1] / '12_beads_RL_mlops' / 'src'))
sys.path.insert(0, SRC)
from barahai.engine import GameState, Rules, STANDARD  # noqa: E402
from barahai.engine.board import FULL, iter_bits, rc  # noqa: E402
from barahai.engine.state import STOP, _key  # noqa: E402
from barahai.agents.alphabeta import evaluate  # noqa: E402
from barahai.agents.greedy import best_capture_run  # noqa: E402

FREE = Rules(forced_capture=False)
PERIOD = 12
WIN = 10_000
VARIANTS = ['classic', 'swap', 'swap_plus', 'place', 'earned', 'swap_guard', 'swap_alt', 'swap_behind', 'place_behind',
            'swap_guard_alt', 'swap_guard_behind']
RECOMMENDED = 'swap_guard'


def make(rules, bb, turn, quiet, turn_no, history):
    return GameState._make(rules, bb, turn, -1, quiet, turn_no, history)


def opener_rule(variant):
    return 'alt' if variant.endswith('_alt') else 'behind' if variant.endswith('_behind') else 'fixed'


def base_variant(variant):
    return variant.replace('_alt', '').replace('_behind', '')


def pick_opener(variant, gs):
    """Who opens the Switch window that starts at this turn (turn_no = 12n)."""
    rule = opener_rule(variant); n = gs.turn_no // PERIOD
    first = gs.rules.first_player
    alt = first if n % 2 == 1 else 1 - first
    if rule == 'fixed':
        return gs.turn
    if rule == 'alt':
        return alt
    c0, c1 = gs.count(0), gs.count(1)  # 'behind': the trailing player opens; level -> alternate
    return alt if c0 == c1 else (0 if c0 < c1 else 1)


def switch_turn(variant, v):
    """(is this a Switch turn for the side to move, opener of the current window)."""
    if base_variant(variant) not in ('swap', 'swap_plus', 'place', 'swap_guard'):
        return False, -1
    gs = v.gs; t = gs.turn_no
    if t < PERIOD:
        return False, -1
    r = t % PERIOD
    if r == 0:
        o = pick_opener(variant, gs); return gs.turn == o, o
    if r == 1:
        return True, v.opener
    if r == 2:
        return gs.turn != v.opener, v.opener
    return False, -1


@dataclass(frozen=True)
class V:
    gs: GameState
    charges: tuple = (0, 0)
    anchored: int = -1           # square of the bead that moved last (swap_guard)
    hijack: bool = False         # did this macro-turn use a switch (for stats)
    opener: int = -1             # who opened the current Switch window


def turn_ends(gs):
    """Every end-of-turn state for the side to move, expanding capture chains."""
    player = gs.turn; out = {}

    def rec(s):
        if s.is_terminal or s.turn != player:
            out[(s.key, s.quiet)] = s; return
        for a in s.legal_actions():
            rec(s.apply(a))
    rec(gs)
    return list(out.values())


def landing(before, after):
    moved = after & ~before
    return moved.bit_length() - 1 if moved else -1


def hijack_steps(gs, anchored=-1):
    """Bitboards after the side to move steps one RIVAL bead (no captures)."""
    me, foe = gs.turn, 1 - gs.turn
    tmp = GameState.from_position(gs.bb[0], gs.bb[1], foe, FREE)
    res = []
    for a in tmp.legal_actions():
        if a == STOP or tmp.is_capture(a):
            continue
        mv = tmp.describe(a)
        if mv.src == anchored:
            continue
        res.append(tmp.apply(a).bb)
    return res


def placements(gs):
    me, foe = gs.turn, 1 - gs.turn
    empty = FULL ^ (gs.bb[0] | gs.bb[1]); res = []
    for sq in iter_bits(gs.bb[foe]):
        r0, c0 = rc(sq)
        for e in iter_bits(empty):
            r1, c1 = rc(e)
            if max(abs(r1 - r0), abs(c1 - c0)) <= 2:
                bb = list(gs.bb); bb[foe] ^= (1 << sq) | (1 << e); res.append(tuple(bb))
    return res


def after_hijack(gs, bb, keep_turn):
    """State after a hijack. keep_turn: the hijacker still makes their own move (swap_plus)."""
    if keep_turn:
        return make(gs.rules, bb, gs.turn, gs.quiet, gs.turn_no, gs.history)
    nxt = 1 - gs.turn
    return make(gs.rules, bb, nxt, gs.quiet + 1, gs.turn_no + 1, gs.history + (_key(bb[0], bb[1], nxt),))


def children(v: V, variant: str):
    gs = v.gs; me = gs.turn; out = []
    sw, op = switch_turn(variant, v)
    variant = base_variant(variant)
    if sw and variant in ('swap', 'swap_guard', 'place'):
        options = placements(gs) if variant == 'place' else hijack_steps(gs, v.anchored if variant == 'swap_guard' else -1)
        for bb in options:
            out.append(V(after_hijack(gs, bb, False), v.charges, -1, True, op))
        if out:
            return out
    if sw and variant == 'swap_plus':
        for bb in hijack_steps(gs):
            mid = after_hijack(gs, bb, True)
            if mid.is_terminal:
                out.append(V(mid, v.charges, -1, True, op)); continue
            for end in turn_ends(mid):
                out.append(V(end, v.charges, -1, True, op))
        if out:
            return out
    for end in turn_ends(gs):
        ch = list(v.charges)
        if variant == 'earned' and end.count(1 - me) < gs.count(1 - me):
            ch[1 - me] = 1  # the victim of a capture charges a Switch
        out.append(V(end, tuple(ch), landing(gs.bb[me], end.bb[me]), False, op))
    if variant == 'earned' and v.charges[me]:
        ch = list(v.charges); ch[me] = 0
        for bb in hijack_steps(gs):
            out.append(V(after_hijack(gs, bb, False), tuple(ch), -1, True))
    return out


def leaf(v: V, variant):
    gs = v.gs
    if gs.is_terminal:
        w = gs.result.winner
        return 0 if w is None else (WIN if w == gs.turn else -WIN)
    s = evaluate(gs) + 100 * best_capture_run(gs)
    if base_variant(variant) == 'earned':
        s += 45 * (v.charges[gs.turn] - v.charges[1 - gs.turn])
    return s


def negamax(v, depth, alpha, beta, variant):
    if depth == 0 or v.gs.is_terminal:
        return leaf(v, variant)
    best = -math.inf
    for c in children(v, variant):
        val = -negamax(c, depth - 1, -beta, -alpha, variant)
        if val > best:
            best = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best


class Bot:
    def __init__(self, depth, eps, rng):
        self.depth, self.eps, self.rng = depth, eps, rng

    def pick(self, v, variant):
        kids = children(v, variant)
        if self.rng.random() < self.eps or self.depth == 0:
            return self.rng.choice(kids)
        scored = [(-negamax(c, self.depth - 1, -math.inf, math.inf, variant), self.rng.random(), i) for i, c in enumerate(kids)]
        return kids[max(scored)[2]]


def play(variant, bots, rng, opening=2):
    v = V(GameState.new(STANDARD)); trace = []; hijacks = []
    while not v.gs.is_terminal:
        me = v.gs.turn; before = (v.gs.count(0), v.gs.count(1))
        if v.gs.turn_no < opening * 2:
            v = rng.choice(children(v, variant))
        else:
            v = bots[me].pick(v, variant)
        if v.hijack:
            hijacks.append((len(trace), me))
        trace.append((v.gs.count(0), v.gs.count(1)))
    # A hijack "lands" if the hijacker is up material two turns later.
    landed = 0
    for i, me in hijacks:
        j = min(i + 2, len(trace) - 1); b0 = trace[i - 1] if i else (12, 12)
        if (trace[j][me] - trace[j][1 - me]) > (b0[me] - b0[1 - me]):
            landed += 1
    diffs = [a - b for a, b in trace]
    comeback = v.gs.result.winner is not None and (
        min(diffs) <= -2 if v.gs.result.winner == 0 else max(diffs) >= 2)
    leads = [1 if d > 0 else -1 if d < 0 else 0 for d in diffs]; nz = [x for x in leads if x]
    changes = sum(1 for a, b in zip(nz, nz[1:]) if a != b)
    return dict(winner=v.gs.result.winner, reason=v.gs.result.reason, turns=v.gs.turn_no, comeback=comeback,
                lead_changes=changes, hijacks=len(hijacks), landed=landed)


def run(variant, games, seed, depths=(2, 2), eps=(.05, .05)):
    rng = random.Random(seed); res = []
    for g in range(games):
        bots = [Bot(depths[k], eps[k], rng) for k in range(2)]
        if g % 2:  # alternate who has the stronger bot in skill tests
            bots = bots[::-1]
        r = play(variant, bots, rng); r['strong'] = (0 if g % 2 == 0 else 1); res.append(r)
    return res


def summary(res, skill=False):
    n = len(res); s = lambda f: sum(1 for r in res if f(r))
    out = dict(games=n,
               p0_win=s(lambda r: r['winner'] == 0) / n, p1_win=s(lambda r: r['winner'] == 1) / n,
               draw=s(lambda r: r['winner'] is None) / n,
               turns=sum(r['turns'] for r in res) / n,
               comeback=s(lambda r: r['comeback']) / max(1, s(lambda r: r['winner'] is not None)),
               lead_changes=sum(r['lead_changes'] for r in res) / n,
               hijacks=sum(r['hijacks'] for r in res) / n,
               hijack_landed=sum(r['landed'] for r in res) / max(1, sum(r['hijacks'] for r in res)))
    if skill:
        out['strong_win'] = s(lambda r: r['winner'] == r['strong']) / n
        out['weak_win'] = s(lambda r: r['winner'] is not None and r['winner'] != r['strong']) / n
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument('--games', type=int, default=120); p.add_argument('--seed', type=int, default=12)
    p.add_argument('--variants', default=','.join(VARIANTS)); p.add_argument('--out', default=str(HERE / 'results.json'))
    p.add_argument('--skill-games', type=int, default=80)
    a = p.parse_args(); table = {}
    for variant in a.variants.split(','):
        t0 = time.time()
        even = summary(run(variant, a.games, a.seed))
        skill = summary(run(variant, a.skill_games, a.seed + 1, depths=(2, 1), eps=(.05, .20)), skill=True)
        table[variant] = dict(even=even, skill=skill, seconds=round(time.time() - t0, 1))
        print(variant, json.dumps(table[variant]), flush=True)
    Path(a.out).write_text(json.dumps(dict(period=PERIOD, games=a.games, skill_games=a.skill_games, seed=a.seed, results=table), indent=2))
    print('WROTE', a.out)


if __name__ == '__main__':
    main()
