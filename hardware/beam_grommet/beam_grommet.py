"""Snap-in TPU grommet for the cable windows in the faceplate support beam (mm).

One grommet per window, one cable per grommet. Its edge is a groove that hugs
the web: a thin flange on the web's REAR face, a neck as long as the web is
thick, and a barbed lip on each long side that snaps over the front face. The cable passes a thin membrane in the
flange, cut by eight radial slits that meet at the window centre: the flaps
part for any cable from CABLE_MIN to CABLE_MAX and close on it, and fold flat
against the bore to let the board-end plug through.

Part frame, which is also the print orientation (flange down, no supports):
  x = u, along the beam, across the window's 24 mm width;
  y = z, up the web, across the window's 12 mm height;
  z = through the web, 0 at the flange's outer face. The web's rear face is at
      z = FLANGE_T and its front face at z = GRIP_Z.
The slits meet on the part's z axis, so the cable passes the web at the
window centre.

Run with the enclosure venv:
    ../enclosure/.venv/bin/python beam_grommet.py
"""

import math
from pathlib import Path
import sys

import cadquery as cq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "enclosure"))
import segno_enclosure as enclosure  # noqa: E402

OUT = HERE / "out"

# --- the window, from the enclosure ----------------------------------------
WIN_W = enclosure.BEAM_CABLE_W        # 24.0, along u
WIN_H = enclosure.BEAM_CABLE_H        # 12.0, along z
WIN_R = enclosure.BEAM_CABLE_R        # 3.0
WEB_T = enclosure.BEAM_T              # 1.6 cold-rolled steel
COAT_MAX = enclosure.COAT_MAX         # 0.10 per face once painted

# --- the cables -------------------------------------------------------------
CABLE_OD = 4.0          # the console's footswitch and LED-feed cable, all ten windows
CABLE_MIN = 2.0         # the range one grommet takes: below it the slit gaps
CABLE_MAX = 7.0         # are a large share of the wire; above it the flaps run
                        # out of bore to fold into
PLUG = (7.4, 5.8)       # JST XHP-2 housing on the board end, passed flat: 7.4
                        # along u, 5.8 along z, through the folded flaps
PLUG_CLR = 0.3          # per side, plug to folded flaps

# --- the part ---------------------------------------------------------------
FIT_CLR = 0.25          # per side, body to bare window. Paint takes COAT_MAX of it.
WALL = 1.2              # neck wall: three 0.4 mm perimeters of TPU
FLANGE_T = 1.2          # six 0.2 mm layers, the membrane's three among them
FLANGE_OV = 2.0         # flange overlap past the window edge, every side
BARB = 1.0              # barb height past the body wall
BARB_LAND = 0.3         # flat on the barb's crest
RETAIN_DEG = 45.0       # retaining face, from the print bed: the steepest
                        # overhang TPU prints without support
LEAD_DEG = 45.0         # lead-in face, from the insertion axis
RELIEF_W = 1.0          # corner slots that free the two long walls as fingers
BARB_MARGIN = 0.5       # barb stops short of each relief slot
MEMBRANE_T = 0.6        # three 0.2 mm layers, printed first, on the bed
SLIT_W = 0.4            # printed gap of each radial slit (one line width)
SLIT_RAYS = 8           # +-u, +-z and one to each corner of the bore
HINGE = 0.8             # unslit membrane left between a slit's end and the bore
                        # wall; the flaps fold about it

MIN_WALL = 1.2          # three perimeters: the thinnest TPU section allowed
MAX_STRAIN = 0.30       # finger root strain while the barb squeezes through
MIN_RETAIN = 0.6        # barb overlap on the window edge, bare and painted
MIN_MEMBRANE = 0.6      # three layers: a thinner membrane tears at the slit ends
MAX_MEMBRANE = 1.0      # a thicker one is too stiff to fold for the plug


