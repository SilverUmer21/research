"""blitzedo, built from the real vector outlines of Barlow Condensed Bold.

Produces three meshes for the light-painted reveal:
  letters   extruded glass letters: front face (earcut with holes), a bevel ring, sides, back
  strokes   tube paths the three comets travel: a loop out of each car's nozzle, then the letter
            outlines in writing order; every vertex knows the time the comet head reaches it
  sparks    particles shed along the strokes, each with its emission time
Text reads left to right along +z, standing in the y-z plane and facing -x (towards the cars).
"""
import math
import numpy as np
import mapbox_earcut as earcut
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from engine import Mesh

TEXT = 'blitzedo'
COMETS = {0: (0, 1, 2), 1: (3, 4, 5), 2: (6, 7)}      # magenta: b l i, cyan: t z e, orange: d o


class FlatPen(BasePen):
    def __init__(self, gs, steps=10):
        super().__init__(gs); self.contours = []; self.cur = None; self.steps = steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for k in range(1, self.steps + 1):
            t = k / self.steps
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for k in range(1, self.steps + 1):
            t = k / self.steps; a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _closePath(self):
        c = self.cur
        if len(c) > 1 and np.allclose(c[0], c[-1]):
            c = c[:-1]
        self.contours.append(np.array(c, float)); self.cur = None

    _endPath = _closePath


def area(c):
    x, y = c[:, 0], c[:, 1]; return .5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def inside(pt, poly):
    x, y = pt; n = len(poly); c = False
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            c = not c
    return c


def glyphs(font_path, width, base_y):
    f = TTFont(font_path); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    total = sum(gs[cmap[ord(ch)]].width for ch in TEXT); s = width / total
    out = []; pen_x = 0.
    for i, ch in enumerate(TEXT):
        g = gs[cmap[ord(ch)]]; p = FlatPen(gs); g.draw(p)
        cs = [np.column_stack([(c[:, 0] + pen_x) * s, c[:, 1] * s + base_y]) for c in p.contours]
        outers = [c for c in cs if area(c) < 0]; holes = [c for c in cs if area(c) >= 0]
        shapes = []
        for o in outers:
            hs = [h for h in holes if inside(h[0], o)]
            shapes.append((o, hs))
        out.append(dict(ch=ch, index=i, shapes=shapes, contours=cs))
        pen_x += g.width
    return out


def build(font_path, x0, width=14., base_y=1.1, thick=.55, bevel=.07):
    """Returns (letters Mesh, strokes data, sparks data, info)."""
    gl = glyphs(font_path, width, base_y); z0 = -width / 2
    P = lambda u, v, x: (x, v, z0 + u)                  # glyph plane (u, v) -> world
    m = Mesh(); m.name = 'glasslogo'; rows = m.data
    for g in gl:
        li = float(g['index'])
        for outer, holes in g['shapes']:
            ring_pts = [outer] + holes
            verts = np.concatenate(ring_pts).astype(np.float32); ends = np.cumsum([len(r) for r in ring_pts]).astype(np.uint32)
            tri = earcut.triangulate_float32(verts, ends).reshape(-1, 3)
            for a, b, c in tri:                          # front (faces -x) and back
                for k in (a, c, b):
                    u, v = verts[k]; rows.append([*P(u, v, x0), -1, 0, 0, li, 0, 0, 0., u, v - base_y])
                for k in (a, b, c):
                    u, v = verts[k]; rows.append([*P(u, v, x0 + thick), 1, 0, 0, li, 0, 0, 3., u, v - base_y])
            for c in ring_pts:                           # bevel ring and side walls
                n = len(c); d = np.roll(c, -1, 0) - c; L = np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
                segn = np.column_stack([-d[:, 1], d[:, 0]]) / L          # material is on the right
                vn = segn + np.roll(segn, 1, 0); vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-9
                smooth_ok = np.sum(segn * np.roll(segn, 1, 0), 1) > .82
                for i in range(n):
                    j = (i + 1) % n
                    na = vn[i] if smooth_ok[i] else segn[i]; nb = vn[j] if smooth_ok[j] else segn[i]
                    (ua, va), (ub, vb) = c[i], c[j]
                    for xa, xb, tilt, mat in ((x0, x0 + bevel, .75, 1.), (x0 + bevel, x0 + thick, 0., 2.)):
                        def nrm(nv):
                            v3 = np.array([-tilt, nv[1] * (1 - tilt * .3), nv[0] * (1 - tilt * .3)]); return v3 / np.linalg.norm(v3)
                        A, B = P(ua, va, xa), P(ub, vb, xa); Cc, D = P(ub, vb, xb), P(ua, va, xb)
                        for pt, nv, uv in ((A, na, (ua, va)), (Cc, nb, (ub, vb)), (B, nb, (ub, vb)), (A, na, (ua, va)), (D, na, (ua, va)), (Cc, nb, (ub, vb))):
                            rows.append([*pt, *nrm(nv), li, 0, 0, mat, uv[0], uv[1] - base_y])
    info = dict(height=max(c[:, 1].max() for g in gl for c in g['contours']) - base_y, width=width, x0=x0, base_y=base_y,
                bowls=[(g['index'], float(np.mean(h[:, 0])), float(np.mean(h[:, 1]))) for g in gl for o, hs in g['shapes'] for h in hs])
    return m, gl, info


