#!/usr/bin/env python
"""Printed layout base for the ten pedal platforms (issue #1544).

The platforms (collars, sleds and pedals) can be printed and assembled long
before the sheet-metal base exists. This base stands in for the metal: it
bolts to each collar's four underside chassis-screw holes at exactly the
positions platform_foot_holes() cuts in the 2 mm base, so the pedals sit at
the console's pitch and row spacing and can be played on the floor.

The platform screws are the only fasteners. Nothing joins two base parts
except a platform:

  BRIDGE       x6. Under each gap between two front pedals: the two inner
               holes of the pedal on its left and the two of the pedal on its
               right. Pedal, sled and the next bridge carry the row on.
  CENTRE       x2, one part. The UNDO/MODE bridge and the CLEAR/BANK bridge
               (turned 180 degrees). Each has a pocket under one end for...
  LINK         x1. A flat plate in both pockets that ties the rows together.
               The four screws at UNDO's and MODE's rear inner holes and
               CLEAR's and BANK's front inner holes pass through it, and the
               pocket walls stop it racking. A single piece from the front
               holes to the CLEAR/BANK holes would be ~273 mm, past the bed.
  END PAD      x4, one part. The outer hole pair of REC/PLAY, TRACK4, CLEAR
               and BANK, so the end platforms stand level.

Print every part upside down (the face the collar sits on, on the bed): the
counterbores and the link pocket then open upward and nothing bridges. The
STLs are exported that way round; the STEPs are in the assembled orientation.

Screws are driven up from underneath, heads flush in counterbores so the base
stands on its own face. The lengths are the console's own nominal ones:

  front collars  M3 x 12, through the base and the collar's printed floor
                 into the sled's lower inserts.
  CLEAR/BANK     M3 x 10 into the collar's own bottom inserts. Their sleds
                 stay on their four deck screws, exactly as in the console.

    python _platform_layout_base.py           # STEP + STL -> out/, assembly check
    python _platform_layout_base.py --png     # ...and two renders in out/
    python _print_check.py out/segno_layout_base_bridge.stl
"""

from __future__ import annotations

import math
import os

import cadquery as cq

import segno_enclosure as E
from segno_enclosure import (
    CONSOLE_BAFFLE_T,
    CONSOLE_PLATFORM_D,
    CONSOLE_SLED_T,
    INSERT_DEPTH,
    OUT,
    PEDAL_ROW1_V,
    PEDAL_ROW2_V,
    PEDALS,
    SKIRT_OUT_W,
    SLOPE_ANGLE,
    platform_foot_holes,
    platform_foot_xy,
    platform_h,
)

# --- layout, all from the enclosure source ------------------------------------
_CS = math.cos(math.radians(SLOPE_ANGLE))
PITCH = E._row1_u(1) - E._row1_u(0)                       # 101.143
ROW1_Y = PEDAL_ROW1_V * _CS                               # plan depth of the front row
ROW2_Y = PEDAL_ROW2_V * _CS                               # ...and of CLEAR/BANK
ROW_DY = ROW2_Y - ROW1_Y
# platform_foot_xy() gives x = depth, y = across; the pattern is symmetric.
HOLE_V = max(abs(x) for x, _ in platform_foot_xy())       # 48.685
HOLE_U = max(abs(y) for _, y in platform_foot_xy())       # 22.1875
FRONT = list(range(8))                                    # indices into PEDALS
CENTRE_GAP = 2                                            # UNDO -> MODE carries the link
CLEAR, BANK = 8, 9

# --- base parameters ------------------------------------------------------------
PLATE_T   = 8.0    # bridges and pads
CBORE_D   = 6.5    # M3 socket head Ø5.5
CBORE_H   = 3.0    # the head's own height: flush with the floor face
HOLE_D    = 3.3    # M3 clearance, kept close: the hole fit IS the pitch tolerance.
                   # Not 3.2 -- a screw that threads into the base cannot draw
                   # the collar down onto it
EDGE_MARGIN = 3.0  # base edge past the collar's footprint
HALF_D = CONSOLE_PLATFORM_D / 2.0 + EDGE_MARGIN           # 62.235
BRIDGE_IN = 10.0   # bridge and pad inner edge, from the pedal centre
BRIDGE_HW = PITCH / 2.0 - BRIDGE_IN                       # 40.571
BRIDGE_HOLE_U = PITCH / 2.0 - HOLE_U                      # 28.384, from the bridge centre
PAD_OUT = SKIRT_OUT_W / 2.0 + EDGE_MARGIN                 # 47.375, pad outer edge
CORNER_BREAK = 1.0
BED_CHAM = 0.6     # on the bed face, which is the top: elephant foot

