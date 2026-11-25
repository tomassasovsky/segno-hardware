"""Snap-in TPU grommet for the cable windows in the faceplate support beam (mm).

One grommet per window, one cable per grommet. The flange sits on the web's
REAR face, the hollow body fills the window, and two barbed fingers pass
through and hold the web's front face. A slit from the cable hole to the top
edge lets it go on over a cable that is already wired.

Part frame, which is also the print orientation (flange down, no supports):
  x = u, along the beam, across the window's 24 mm width;
  y = z, up the web, across the window's 12 mm height;
  z = through the web, 0 at the flange's outer face. The web's rear face is at
      z = FLANGE_T and its front face at z = GRIP_Z.
The hole axis is the part's z axis, so the cable passes the web at the
window centre.

Run with the enclosure venv:
    ../enclosure/.venv/bin/python beam_grommet.py [--cable-od 4.0]
"""

import argparse
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

# --- the cable --------------------------------------------------------------
CABLE_OD = 4.0          # black 2-core footswitch cable, jacketed
HOLE_CLR = 0.2          # on the diameter; FDM TPU holes print ~0.1-0.2 under,
                        # so this ends up a light slide on the jacket
# The board end carries a JST XHP-2 housing, about 5.8 x 7.4 mm, which will
# not pass the hole: that is why the grommet is slit.

# --- the part ---------------------------------------------------------------
FIT_CLR = 0.25          # per side, body to bare window. Paint takes COAT_MAX of it.
WALL = 1.6              # body wall: four 0.4 mm perimeters of TPU
FLANGE_T = 2.0          # ten 0.2 mm layers; stiff enough not to pull through
FLANGE_OV = 2.5         # flange overlap past the window edge, every side
BARB = 1.0              # barb height past the body wall
BARB_LAND = 0.4         # flat on the barb's crest
RETAIN_DEG = 45.0       # retaining face, from the print bed: the steepest
                        # overhang TPU prints without support
LEAD_DEG = 30.0         # lead-in face, from the insertion axis
RELIEF_W = 1.0          # corner slots that free the two long walls as fingers
BARB_MARGIN = 0.5       # barb stops short of each relief slot
SLIT_W = 0.5            # printed kerf from the hole to the top edge
BELL = 0.8              # 45 deg chamfer on the hole's flange-side mouth

MIN_WALL = 1.2          # three perimeters: the thinnest TPU section allowed
MAX_STRAIN = 0.30       # finger root strain while the barb squeezes through
MIN_RETAIN = 0.6        # barb overlap on the window edge, bare and painted


def derived(cable_od=CABLE_OD):
    """Every dimension the build and the checks share."""
    d = {}
    d["hole"] = cable_od + HOLE_CLR
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
    return d


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


def build(cable_od=CABLE_OD):
    d = derived(cable_od)
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

    # The cable hole, with a 45 deg bell mouth on the flange's outer face where
    # the cable turns down to the floor.
    hole_r = d["hole"] / 2
    part = part.cut(cq.Workplane("XY").circle(hole_r).extrude(FLANGE_T + 1).translate((0, 0, -0.5)))
    bell = cq.Solid.makeCone(hole_r + BELL + 0.5, hole_r, BELL + 0.5,
                             pnt=cq.Vector(0, 0, -0.5))
    part = part.cut(cq.Workplane().add(bell))

    # The slit: hole to the top edge, through the flange, the top finger and its barb.
    slit = (cq.Workplane("XY")
            .box(SLIT_W, d["flange_h"], d["tip_z"] + 2, centered=(True, False, False))
            .translate((0, 0, -1)))
    part = part.cut(slit)
    return part.val()


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


def export(cable_od=CABLE_OD):
    OUT.mkdir(exist_ok=True)
    stem = OUT / f"beam_grommet_od{cable_od:.1f}"
    solid = build(cable_od)
    cq.exporters.export(solid, f"{stem}.step")
    cq.exporters.export(solid, f"{stem}.stl", tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(installed(solid), f"{stem}_installed.step")
    # OpenCascade adds trailing spaces to STEP entity lines.
    for path in (Path(f"{stem}.step"), Path(f"{stem}_installed.step")):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    return solid


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cable-od", type=float, default=CABLE_OD,
                    help="cable outer diameter, mm (default %(default)s)")
    args = ap.parse_args()
    import check_grommet
    solid = export(args.cable_od)
    check_grommet.check(solid, args.cable_od)
    print(f"beam_grommet_od{args.cable_od:.1f}: {solid.Volume() / 1000:.2f} cm3, checks passed -> {OUT}")
    for u, y_front, y_rear, z in hole_world():
        print(f"  cable crosses the web at u {u:7.2f}, y {y_front:.2f}..{y_rear:.2f}, z {z:.2f}")


if __name__ == "__main__":
    main()