def derived():
    """Every dimension the build and the checks share."""
    d = {}
    d["body_w"] = WIN_W - 2 * FIT_CLR
    d["body_h"] = WIN_H - 2 * FIT_CLR
    d["body_r"] = WIN_R - FIT_CLR
    d["bore_w"] = d["body_w"] - 2 * WALL
    d["bore_h"] = d["body_h"] - 2 * WALL
    d["bore_r"] = max(d["body_r"] - WALL, 0.4)
    d["flange_w"] = WIN_W + 2 * FLANGE_OV
    d["flange_h"] = WIN_H + 2 * FLANGE_OV
    d["flange_r"] = WIN_R + FLANGE_OV
    d["grip_z"] = FLANGE_T + WEB_T                       # web front face
    d["retain_rise"] = BARB / math.tan(math.radians(RETAIN_DEG))
    d["lead_len"] = BARB / math.tan(math.radians(LEAD_DEG))
    d["crest_z"] = d["grip_z"] + d["retain_rise"]
    d["tip_z"] = d["crest_z"] + BARB_LAND + d["lead_len"]
    d["relief_x"] = d["body_w"] / 2 - d["body_r"]        # where each long wall's arc starts
    d["finger_w"] = 2 * (d["relief_x"] - RELIEF_W)
    d["barb_w"] = d["finger_w"] - 2 * BARB_MARGIN
    # The opening the folded flaps leave, inside the bore.
    d["open_w"] = d["bore_w"] - 2 * MEMBRANE_T
    d["open_h"] = d["bore_h"] - 2 * MEMBRANE_T
    return d


def slit_rays(d):
    """(angle, length) of each radial slit, from the centre toward the bore wall.

    Four rays run along +-u and +-z; the other four aim at the bore's corners,
    so the eight flaps are all hinged on straight bore wall. Each slit stops
    where both corners of its end are still HINGE from every bore wall.
    """
    hw, hh = d["bore_w"] / 2, d["bore_h"] / 2
    corner = math.degrees(math.atan2(hh, hw))
    rays = []
    for a in (0, corner, 90, 180 - corner, 180, 180 + corner, 270, 360 - corner):
        c, s = abs(math.cos(math.radians(a))), abs(math.sin(math.radians(a)))
        length = math.inf
        for half, along, across in ((hw, c, s), (hh, s, c)):
            if along > 1e-9:
                length = min(length, (half - HINGE - SLIT_W / 2 * across) / along)
        rays.append((a, length))
    return rays


def rrect(w, h, r, z0, height):
    return (cq.Workplane("XY").workplane(offset=z0)
            .sketch().rect(w, h).vertices().fillet(r).finalize()
            .extrude(height))


def barb(d, side):
    """One barb, a prism along x on the long wall at y = side * body_h / 2.

    In (outward, z): it starts flush with the wall at the web's front face,
    climbs the 45 deg retaining face, runs the crest and leans back to the wall
    at the tip. Its inner edge digs 0.5 into the wall so the union is solid.
    """
    g, c, t = d["grip_z"], d["crest_z"], d["tip_z"]
    pts = [(-0.5, g), (0.0, g), (BARB, c), (BARB, c + BARB_LAND), (0.0, t), (-0.5, t)]
    prof = (cq.Workplane("YZ", origin=(-d["barb_w"] / 2, 0, 0))
            .polyline([(side * (d["body_h"] / 2 + o), z) for o, z in pts]).close()
            .extrude(d["barb_w"]))
    return prof


