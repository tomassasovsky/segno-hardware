"""Render the grommet alone, cut away in the beam, and installed with its cable."""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
import cadquery as cq

import beam_grommet as g

enclosure = g.enclosure
BG = "#f4f3ef"
TPU = "#2b2f36"
STEEL = "#9aa4ae"
CABLE = "#141414"


def project(objects, elev, azim, tol=0.05):
    """Painter's-algorithm polygons for (solid, colour) pairs."""
    e, a = math.radians(elev), math.radians(azim)
    view = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    right = np.cross([0, 0, 1], view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    # Light from over the viewer's left shoulder, whatever the view.
    lv = view + 0.8 * up - 0.4 * right
    lv /= np.linalg.norm(lv)
    polys, colors, depth = [], [], []
    for solid, color in objects:
        verts, tris = solid.tessellate(tol, 0.2)
        v = np.array([p.toTuple() for p in verts])
        t = v[np.array(tris)]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        front = n @ view > 0
        base = np.array(matplotlib.colors.to_rgb(color))
        shade = 0.45 + 0.55 * np.clip(n @ lv, 0, 1)
        for tri, s in zip(t[front], shade[front]):
            polys.append(np.c_[tri @ right, tri @ up])
            colors.append(np.clip(base * s + 0.06, 0, 1))
            depth.append((tri @ view).mean())
    order = np.argsort(depth)
    return [polys[i] for i in order], [colors[i] for i in order]


def draw(ax, objects, elev, azim, title):
    polys, colors = project(objects, elev, azim)
    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors=colors, linewidths=0.2))
    pts = np.vstack(polys)
    pad = 0.06 * (pts.max(0) - pts.min(0)).max()
    ax.set_xlim(pts[:, 0].min() - pad, pts[:, 0].max() + pad)
    ax.set_ylim(pts[:, 1].min() - pad, pts[:, 1].max() + pad)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12, weight="bold", color="#20252c")


def cable(offset):
    """4 mm cable: in from the pedal side, through the hole, down to the floor."""
    x, y0, zc = offset
    r = 12.0
    path = (cq.Workplane("YZ", origin=(x, 0, 0)).moveTo(y0 - 14, zc).lineTo(y0 + 2, zc)
            .radiusArc((y0 + 2 + r, zc - r), r).lineTo(y0 + 2 + r, 6.0))
    return (cq.Workplane(cq.Plane((x, y0 - 14, zc), (1, 0, 0), (0, 1, 0)))
            .circle(g.CABLE_OD / 2).sweep(path, transition="round").val())


def render(path):
    part = g.build()
    u, offset = g.placements()[2]
    beam = enclosure._beam_solid()
    x = offset[0]
    coupon = beam.intersect(cq.Workplane("XY").box(60, 60, 60).translate((x, 20, 25)).val())
    placed = g.to_beam(part, offset)
    wire = cable(offset)
    half = cq.Workplane("XY").box(60, 80, 80).translate((x + 0.6 + 30, 20, 25)).val()

    fig = plt.figure(figsize=(16, 7.4), facecolor=BG)
    fig.text(0.035, 0.93, "Beam cable grommet, TPU 95A", fontsize=22, weight="bold", color="#20252c")
    fig.text(0.035, 0.885,
             f"One per window, one cable each, {g.CABLE_MIN:.0f} to {g.CABLE_MAX:.0f} mm. Flange on the web's rear face, "
             "barbed lips snap over its front face. Eight slit flaps grip the cable and fold back for the plug.",
             fontsize=12, color="#525b65")
    ax = fig.add_axes((0.01, 0.08, 0.30, 0.74), facecolor=BG)
    draw(ax, [(part, "#5d646f")], -50, -60, "From the bed side: the membrane, printed first")
    ax = fig.add_axes((0.33, 0.08, 0.33, 0.74), facecolor=BG)
    draw(ax, [(coupon.cut(half), STEEL), (placed.cut(half), TPU), (wire.cut(half), CABLE)],
         12, 0, "Cut through the centre: rear (right) to front")
    ax = fig.add_axes((0.67, 0.08, 0.32, 0.74), facecolor=BG)
    draw(ax, [(coupon, STEEL), (placed, TPU), (wire, CABLE)], 22, 55,
         f"In the beam at u {u:.0f}, seen from the rear")
    d = g.derived()
    fig.text(0.035, 0.035,
             f"Window {g.WIN_W:.0f} x {g.WIN_H:.0f} R{g.WIN_R:.0f} in {g.WEB_T} steel  ·  body "
             f"{d['body_w']} x {d['body_h']} ({g.FIT_CLR} a side)  ·  flange {d['flange_w']:.0f} x "
             f"{d['flange_h']:.0f} x {g.FLANGE_T}  ·  {g.MEMBRANE_T} membrane, {g.SLIT_RAYS} slits  ·  barb {g.BARB} at "
             f"{g.RETAIN_DEG:.0f} deg  ·  {part.Volume() / 1000:.2f} cm3",
             fontsize=10.5, color="#525b65")
    fig.savefig(path, dpi=110, facecolor=BG)


if __name__ == "__main__":
    g.OUT.mkdir(exist_ok=True)
    render(g.OUT / "beam_grommet_preview.png")
    print(f"wrote {g.OUT / 'beam_grommet_preview.png'}")
