#!/usr/bin/env python
"""Printed layout base for the ten pedal platforms (issue #1544).

The platforms (rings, sleds and pedals) can be printed and assembled long
before the sheet-metal base exists. This base stands in for the metal: it
bolts to each platform's four underside chassis-screw holes at exactly the
positions platform_foot_holes() cuts in the 2 mm base, so the pedals sit at
the console's pitch and row spacing and can be played on the floor.

  FRONT PIECE  x4, identical. Two front-row pedals each (REC/PLAY+STOP,
               UNDO+MODE, TRACK1+2, TRACK3+4). Its width is exactly two
               pedal pitches, so the pieces butt at the mid-gap between
               pedals and the butt faces set the pitch.
  MID PIECE    x1. CLEAR and BANK, reaching forward to butt against the
               UNDO+MODE piece's rear edge, so the row spacing is also set by
               a butt face.
  KEY          x12. Dog-bone keys pressed down into blind sockets that
               straddle each seam. The socket shoulders sit KEY_DRAW further
               from the seam than the key's head faces, so a seated key
               squeezes the butt faces together instead of letting the
               seam open by its clearance.

Every piece prints flat, top face up: the counterbores open onto the bed and
only their roofs bridge, the key sockets are blind from the top, and nothing
overhangs. The weight-saving windows sit under the sleds, where the four
screws carry the load into the frame around them.

Screws are driven up from underneath, heads sunk in counterbores so the base
stands flat on its bottom face:

  front rings  M3 x 10, through CLAMP_T of base and the ring's printed floor
               into the sled's lower inserts (the same joint as the console).
  CLEAR/BANK   M3 x 8 into the ring's own bottom inserts. Their sleds stay
               on their four deck screws, exactly as in the console.

    python _platform_layout_base.py           # STEP + STL -> out/, assembly check
    python _print_check.py out/segno_layout_base_mid.stl
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
PITCH = E._row1_u(1) - E._row1_u(0)                 # 101.143
ROW1_Y = PEDAL_ROW1_V * _CS                         # plan depth of the front row
ROW2_Y = PEDAL_ROW2_V * _CS                         # ...and of CLEAR/BANK
FRONT_PAIRS = [(0, 1), (2, 3), (4, 5), (6, 7)]      # indices into PEDALS
MID_PAIR = (8, 9)                                   # CLEAR, BANK
JOIN_PAIR = 1                                       # UNDO+MODE carries the mid piece

# --- base parameters ------------------------------------------------------------
PLATE_T   = 8.0    # the screw heads sink inside it, so it stands on its own face
CLAMP_T   = 3.0    # PETG under each screw head. More than the 2 mm metal it
                   # replaces: printed, and it bears the head directly
EDGE_MARGIN = 3.0  # base edge past the collar's front and rear faces
HOLE_D    = 3.4    # M3 clearance. The rings' own holes (Ø3.7) are the looser fit
CBORE_D   = 6.5    # M3 socket head Ø5.5
CORNER_BREAK = 1.0
BOT_CHAM  = 0.6    # elephant foot on a butt face would hold every seam open
FRONT_HALF_D = CONSOLE_PLATFORM_D / 2.0 + EDGE_MARGIN

# Windows under the sleds. Inside the ring footprint and clear of the screw
# counterbores and the key sockets; the CLEAR/BANK piece also has one per pedal
# in the span between the rows.
WIN_HALF_U = 34.0
WIN_HALF_V = 38.0
WIN_R      = 6.0
GAP_WIN_MARGIN = 8.0   # frame left round the between-rows window

# Screws, from underneath. Both lengths stop the tip short of the blind
# 6 mm pilots the inserts sit in.
FRONT_SCREW_L = 10.0
MID_SCREW_L   = 8.0
INSERT_L      = 5.0    # M3 Ø5 x 5 heat-set inserts, as everywhere on the console

# --- keys -------------------------------------------------------------------------
# Plan shape, mirrored about the seam: a neck across it, a head in each piece.
KEY_L      = 8.0    # seam to the head's outer face
KEY_HEAD_L = 4.0
KEY_NECK_W = 6.0
KEY_HEAD_W = 12.0
KEY_CLR    = 0.15   # socket clearance on the faces that only locate
KEY_DRAW   = 0.05   # head faces stand this much short of the socket shoulders,
                    # per side: pressing the key in pulls the seam shut. Set it
                    # to 0 if a test key will not go in by hand and a mallet.
KEY_END_CLR = 0.3   # beyond the head's outer face; nothing bears there
KEY_CORNER  = 0.5   # convex key corners, clear of the socket's rounded corners
KEY_LEAD    = 0.6   # bottom chamfer, so the key starts and then wedges in
SOCKET_FLOOR = 1.0  # blind socket: the key stops flush instead of falling through
KEY_H = PLATE_T - SOCKET_FLOOR - 0.2   # seats 0.2 below the top face

SIDE_KEYS_V = (-40.0, 0.0, 40.0)                  # front pieces' side seams
ROW_KEYS_U  = (-PITCH / 2.0, 0.0, PITCH / 2.0)    # row seam, piece-local u

BED = 215.0   # Ender 3 V3, 220 x 220, less a margin (RAIL_MAXLEN)


def _pair_centre(pair):
    """Piece origin in world (u, plan v): the midpoint of its two pedals."""
    (_, ua, va), (_, ub, vb) = PEDALS[pair[0]], PEDALS[pair[1]]
    assert va == vb, "a piece's pedals share a row"
    return ((ua + ub) / 2.0, va * _CS)


MID_FRONT_EDGE = (ROW1_Y + FRONT_HALF_D) - ROW2_Y   # piece-local, negative


def _key_outline():
    """Key plan outline about the seam, axis along +a, convex corners broken.
    The socket is the same shape grown by the clearances (see _socket)."""
    hn, hh = KEY_NECK_W / 2.0, KEY_HEAD_W / 2.0
    a0, a1 = KEY_L - KEY_HEAD_L, KEY_L
    c = KEY_CORNER
    return [(a1 - c, hh), (a0, hh), (a0, hn), (-a0, hn), (-a0, hh), (-a1 + c, hh),
            (-a1, hh - c), (-a1, -hh + c), (-a1 + c, -hh), (-a0, -hh), (-a0, -hn),
            (a0, -hn), (a0, -hh), (a1 - c, -hh), (a1, -hh + c), (a1, hh - c)]


def _socket(along_u):
    """Socket cutter centred on the seam at the origin, from z=SOCKET_FLOOR up.
    along_u: the key axis runs along u (a side seam) rather than along v."""
    hn, hh = KEY_NECK_W / 2.0 + KEY_CLR, KEY_HEAD_W / 2.0 + KEY_CLR
    a0 = KEY_L - KEY_HEAD_L + KEY_DRAW            # shoulder, further out: draws
    a1 = KEY_L + KEY_END_CLR
    pts = [(a1, hh), (a0, hh), (a0, hn), (-a0, hn), (-a0, hh), (-a1, hh),
           (-a1, -hh), (-a0, -hh), (-a0, -hn), (a0, -hn), (a0, -hh), (a1, -hh)]
    if not along_u:
        pts = [(c, a) for a, c in pts]
    return (cq.Workplane("XY").polyline(pts).close()
            .extrude(PLATE_T).translate((0, 0, SOCKET_FLOOR)))


def build_key():
    """One key, printed standing on its bottom (chamfered) face."""
    key = cq.Workplane("XY").polyline(_key_outline()).close().extrude(KEY_H)
    return key.faces("<Z").chamfer(KEY_LEAD)


def build_coupon():
    """Half of a one-seam test joint: half a socket at the seam face and one
    screw counterbore. Print two (turned 180 degrees they make the seam) and a
    key before the big pieces, to tune KEY_CLR / KEY_DRAW and to try a screw
    head in its counterbore."""
    hw = KEY_HEAD_W / 2.0 + 8.0
    length = KEY_L + KEY_END_CLR + 6.0 + CBORE_D
    hx = length - CBORE_D / 2.0 - 2.0
    return (cq.Workplane("XY").box(length, 2 * hw, PLATE_T, centered=(False, True, False))
            .faces("<Z").chamfer(BOT_CHAM)
            .cut(_socket(True))
            .cut(cq.Workplane("XY").circle(HOLE_D / 2.0).extrude(PLATE_T + 2.0)
                 .translate((hx, 0, -1.0)))
            .cut(cq.Workplane("XY").circle(CBORE_D / 2.0)
                 .extrude(PLATE_T - CLAMP_T + 1.0).translate((hx, 0, -1.0))))


def _rrect(cx, cy, hu, hv, r):
    return (cq.Workplane("XY").rect(2 * hu, 2 * hv).extrude(PLATE_T + 2.0)
            .edges("|Z").fillet(r).translate((cx, cy, -1.0)))


def _piece(pair, v0, v1, side_keys, row_keys):
    """One base piece in its local frame: origin at the pair centre, X across
    (world u), Y depth (world plan v, +Y rearward), Z up from the bed face."""
    cu, cv = _pair_centre(pair)
    body = (cq.Workplane("XY").box(2 * PITCH, v1 - v0, PLATE_T, centered=(True, False, False))
            .translate((0, v0, 0))
            .edges("|Z").chamfer(CORNER_BREAK)
            .faces("<Z").chamfer(BOT_CHAM))
    holes = []
    for idx in pair:
        _, u, v = PEDALS[idx]
        px, py = u - cu, v * _CS - cv
        body = body.cut(_rrect(px, py, WIN_HALF_U, WIN_HALF_V, WIN_R))
        if v0 < py - CONSOLE_PLATFORM_D / 2.0 - 2 * GAP_WIN_MARGIN:   # between rows
            g0 = v0 + GAP_WIN_MARGIN + KEY_L + KEY_END_CLR
            g1 = py - CONSOLE_PLATFORM_D / 2.0 - GAP_WIN_MARGIN
            body = body.cut(_rrect(px, (g0 + g1) / 2.0, WIN_HALF_U, (g1 - g0) / 2.0, WIN_R))
        # platform_foot_xy(): x = depth (+rearward), y = across. The pattern is
        # symmetric, so the hand of the across axis does not matter.
        for fx, fy in platform_foot_xy():
            hx, hy = px + fy, py + fx
            holes.append((cu + hx, cv + hy))
            body = (body.cut(cq.Workplane("XY").circle(HOLE_D / 2.0)
                             .extrude(PLATE_T + 2.0).translate((hx, hy, -1.0)))
                    .cut(cq.Workplane("XY").circle(CBORE_D / 2.0)
                         .extrude(PLATE_T - CLAMP_T + 1.0).translate((hx, hy, -1.0))))
    sockets = []
    if side_keys:
        sockets += [_socket(True).translate((s * PITCH, kv, 0))
                    for s in (-1, 1) for kv in SIDE_KEYS_V]
    for edge in row_keys:
        sockets += [_socket(False).translate((ku, edge, 0)) for ku in ROW_KEYS_U]
    for s in sockets:
        body = body.cut(s)
    return body, holes, sockets


def build_front():
    return _piece(FRONT_PAIRS[0], -FRONT_HALF_D, FRONT_HALF_D,
                  side_keys=True, row_keys=(FRONT_HALF_D,))


def build_mid():
    return _piece(MID_PAIR, MID_FRONT_EDGE, FRONT_HALF_D,
                  side_keys=False, row_keys=(MID_FRONT_EDGE,))


def _ring(cq_, v):
    """The console collar exactly as build_platform_steps() exports it,
    turned into this frame (its local +X = rearward = +Y here)."""
    r = E._platform_printed(cq_, platform_h(v), v, baffle_t=CONSOLE_BAFFLE_T,
                            sled=CONSOLE_SLED_T)
    return r.rotate((0, 0, 0), (0, 0, 1), 90)


def _vol(shape):
    return sum(s.Volume() for s in shape.Solids())


def _check(front, mid):
    """The base is worth printing only if the rings bolt on where the metal
    would put them, the screws reach, and every piece fits the bed."""
    f_body, _, f_sockets = front
    m_body, _, m_sockets = mid
    # 1. Hole positions: every piece placed in the world reproduces the metal
    #    base's own pattern, hole for hole.
    world = []
    for pair in FRONT_PAIRS:
        cu, cv = _pair_centre(pair)
        world += [(cu + x, cv + y) for x, y in _piece_holes(pair)]
    cu, cv = _pair_centre(MID_PAIR)
    world += [(cu + x, cv + y) for x, y in _piece_holes(MID_PAIR)]
    metal = [(h["u"], h["v"]) for h in platform_foot_holes()]
    assert len(world) == len(metal) == 40, "HOLES: expected 40 chassis screws"
    for h in metal:
        assert min(math.dist(h, w) for w in world) < 1e-9, \
            f"HOLES: metal hole at {h} has no matching base hole"
    # 2. Seams: the pieces butt with no gap and no overlap.
    cus = [_pair_centre(p)[0] for p in FRONT_PAIRS]
    for a, b in zip(cus, cus[1:]):
        assert abs((b - a) - 2 * PITCH) < 1e-9, "SEAM: front pieces do not butt"
    assert abs(_pair_centre(MID_PAIR)[0] - cus[JOIN_PAIR]) < 1e-9, \
        "SEAM: the mid piece is not centred on UNDO+MODE"
    assert abs((ROW2_Y + MID_FRONT_EDGE) - (ROW1_Y + FRONT_HALF_D)) < 1e-9, \
        "SEAM: the mid piece's front edge misses the front piece's rear edge"
    # 3. Bed.
    for name, body in (("front", f_body), ("mid", m_body)):
        bb = body.val().BoundingBox()
        assert max(bb.xlen, bb.ylen) <= BED, f"BED: {name} piece {bb.xlen:.1f} x {bb.ylen:.1f}"
    # 4. Sockets stay in solid material: a socket that breaks into a window or
    #    a counterbore leaves the key nothing to bear on.
    for body, sockets in ((f_body, f_sockets), (m_body, m_sockets)):
        _socket_clear(body, sockets)
    # 5. A seated key meets the pieces only at its four shoulders, by KEY_DRAW:
    #    more means a socket is mis-sized, less means the seam can open.
    pair = f_body.union(f_body.translate((2 * PITCH, 0, 0)))
    key = build_key().translate((PITCH, 0, SOCKET_FLOOR))
    shoulder = (KEY_HEAD_W - KEY_NECK_W) / 2.0 - KEY_CLR
    want = 4 * shoulder * KEY_DRAW * (KEY_H - KEY_LEAD)
    got = _vol(pair.val().intersect(key.val()))
    assert abs(got - want) < 0.05 * want, f"KEY: {got:.2f} mm3 of interference, expected {want:.2f}"
    # 6. Rings and screws, against the real collar geometry.
    floors = {}
    for v, body, screw_l, label in ((PEDAL_ROW1_V, f_body, FRONT_SCREW_L, "front"),
                                    (PEDAL_ROW2_V, m_body, MID_SCREW_L, "mid")):
        ring = _ring(cq, v)
        floor = floors[label] = _floor_at_centre(ring)
        for fx, fy in platform_foot_xy():
            x, y = fy, fx               # ring-local, turned into this frame
            rod_top = screw_l - CLAMP_T  # tip above the base's top face
            rod = (cq.Workplane("XY").circle(1.45).extrude(rod_top)
                   .translate((x, y, 0)))
            clash = _vol(ring.val().intersect(rod.val()))
            if label == "front":
                # through the collar floor, then into the sled insert
                engage = rod_top - floor
                assert clash < 1e-6, f"SCREW: front screw hits the collar ({clash:.2f} mm3)"
                assert 3.5 <= engage <= INSERT_L, \
                    f"SCREW: front M3x{screw_l:.0f} engages {engage:.2f} mm in the sled"
                assert engage <= INSERT_DEPTH - 0.5, "SCREW: front tip reaches the pilot floor"
            else:
                assert clash < 1e-6, f"SCREW: mid screw leaves its insert pocket ({clash:.2f} mm3)"
                assert 3.5 <= rod_top <= INSERT_DEPTH - 0.5, \
                    f"SCREW: mid M3x{screw_l:.0f} engages {rod_top:.2f} mm"
    return floors["front"]


def _piece_holes(pair):
    cu, cv = _pair_centre(pair)
    out = []
    for idx in pair:
        _, u, v = PEDALS[idx]
        for fx, fy in platform_foot_xy():
            out.append((u - cu + fy, v * _CS - cv + fx))
    return out


def _socket_clear(body, sockets):
    """Each socket, grown by 1.5 mm, may only meet the seam face it straddles:
    nothing else of the piece may be missing inside that envelope."""
    for s in sockets:
        bb = s.val().BoundingBox()
        env = cq.Workplane("XY").box(bb.xlen + 3.0, bb.ylen + 3.0, PLATE_T,
                                     centered=False).translate((bb.xmin - 1.5, bb.ymin - 1.5, 0))
        piece_env = env.intersect(_outline(body))
        missing = _vol(piece_env.cut(body).cut(s).val())   # edge chamfers only
        assert missing < 10.0, f"SOCKET at ({bb.center.x:.1f}, {bb.center.y:.1f}) breaks into a cut-out"


def _outline(body):
    """The piece's plan outline as a solid, without any of its cuts."""
    bb = body.val().BoundingBox()
    return (cq.Workplane("XY").box(bb.xlen, bb.ylen, PLATE_T, centered=False)
            .translate((bb.xmin, bb.ymin, 0)))