def comet_paths(gl, x0, nozzles, t_launch, t_write0, t_write1, width=14.):
    """Per comet: an (N,3) path, per-point arrival time and visibility (0 jump, .6 launch loop, 1 letter)."""
    z0 = -width / 2; P = lambda u, v: np.array([x0 - .03, v, z0 + u])
    out = []
    for cid, letters in COMETS.items():
        pts, vis = [], []
        for li in letters:
            for c in gl[li]['contours']:
                cc = np.vstack([c, c[:1]])
                if pts:                                   # lift and jump to the next contour
                    a, b = pts[-1], P(*cc[0])
                    for k in range(1, 6):
                        pts.append(a + (b - a) * k / 6 + np.array([-.25 * math.sin(math.pi * k / 6), 0, 0])); vis.append(0.)
                for u, v in cc:
                    pts.append(P(u, v)); vis.append(1.)
        pts = np.array(pts); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        tw = t_write0 + (t_write1 - t_write0) * s / s[-1]
        # The launch loop: out of the nozzle backwards, up over the car, and down onto the first stroke.
        nz = np.array(nozzles[cid]); start = pts[0]
        c1 = nz + np.array([-3.5, 2.2, 0.]); c2 = np.array([nz[0] + 6., 4.6, nz[2] * 1.6]); loop = []
        for k in range(48):
            t = k / 48; a, b, cc_, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            loop.append(a * nz + b * c1 + cc_ * c2 + d * start)
        loop = np.array(loop); tl = t_launch + (t_write0 - t_launch) * (np.arange(48) / 48) ** .8
        out.append(dict(pts=np.vstack([loop, pts]), t=np.concatenate([tl, tw]), vis=np.concatenate([np.full(48, .6), vis]), comet=cid))
    return out


def stroke_mesh(paths, sides=7):
    m = Mesh(); m.name = 'strokes'; rows = m.data
    for p in paths:
        pts, ts, vis, cid = p['pts'], p['t'], p['vis'], p['comet']
        tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
        ref = np.array([1., 0, 0]); rings = []
        for i in range(len(pts)):
            n1 = np.cross(tang[i], ref)
            if np.linalg.norm(n1) < .1:
                n1 = np.cross(tang[i], [0, 1., 0])
            n1 /= np.linalg.norm(n1); n2 = np.cross(tang[i], n1)
            rings.append([n1 * math.cos(2 * math.pi * k / sides) + n2 * math.sin(2 * math.pi * k / sides) for k in range(sides)])
        for i in range(len(pts) - 1):
            if vis[i] == 0 and vis[i + 1] == 0:
                continue
            for k in range(sides):
                kk = (k + 1) % sides
                for ii, kx in ((i, k), (i + 1, k), (i + 1, kk), (i, k), (i + 1, kk), (i, kk)):
                    rows.append([*pts[ii], *rings[ii][kx], float(cid), ts[ii], min(vis[i], vis[i + 1]), 0., kx / sides, 0.])
    return m


def spark_mesh(paths, count=2400, seed=5):
    rng = np.random.default_rng(seed); m = Mesh(); m.name = 'logosparks'; rows = m.data
    for k in range(count):
        p = paths[k % 3]; i = rng.integers(0, len(p['pts']) - 1)
        if p['vis'][i] == 0:
            continue
        f = rng.random(); pos = p['pts'][i] * (1 - f) + p['pts'][i + 1] * f; t0 = p['t'][i] * (1 - f) + p['t'][i + 1] * f
        d = rng.normal(size=3); d /= np.linalg.norm(d)
        for uv in [(-1, -1), (1, -1), (1, 1), (-1, -1), (1, 1), (-1, 1)]:
            rows.append([*pos, *d, float(p['comet']), t0, rng.random(), 0., *uv])
    return m
