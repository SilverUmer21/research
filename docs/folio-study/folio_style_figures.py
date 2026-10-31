"""Figures for FOLIO-2025-STUDY.md.

Re-implements the shading model of Bruno Simon's folio-2025 (MIT) in numpy so
the style notes can show what each term does. Constants are copied from
sources/Game/Materials/MeshDefaultMaterial.js, Ligthing.js, Fog.js,
Cycles/DayCycles.js, View.js and static/palette.png at commit main (2026-04-07).

The scene is a tiny ray-traced stand-in (ground, a lavender rock sphere, a
red-orange crate) seen from the folio camera angle. No bloom, grass or
tilt-shift: this isolates the colour/lighting maths.

Usage: python tools/style/folio_style_figures.py [output_dir]
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent

# static/palette.png: 128x4, 24 swatches 4 px wide, nearest filtering.
PALETTE = [
    "#7c7691", "#ebd1a3", "#574e37", "#3dbbe7", "#c8c2c1", "#4a413c",
    "#575a5e", "#eec3af", "#e4a90c", "#91ad78", "#e49a78", "#988165",
    "#abae2b", "#a49876", "#b36d45", "#e56202", "#ec3f1c", "#fde6e1",
    "#f8a658", "#c30e3a", "#c366ef", "#ed719f", "#1e0603", "#fff2e8",
]

# DayCycles.js presets. progress is the cycle stop where each preset is pure.
PRESETS = {
    "day":   dict(progress=0.07, light="#ffd2c2", intensity=1.2, shadow="#6d3fff", fogA="#00ffff", fogB="#9b89ff", near=0.315, far=1.25),
    "dusk":  dict(progress=0.25, light="#ff8181", intensity=1.2, shadow="#4e009c", fogA="#3e53ff", fogB="#ff4ce4", near=0.0, far=1.25),
    "night": dict(progress=0.47, light="#3240ff", intensity=3.8, shadow="#2f00db", fogA="#10266f", fogB="#490a42", near=-0.85, far=1.0),
    "dawn":  dict(progress=0.80, light="#ffa882", intensity=1.2, shadow="#db004f", fogA="#f885ff", fogB="#ff7d24", near=0.3, far=1.25),
}

GROUND = "#e8b07d"   # floor slabs: mix(#a87762, #ffcf8b, ~0.75)
ROCK = PALETTE[0]
CRATE = PALETTE[16]

W, H = 480, 300
FOV = np.radians(25.0)
CAM_PHI, CAM_THETA, CAM_RADIUS = np.pi * 0.31, np.pi * 0.25, 13.0  # folio zooms 15-30; closer here so the props read


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def hexlin(h):
    h = h.lstrip("#")
    return srgb_to_linear([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def spherical(r, phi, theta):
    # three.js Vector3.setFromSphericalCoords
    return np.array([r * np.sin(phi) * np.sin(theta), r * np.cos(phi), r * np.sin(phi) * np.cos(theta)])


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def light_direction(progress):
    # Ligthing.js update(): sun orbits with the day cycle.
    a = -(progress + 9 / 16) * np.pi * 2
    theta = 0.72 + np.sin(a) * 1.25
    phi = 0.63 + np.cos(a) * 0.5 * 0.62
    d = spherical(1, phi, theta)
    return d / np.linalg.norm(d)


def camera_rays():
    eye = spherical(CAM_RADIUS, CAM_PHI, CAM_THETA)
    fwd = -eye / np.linalg.norm(eye)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    th = np.tan(FOV / 2)
    xs = (np.arange(W) + 0.5) / W * 2 - 1
    ys = 1 - (np.arange(H) + 0.5) / H * 2
    gx, gy = np.meshgrid(xs * th * W / H, ys * th)
    d = fwd + gx[..., None] * right + gy[..., None] * up
    return eye, d / np.linalg.norm(d, axis=-1, keepdims=True)


def fog_distances(eye_dir_len=CAM_RADIUS * 1.4):
    # View.js optimalArea: distances to the floor at the bottom/top screen edge,
    # measured from the zoomed-out camera (radius 30 * (1 - -0.4)).
    eye = spherical(eye_dir_len, CAM_PHI, CAM_THETA) * (30 * 1.4 / eye_dir_len)
    fwd = -eye / np.linalg.norm(eye)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    out = []
    for sy in (-1, 1):
        d = fwd + up * np.tan(FOV / 2) * sy
        t = -eye[1] / d[1]
        out.append(np.linalg.norm(d * t))
    return out


SPHERE_C, SPHERE_R = np.array([-1.2, 1.1, 1.4]), 1.1
BOX_MIN, BOX_MAX = np.array([0.6, 0.0, -2.2]), np.array([2.4, 1.6, -0.4])


def hit_sphere(o, d):
    oc = o - SPHERE_C
    b = np.sum(oc * d, -1)
    c = np.sum(oc * oc, -1) - SPHERE_R ** 2
    disc = b * b - c
    t = -b - np.sqrt(np.maximum(disc, 0))
    return np.where((disc > 0) & (t > 1e-4), t, np.inf)


def hit_box(o, d):
    with np.errstate(divide="ignore", invalid="ignore"):
        inv = 1.0 / d
        t0 = (BOX_MIN - o) * inv
        t1 = (BOX_MAX - o) * inv
    tmin = np.max(np.minimum(t0, t1), -1)
    tmax = np.min(np.maximum(t0, t1), -1)
    return np.where((tmax >= tmin) & (tmax > 1e-4), np.where(tmin > 1e-4, tmin, np.inf), np.inf)


def hit_ground(o, d):
    with np.errstate(divide="ignore", invalid="ignore"):
        t = -o[..., 1] / d[..., 1]
    return np.where(t > 1e-4, t, np.inf)


def box_normal(p):
    c = (BOX_MIN + BOX_MAX) / 2
    h = (BOX_MAX - BOX_MIN) / 2
    q = (p - c) / h
    axis = np.argmax(np.abs(q), -1)
    n = np.zeros_like(p)
    np.put_along_axis(n, axis[..., None], np.take_along_axis(np.sign(q), axis[..., None], -1), -1)
    return n


def render(preset, terms=None):
    """terms: optional dict collecting intermediate images for the breakdown."""
    eye, d = camera_rays()
    o = np.broadcast_to(eye, d.shape)
    ts = np.stack([hit_ground(o, d), hit_sphere(o, d), hit_box(o, d)])
    obj = np.argmin(ts, 0)
    t = np.min(ts, 0)
    hit = np.isfinite(t)
    p = o + d * np.where(hit, t, 0)[..., None]

    n = np.zeros_like(p)
    n[obj == 0] = [0, 1, 0]
    sn = (p - SPHERE_C) / SPHERE_R
    n[obj == 1] = sn[obj == 1]
    bn = box_normal(p)
    n[obj == 2] = bn[obj == 2]

    base = np.zeros_like(p)
    base[obj == 0] = hexlin(GROUND)
    base[obj == 1] = hexlin(ROCK)
    base[obj == 2] = hexlin(CRATE)
    if terms is not None:
        terms["1 base palette"] = base.copy()

    # Light bounce: downward-facing surfaces near the floor pick up its colour.
    color = base.copy()
    bounce_orient = smoothstep(-1, 1, -n[..., 1])
    bounce_dist = np.maximum((1.5 - np.maximum(0, p[..., 1])) / 1.5, 0) ** 2
    bounce = (bounce_orient * bounce_dist * (obj != 0))[..., None]
    color = color * (1 - bounce) + hexlin(GROUND) * bounce
    shadow_base = base  # the folio tints shadows from the pre-bounce colour
    if terms is not None:
        terms["2 + floor bounce"] = color.copy()

    L = light_direction(preset["progress"])
    lit = color * hexlin(preset["light"]) * preset["intensity"]
    if terms is not None:
        terms["3 x light colour"] = lit.copy()

    ndl = np.sum(n * L, -1)
    core = smoothstep(1.0, -0.25, ndl) * (obj != 0)

    # Cast shadows: average a few jittered shadow rays (stands in for PCF radius).
    rng = np.random.default_rng(3)
    drop = np.zeros(t.shape)
    samples = 6
    for _ in range(samples):
        Lj = L + rng.normal(0, 0.03, 3); Lj /= np.linalg.norm(Lj)
        so = p + n * 2e-3
        sd = np.broadcast_to(Lj, p.shape)
        blocked = np.isfinite(np.minimum(hit_sphere(so, sd), hit_box(so, sd)))
        drop += blocked
    drop = drop / samples * hit
    mix_amt = np.clip(np.maximum(core, drop), 0, 1)[..., None]
    shade = shadow_base * hexlin(preset["shadow"])
    out = lit * (1 - mix_amt) + shade * mix_amt
    if terms is not None:
        terms["4 shadow mask"] = np.repeat(mix_amt, 3, -1)
        terms["5 tinted shadow"] = out.copy()

    # Fog: range fog toward a diagonal screen-space gradient (also the sky).
    near_d, far_d = fog_distances()
    amp = far_d - near_d
    fnear = near_d + preset["near"] * amp
    ffar = near_d + preset["far"] * amp
    ys, xs = np.mgrid[0:H, 0:W]
    radial = np.sqrt((xs / W) ** 2 + (ys / H) ** 2)
    g = smoothstep(0, 1, radial)[..., None]
    fog_col = hexlin(preset["fogA"]) * (1 - g) + hexlin(preset["fogB"]) * g
    dist = np.where(hit, t, 1e9)
    f = smoothstep(fnear, ffar, dist)[..., None]
    out = out * (1 - f) + fog_col * f
    out = np.where(hit[..., None], out, fog_col)
    if terms is not None:
        terms["6 + fog / sky"] = out.copy()
    return out


def to_img(lin):
    return Image.fromarray((linear_to_srgb(lin) * 255 + 0.5).astype(np.uint8))


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(img, text, xy=(10, 8), size=18):
    dr = ImageDraw.Draw(img)
    x, y = xy
    dr.text((x + 1, y + 1), text, fill=(0, 0, 0), font=font(size))
    dr.text((x, y), text, fill=(255, 255, 255), font=font(size))


def text_on(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return (0, 0, 0) if 0.299 * r + 0.587 * g + 0.114 * b > 140 else (255, 255, 255)


def presets_figure():
    tiles = []
    for name, pr in PRESETS.items():
        img = to_img(render(pr))
        label(img, name)
        strip = Image.new("RGB", (W, 34), "white")
        dr = ImageDraw.Draw(strip)
        keys = [("light", pr["light"]), ("shadow", pr["shadow"]), ("fog A", pr["fogA"]), ("fog B", pr["fogB"])]
        for i, (k, v) in enumerate(keys):
            x0 = i * W // 4
            dr.rectangle([x0, 0, x0 + W // 4, 34], fill=v)
            dr.text((x0 + 6, 9), f"{k} {v}", fill=text_on(v), font=font(13))
        tile = Image.new("RGB", (W, H + 34))
        tile.paste(img, (0, 0)); tile.paste(strip, (0, H))
        tiles.append(tile)
    sheet = Image.new("RGB", (W * 2 + 6, (H + 34) * 2 + 6), "white")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % 2) * (W + 6), (i // 2) * (H + 34 + 6)))
    sheet.save(OUT / "folio-day-presets.png")


def breakdown_figure():
    terms = {}
    render(PRESETS["dusk"], terms)
    tw, th = W // 2, H // 2
    sheet = Image.new("RGB", (tw * 3 + 8, th * 2 + 4), "white")
    for i, (k, v) in enumerate(terms.items()):
        img = to_img(v).resize((tw, th), Image.LANCZOS) if "mask" not in k else Image.fromarray((np.clip(v, 0, 1) * 255).astype(np.uint8)).resize((tw, th))
        label(img, k, size=14)
        sheet.paste(img, ((i % 3) * (tw + 4), (i // 3) * (th + 4)))
    sheet.save(OUT / "folio-shading-breakdown.png")


def palette_figure():
    sw, sh = 110, 64
    cols = 8
    img = Image.new("RGB", (sw * cols, sh * 3), "white")
    dr = ImageDraw.Draw(img)
    for i, c in enumerate(PALETTE):
        x, y = (i % cols) * sw, (i // cols) * sh
        dr.rectangle([x, y, x + sw, y + sh], fill=c)
        dr.text((x + 6, y + 6), f"{i:02d}", fill=text_on(c), font=font(12))
        dr.text((x + 6, y + 40), c, fill=text_on(c), font=font(14))
    img.save(OUT / "folio-palette.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    palette_figure()
    presets_figure()
    breakdown_figure()
    print("wrote", OUT)