# Windows between each bridge's two hole columns, under the collars' outer
# bands and the gap between them. The centre bridge's stops short of its pocket.
WIN_HU = 20.0
WIN_V  = (-38.0, 38.0)
WIN_V_CENTRE = (-38.0, 32.0)
WIN_R  = 6.0

# --- link ---------------------------------------------------------------------------
LINK_T   = 4.0
LINK_HW  = BRIDGE_HOLE_U + 7.5                             # 35.884
LINK_END = 8.0                                             # past the end holes
LINK_V0  = HOLE_V - LINK_END                               # link frame: front row centre
LINK_V1  = ROW_DY - HOLE_V + LINK_END
POCKET_CLR = 0.15                                          # walls locate the link
POCKET_D   = LINK_T + 0.1   # the link, not the bridge, takes any thickness error

# Screws, from underneath. Both lengths stop the tip short of the blind
# 6 mm pilots the inserts sit in.
FRONT_SCREW_L = 12.0
MID_SCREW_L   = 10.0

BED = 215.0   # Ender 3 V3, 220 x 220, less a margin (RAIL_MAXLEN)


def _rrect(cx, hu, v0, v1, r):
    return (cq.Workplane("XY").rect(2 * hu, v1 - v0).extrude(PLATE_T + 2.0)
            .edges("|Z").fillet(r).translate((cx, (v0 + v1) / 2.0, -1.0)))


def _screw_hole(body, x, y):
    return (body.cut(cq.Workplane("XY").circle(HOLE_D / 2.0)
                     .extrude(PLATE_T + 2.0).translate((x, y, -1.0)))
            .cut(cq.Workplane("XY").circle(CBORE_D / 2.0)
                 .extrude(CBORE_H + 1.0).translate((x, y, -1.0))))


def _plate(u0, u1, v0, v1, t):
    return (cq.Workplane("XY").box(u1 - u0, v1 - v0, t, centered=False)
            .translate((u0, v0, 0))
            .edges("|Z").chamfer(CORNER_BREAK)
            .faces(">Z").chamfer(BED_CHAM))


def bridge_holes():
    """Bridge frame: origin midway between the two pedals, X across, Y depth."""
    return [(su * BRIDGE_HOLE_U, sv * HOLE_V) for su in (-1, 1) for sv in (-1, 1)]


def build_bridge(centre=False):
    """A gap bridge. centre=True adds the link pocket under its +Y end."""
    body = _plate(-BRIDGE_HW, BRIDGE_HW, -HALF_D, HALF_D, PLATE_T)
    v0, v1 = WIN_V_CENTRE if centre else WIN_V
    body = body.cut(_rrect(0, WIN_HU, v0, v1, WIN_R))
    for x, y in bridge_holes():
        body = _screw_hole(body, x, y)
    if centre:
        body = body.cut(cq.Workplane("XY")
                        .box(2 * (LINK_HW + POCKET_CLR), HALF_D - LINK_V0 + POCKET_CLR + 1.0,
                             POCKET_D, centered=(True, False, False))
                        .translate((0, LINK_V0 - POCKET_CLR, 0)))
    return body


def pad_holes():
    """End-pad frame: origin at the pedal centre; the pad is on its -X side."""
    return [(-HOLE_U, sv * HOLE_V) for sv in (-1, 1)]


def build_pad():
    body = _plate(-PAD_OUT, -BRIDGE_IN, -HALF_D, HALF_D, PLATE_T)
    for x, y in pad_holes():
        body = _screw_hole(body, x, y)
    return body


def link_holes():
    """Link frame: origin at the UNDO/MODE bridge centre, Y rearward."""
    return [(su * BRIDGE_HOLE_U, v) for su in (-1, 1) for v in (HOLE_V, ROW_DY - HOLE_V)]


def build_link():
    body = _plate(-LINK_HW, LINK_HW, LINK_V0, LINK_V1, LINK_T)
    for x, y in link_holes():
        body = _screw_hole(body, x, y)
    return body


