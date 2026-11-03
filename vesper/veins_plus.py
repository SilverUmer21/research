"""Afterlight's branching molten arteries, rebuilt so each artery's path is kept.

Same geometry as afterlight/veins.py (same control points, widths and projection).
The difference: every ribbon also returns its centre line with distances, so the
renderer can place real point lights where the travelling pulses are.
"""
import math
import numpy as np
from engine import normalize
from veins import Projector, curve

WIDEN = 1.35  # the magenta cut widens the arteries so the lava reads at hood distance

def build_veins(mesh, body):
    bed = mesh('veinBeds', True); molten = mesh('veins', True)
    top = Projector(body, 1, 1); sides = {s: Projector(body, 2, s) for s in (-1, 1)}
    ribbons = []

    def ribbon(controls, proj, width, phase=0., start=0.):
        width *= WIDEN
        pts2 = curve(controls, 48); centers = [proj(p, .006) for p in pts2]
        dist = start; path = []
        for j in range(len(pts2) - 1):
            a, b = centers[j], centers[j + 1]
            if a is None or b is None: continue
            d = np.linalg.norm(b - a); tangent = normalize(pts2[j + 1] - pts2[j]); cross = np.array([-tangent[1], tangent[0]])
            taper = .65 + .35 * math.sin(math.pi * (j + .5) / (len(pts2) - 1))
            path.append((dist, a))
            for target, w, offset, emit in [(bed, width * 1.75, .005, 0), (molten, width, .010, 2.6)]:
                q = [pts2[j] - cross * w * taper, pts2[j] + cross * w * taper, pts2[j + 1] + cross * w * taper, pts2[j + 1] - cross * w * taper]
                p = [proj(x, offset) for x in q]
                if any(x is None for x in p): continue
                uv = [(dist, -1), (dist, 1), (dist + d, 1), (dist + d, -1)] if target is molten else None
                if np.cross(p[1] - p[0], p[2] - p[0])[proj.axis] * proj.sign < 0:
                    p = p[::-1]
                    if uv is not None: uv = uv[::-1]
                st = len(target.data); target.face(p, '#080b13' if target is bed else '#ff952f', em=emit, uvs=uv)
                if target is molten:
                    for row in target.data[st:]: row[9] = phase
            dist += d
        if path:
            off = np.zeros(3); off[proj.axis] = .05 * proj.sign
            ribbons.append(dict(phase=phase, d=np.array([p[0] for p in path]), p=np.array([p[1] for p in path]) + off))

    for side in (-1, 1):
        z = lambda v: side * v
        ribbon([(.73, z(.20)), (1.11, z(.27)), (1.54, z(.45)), (2.17, z(.64))], top, .019, 0.)
        for points, w, offset in [
            ([(1.00, z(.29)), (1.13, z(.49)), (1.28, z(.79)), (1.49, z(.98))], .013, .30),
            ([(1.32, z(.41)), (1.43, z(.28)), (1.71, z(.20)), (1.95, z(.20))], .010, .66),
            ([(1.63, z(.52)), (1.70, z(.68)), (1.86, z(.77)), (2.05, z(.78))], .011, .99),
            ([(.86, z(.68)), (1.12, z(.79)), (1.32, z(.99)), (1.46, z(1.01))], .014, .28)]:
            ribbon(points, top, w, 0., offset)
        proj = sides[side]
        ribbon([(-.95, .785), (-.60, .805), (.10, .80), (.78, .73)], proj, .013, .07, 0.)
        ribbon([(-.78, .79), (-.92, .71), (-1.02, .55), (-.87, .45)], proj, .009, .07, .22)
        ribbon([(.40, .78), (.70, .82), (.90, .67), (.94, .48)], proj, .010, .07, 1.10)
        ribbon([(-1.25, z(.43)), (-1.44, z(.59)), (-1.86, z(.55)), (-2.22, z(.57))], top, .016, .12, 0.)
    flames = mesh('blaze'); anchors = []
    for x, zz in [(1.05, .34), (1.42, -.46), (1.27, .94), (-1.68, -.54)]:
        p = top((x, zz), .018)
        if p is not None: anchors.append(p)
    for k, p in enumerate(anchors):
        for layer in (0., 1.):
            for j in range(18):
                a = j / 18.; b = (j + 1) / 18.
                for i in range(10):
                    q = i * math.pi * 2 / 10; qq = (i + 1) * math.pi * 2 / 10
                    for u, t in [(a, q), (b, q), (b, qq), (a, q), (b, qq), (a, qq)]:
                        flames.data.append([*p, u, t, layer, 1, 1, 1, float(k), u, t / (2 * math.pi)])
    return ribbons