def _floor_at_centre(ring):
    """Collar floor thickness, measured on the real solid at the pedal centre."""
    probe = cq.Workplane("XY").box(0.5, 0.5, 200.0, centered=(True, True, False))
    return ring.val().intersect(probe.val()).BoundingBox().zmax


def _assembly(front, mid):
    """Base, keys and rings in world position, for the viewer and the render."""
    parts = []
    key = build_key()
    for pair in FRONT_PAIRS + [MID_PAIR]:
        body = (mid if pair == MID_PAIR else front)[0]
        cu, cv = _pair_centre(pair)
        parts.append(("base", body.translate((cu, cv, 0))))
    for pair in FRONT_PAIRS[:-1]:
        cu, cv = _pair_centre(pair)
        for kv in SIDE_KEYS_V:
            parts.append(("key", key.rotate((0, 0, 0), (0, 0, 1), 0)
                          .translate((cu + PITCH, cv + kv, SOCKET_FLOOR))))
    cu, cv = _pair_centre(MID_PAIR)
    for ku in ROW_KEYS_U:
        parts.append(("key", key.rotate((0, 0, 0), (0, 0, 1), 90)
                      .translate((cu + ku, cv + MID_FRONT_EDGE, SOCKET_FLOOR))))
    rings = {PEDAL_ROW1_V: _ring(cq, PEDAL_ROW1_V), PEDAL_ROW2_V: _ring(cq, PEDAL_ROW2_V)}
    for _, u, v in PEDALS:
        parts.append(("ring", rings[v].translate((u, v * _CS, PLATE_T))))
    return parts