def _placed():
    """Every base part in world (u, plan v): (kind, workplane, world holes,
    head-seat height above the floor at those holes)."""
    out = []

    def put(kind, body, holes, cu, cv, flip, seat):
        if flip:
            body = body.rotate((0, 0, 0), (0, 0, 1), 180)
            holes = [(-x, -y) for x, y in holes]
        out.append((kind, body.translate((cu, cv, 0)),
                    [(cu + x, cv + y) for x, y in holes], seat))

    for i in FRONT[:-1]:
        cu = (PEDALS[i][1] + PEDALS[i + 1][1]) / 2.0
        centre = i == CENTRE_GAP
        put("centre" if centre else "bridge", build_bridge(centre), bridge_holes(),
            cu, ROW1_Y, False, CBORE_H)
    cu = (PEDALS[CLEAR][1] + PEDALS[BANK][1]) / 2.0
    put("centre", build_bridge(True), bridge_holes(), cu, ROW2_Y, True, CBORE_H)
    # a clamped link is drawn up against the pocket roof, off the floor
    put("link", build_link().translate((0, 0, POCKET_D - LINK_T)), link_holes(),
        cu, ROW1_Y, False, POCKET_D - LINK_T + CBORE_H)
    for idx, flip in ((0, False), (7, True), (CLEAR, False), (BANK, True)):
        _, u, v = PEDALS[idx]
        put("pad", build_pad(), pad_holes(), u, v * _CS, flip, CBORE_H)
    return out


def _ring(v):
    """The console collar exactly as build_platform_steps() exports it,
    turned into this frame (its local +X = rearward = +Y here)."""
    r = E._platform_printed(cq, platform_h(v), v, baffle_t=CONSOLE_BAFFLE_T,
                            sled=CONSOLE_SLED_T)
    return r.rotate((0, 0, 0), (0, 0, 1), 90)


def _vol(shape):
    return sum(s.Volume() for s in shape.Solids())


def _floor_at_centre(ring):
    """Collar floor thickness, measured on the real solid at the pedal centre."""
    probe = cq.Workplane("XY").box(0.5, 0.5, 200.0, centered=(True, True, False))
    return ring.val().intersect(probe.val()).BoundingBox().zmax


def _find(p, pts):
    return next((q for q in pts if math.dist(p, q) < 1e-9), None)


def _check(parts):
    """The base is worth printing only if the collars bolt on where the metal
    would put them, the screws reach, no two parts collide and each fits the bed."""
    # 1. Holes: bridges and pads take every metal-base hole exactly once; the
    #    link's four holes are four of those.
    metal = [(h["u"], h["v"]) for h in platform_foot_holes()]
    own = [h for kind, _, holes, _ in parts if kind != "link" for h in holes]
    assert len(own) == len(metal) == 40, f"HOLES: {len(own)} base holes for 40 screws"
    for h in metal:
        assert _find(h, own), f"HOLES: metal hole at {h} has no base hole"
    link = next(p for p in parts if p[0] == "link")
    for h in link[2]:
        assert _find(h, own), f"LINK: hole at {h} is not on a platform screw"
    # 2. No two parts occupy the same space, so the link sits in its pockets.
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            v = _vol(a[1].val().intersect(b[1].val()))
            assert v < 1e-6, f"OVERLAP: {a[0]} and {b[0]} share {v:.2f} mm3"
    # 3. Bed.
    for kind, body in (("bridge", build_bridge()), ("centre", build_bridge(True)),
                       ("pad", build_pad()), ("link", build_link())):
        bb = body.val().BoundingBox()
        assert max(bb.xlen, bb.ylen) <= BED, f"BED: {kind} {bb.xlen:.1f} x {bb.ylen:.1f}"
    # 4. Screws, against the real collar geometry: clear of the collar, and
    #    engaged short of the insert pilot's floor. Where the link is under a
    #    bridge, the screw head seats in the link.
    seats = {h: s for kind, _, holes, s in parts if kind != "link" for h in holes}
    for h in link[2]:
        seats[_find(h, seats)] = link[3]
    engage = {}
    for row_v, screw_l, label in ((PEDAL_ROW1_V, FRONT_SCREW_L, "front"),
                                  (PEDAL_ROW2_V, MID_SCREW_L, "mid")):
        ring = _ring(row_v)
        floor = _floor_at_centre(ring) if label == "front" else 0.0
        for _, u, v in [p for p in PEDALS if p[2] == row_v]:
            for fx, fy in platform_foot_xy():
                h = (u + fy, v * _CS + fx)
                tip = seats[_find(h, seats)] + screw_l - PLATE_T   # above the base top
                rod = cq.Workplane("XY").circle(1.45).extrude(tip).translate((fy, fx, 0))
                clash = _vol(ring.val().intersect(rod.val()))
                assert clash < 1e-6, f"SCREW: {label} screw at {h} hits the collar"
                e = tip - floor
                assert 3.5 <= e <= INSERT_DEPTH - 0.5, \
                    f"SCREW: {label} M3x{screw_l:.0f} at {h} engages {e:.2f} mm"
                engage.setdefault(label, []).append(e)
    return engage