def build():
    d = derived()
    part = rrect(d["flange_w"], d["flange_h"], d["flange_r"], 0, FLANGE_T)
    body = rrect(d["body_w"], d["body_h"], d["body_r"], FLANGE_T, d["tip_z"] - FLANGE_T)
    body = body.cut(rrect(d["bore_w"], d["bore_h"], d["bore_r"], FLANGE_T, d["tip_z"]))
    part = part.union(body).union(barb(d, 1)).union(barb(d, -1))

    # Corner reliefs: four slots through the wall where each long side meets
    # its corner arc, from the flange face to the tip. The long walls become
    # cantilever fingers that flex inward; the C-shaped ends stay stiff.
    depth = WALL + BARB + 1.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            slot = (cq.Workplane("XY")
                    .box(RELIEF_W, depth, d["tip_z"] - FLANGE_T + 1, centered=(True, False, False))
                    .translate((sx * (d["relief_x"] - RELIEF_W / 2),
                                d["body_h"] / 2 - WALL - 0.01 if sy > 0 else -(d["body_h"] / 2 - WALL - 0.01) - depth,
                                FLANGE_T)))
            part = part.cut(slot)

    # The membrane: the bore runs on down through the flange and stops
    # MEMBRANE_T above the bed, so the membrane is the first layers printed and
    # every wall above it is vertical.
    part = part.cut(rrect(d["bore_w"], d["bore_h"], d["bore_r"], MEMBRANE_T, FLANGE_T))
    for slit in slit_cutters(d):
        part = part.cut(slit)
    return part.val()


def slit_cutters(d):
    """One box per radial slit, through the membrane, starting at the centre."""
    return [cq.Workplane("XY")
            .box(length, SLIT_W, MEMBRANE_T + 1, centered=(False, True, False))
            .translate((0, 0, -0.5))
            .rotate((0, 0, 0), (0, 0, 1), angle).val()
            for angle, length in slit_rays(d)]


def placements():
    """Each window's grommet transform into the beam's local frame.

    The beam frame is `_beam_solid`'s: x from the beam's left end, y forward of
    the foot's free edge (web front face at y = BEAM_FOOTL), z up from the floor
    top. Part z = 0 (flange outer face) lands on y = BEAM_FOOTL + WEB_T + FLANGE_T,
    so the flange beds on the web's rear face and the fingers point forward.
    """
    wz = (enclosure.BEAM_H - WIN_H) / 2.0
    y0 = enclosure.BEAM_FOOTL + WEB_T + FLANGE_T
    return [(u, (u - enclosure.BEAM_U0, y0, wz + WIN_H / 2.0)) for u in enclosure.beam_cable_u()]


def to_beam(solid, offset):
    # Rotate +90 deg about x: part (x, y, z) -> (x, -z, y). Part z (through the
    # web, flange first) becomes -y, so the fingers point forward; part y (up
    # the window) becomes z.
    return solid.rotate((0, 0, 0), (1, 0, 0), 90).translate(offset)


# The beam's local frame sits here in the console's world frame (see
# `_beam_solid`): world x = u, y = depth from the front, z up from the floor
# bottom.
BEAM_ORIGIN = (enclosure.BEAM_U0, enclosure._BEAM_VP - enclosure.BEAM_FOOTL, enclosure.T)


def hole_world():
    """Where each cable crosses the web, world (u, front-face y, rear-face y, z)."""
    _, y, z = BEAM_ORIGIN
    return [(u, y + enclosure.BEAM_FOOTL, y + enclosure.BEAM_FOOTL + WEB_T, zc + z)
            for u, (_, _, zc) in placements()]


def installed(solid):
    """The ten grommets where they sit in the console, world frame."""
    return cq.Compound.makeCompound(
        [to_beam(solid, offset).translate(BEAM_ORIGIN) for _, offset in placements()])


def export():
    OUT.mkdir(exist_ok=True)
    stem = OUT / "beam_grommet"
    solid = build()
    cq.exporters.export(solid, f"{stem}.step")
    cq.exporters.export(solid, f"{stem}.stl", tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(installed(solid), f"{stem}_installed.step")
    # OpenCascade adds trailing spaces to STEP entity lines.
    for path in (Path(f"{stem}.step"), Path(f"{stem}_installed.step")):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    return solid


def main():
    import check_grommet
    solid = export()
    check_grommet.check(solid)
    print(f"beam_grommet: {solid.Volume() / 1000:.2f} cm3, checks passed -> {OUT}")
    for u, y_front, y_rear, z in hole_world():
        print(f"  cable crosses the web at u {u:7.2f}, y {y_front:.2f}..{y_rear:.2f}, z {z:.2f}")


if __name__ == "__main__":
    main()