def render_png(parts, path):
    """Shaded VTK view of the assembled base, same idiom as render_png()."""
    import vtk
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.95, 0.95, 0.95)
    colour = {"base": (0.85, 0.55, 0.15), "key": (0.15, 0.45, 0.85), "ring": (0.18, 0.18, 0.20)}
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
    front, mid = build_front(), build_mid()
    floor = _check(front, mid)
    os.makedirs(OUT, exist_ok=True)
    outs = []
    for name, body in (("front", front[0]), ("mid", mid[0]), ("key", build_key()),
                       ("coupon", build_coupon())):
        base = os.path.join(OUT, f"segno_layout_base_{name}")
        cq.exporters.export(body.val(), base + ".step")
        cq.exporters.export(body, base + ".stl", tolerance=0.05)
        outs.append(base)
    parts = _assembly(front, mid)
    asm = cq.Assembly()
    for i, (kind, wp) in enumerate(parts):
        asm.add(wp, name=f"{kind}_{i}")
    asm.export(os.path.join(OUT, "segno_layout_base_assembly.step"))
    if render:
        render_png(parts, os.path.join(OUT, "_layout_base.png"))

    fb, mb = front[0].val().BoundingBox(), mid[0].val().BoundingBox()
    n_keys = 3 * len(SIDE_KEYS_V) + len(ROW_KEYS_U)
    print("Pedal platform layout base (issue #1544)")
    print(f"  front piece x4   {fb.xlen:.2f} x {fb.ylen:.2f} x {PLATE_T:.1f} mm")
    print(f"  mid piece   x1   {mb.xlen:.2f} x {mb.ylen:.2f} x {PLATE_T:.1f} mm")
    print(f"  key         x{n_keys}  (print a couple spare)")
    print("  coupon      x2   test joint: print first with one key")
    print(f"  pitch {PITCH:.3f}, rows {ROW2_Y - ROW1_Y:.3f} apart in plan "
          f"(front row {ROW1_Y:.3f} from the console's front)")
    print(f"  screws: 32 x M3x{FRONT_SCREW_L:.0f} (front, {FRONT_SCREW_L - CLAMP_T - floor:.2f} mm "
          f"into the sled), 8 x M3x{MID_SCREW_L:.0f} (CLEAR/BANK, "
          f"{MID_SCREW_L - CLAMP_T:.2f} mm into the collar)")
    for b in outs:
        print(f"  out/{os.path.basename(b)}.step (+ .stl)")
    print("  out/segno_layout_base_assembly.step")


if __name__ == "__main__":
    import sys
    main(render="--png" in sys.argv)