def _assembly(parts):
    rings = {PEDAL_ROW1_V: _ring(PEDAL_ROW1_V), PEDAL_ROW2_V: _ring(PEDAL_ROW2_V)}
    out = [(kind, wp) for kind, wp, _, _ in parts]
    for _, u, v in PEDALS:
        out.append(("ring", rings[v].translate((u, v * _CS, PLATE_T))))
    return out


def render_png(parts, path, top=False):
    """Shaded VTK view of the assembled base, same idiom as render_png()."""
    import vtk
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.95, 0.95)
    colour = {"bridge": (0.85, 0.55, 0.15), "centre": (0.85, 0.35, 0.10),
              "pad": (0.65, 0.65, 0.20), "link": (0.15, 0.45, 0.85),
              "ring": (0.18, 0.18, 0.20)}
    for kind, wp in parts:
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(wp.val().toVtkPolyData(0.3, 0.2))
        a = vtk.vtkActor()
        a.SetMapper(m)
        a.GetProperty().SetColor(*colour[kind])
        ren.AddActor(a)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(1700, 1000)
    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(423.0, 160.0, 0.0)
    if top:
        cam.SetPosition(423.0, 160.0, 900.0)
        cam.SetViewUp(0, 1, 0)
    else:
        cam.SetPosition(423.0 - 250.0, 160.0 - 900.0, 650.0)
        cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.35)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(path)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()


def main(render=False):
    parts = _placed()
    engage = _check(parts)
    os.makedirs(OUT, exist_ok=True)
    singles = (("bridge", build_bridge(), 6), ("centre", build_bridge(True), 2),
               ("link", build_link(), 1), ("pad", build_pad(), 4))
    for name, body, _ in singles:
        base = os.path.join(OUT, f"segno_layout_base_{name}")
        cq.exporters.export(body.val(), base + ".step")
        # print orientation: the face the collar sits on goes on the bed
        flipped = body.rotate((0, 0, 0), (1, 0, 0), 180)
        flipped = flipped.translate((0, 0, -flipped.val().BoundingBox().zmin))
        cq.exporters.export(flipped, base + ".stl", tolerance=0.05)
    asm_parts = _assembly(parts)
    asm = cq.Assembly()
    for i, (kind, wp) in enumerate(asm_parts):
        asm.add(wp, name=f"{kind}_{i}")
    asm.export(os.path.join(OUT, "segno_layout_base_assembly.step"))
    if render:
        render_png(asm_parts, os.path.join(OUT, "_layout_base.png"))
        render_png([p for p in asm_parts if p[0] != "ring"],
                   os.path.join(OUT, "_layout_base_top.png"), top=True)

    print("Pedal platform layout base (issue #1544)")
    for name, body, qty in singles:
        bb = body.val().BoundingBox()
        print(f"  {name:<7} x{qty}   {bb.xlen:6.2f} x {bb.ylen:6.2f} x {bb.zlen:.1f} mm")
    print(f"  pitch {PITCH:.3f}, rows {ROW_DY:.3f} apart in plan")
    print(f"  screws: 32 x M3x{FRONT_SCREW_L:.0f} front "
          f"({min(engage['front']):.2f}-{max(engage['front']):.2f} mm into the sled), "
          f"8 x M3x{MID_SCREW_L:.0f} CLEAR/BANK "
          f"({min(engage['mid']):.2f}-{max(engage['mid']):.2f} mm into the collar)")
    for name, _, _ in singles:
        print(f"  out/segno_layout_base_{name}.step (+ .stl, print orientation)")
    print("  out/segno_layout_base_assembly.step")


if __name__ == "__main__":
    import sys
    main(render="--png" in sys.argv)
