"""Geometry checks for the beam cable grommet.

Run on their own (`python check_grommet.py`) or from beam_grommet.py, which
calls check() on every part it exports. Each assertion names the rule it
protects; none of them is a tolerance to loosen until the part passes.
"""

import math

import numpy as np

import beam_grommet as g

enclosure = g.enclosure


def overhangs(solid, limit_deg=g.RETAIN_DEG):
    """Area of downward faces flatter than `limit_deg` from the bed, above Z=0.

    Tessellated triangle normals: a downward face closer to horizontal than the
    limit needs support unless it lies on the bed. The 0.02 slack covers
    the facets of the bell mouth's 45 deg cone.
    """
    verts, tris = solid.tessellate(0.01, 0.05)
    v = np.array([p.toTuple() for p in verts])
    t = v[np.array(tris)]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    limit = -math.cos(math.radians(limit_deg)) - 0.02
    on_bed = t[:, :, 2].max(axis=1) < 1e-6
    bad = (nz < limit) & ~on_bed
    return float(area[bad].sum())


def check(solid):
    d = g.derived()

    # --- a printable TPU part ---------------------------------------------
    assert solid.isValid() and len(solid.Solids()) == 1, "grommet is not one valid solid"
    # Vertices, not BoundingBox(): once the STL export has meshed the solid,
    # its box grows by the mesh tolerance.
    assert abs(min(v.Z for v in solid.Vertices())) < 1e-6, "STL frame: the flange must sit on Z=0"
    assert overhangs(solid) < 1e-3, "a face flatter than 45 deg over the bed would need support"
    for name, t in [("WALL", g.WALL), ("FLANGE_T", g.FLANGE_T),
                    ("flange ring", (d["flange_h"] - d["bore_h"]) / 2)]:
        assert t >= g.MIN_WALL, f"{name} {t:.2f} mm is thinner than {g.MIN_WALL} mm of TPU"

    # --- the membrane ------------------------------------------------------
    assert g.MIN_MEMBRANE <= g.MEMBRANE_T <= g.MAX_MEMBRANE, \
        f"membrane {g.MEMBRANE_T} mm: under {g.MIN_MEMBRANE} it tears, over {g.MAX_MEMBRANE} it will not fold"
    # Every slit ends inside the hinge band, so no flap is cut loose from the wall.
    hinge_min = 0.75 * g.HINGE
    inset = g.rrect(d["bore_w"] - 2 * hinge_min, d["bore_h"] - 2 * hinge_min,
                    max(d["bore_r"] - hinge_min, 0.1), -1, g.MEMBRANE_T + 2).val()
    for slit in g.slit_cutters(d):
        assert slit.cut(inset).Volume() < 1e-6, "a slit runs into the hinge at the bore wall"
    # Inside the hinge band the slits must cut the membrane into separate flaps:
    # that proves they meet at the centre and reach the hinge.
    band = g.HINGE + 0.5
    core = solid.intersect(g.rrect(d["bore_w"] - 2 * band, d["bore_h"] - 2 * band,
                                   0.1, -1, g.MEMBRANE_T + 1).val())
    flaps = len(core.Solids())
    assert flaps == g.SLIT_RAYS, f"the slits leave {flaps} flaps, not {g.SLIT_RAYS}"

    # --- the cables and the plug ------------------------------------------
    assert g.CABLE_MIN <= g.CABLE_OD <= g.CABLE_MAX, "the console's own cable is out of range"
    assert g.CABLE_MAX <= d["open_h"], \
        f"a {g.CABLE_MAX} mm cable would not pass the folded flaps ({d['open_h']:.1f} mm)"
    assert g.CABLE_MIN >= 4 * g.SLIT_W, "slit gaps too wide to close on the thinnest cable"
    pw, ph = g.PLUG
    assert pw + 2 * g.PLUG_CLR <= d["open_w"] and ph + 2 * g.PLUG_CLR <= d["open_h"], \
        f"the {pw} x {ph} plug does not pass the folded flaps ({d['open_w']:.1f} x {d['open_h']:.1f})"

    # --- the window --------------------------------------------------------
    painted_clr = g.FIT_CLR - g.COAT_MAX
    assert painted_clr >= 0.1, f"body clears a painted window by only {painted_clr:.2f}"
    assert d["body_r"] >= g.WIN_R - g.FIT_CLR - 1e-9, "body corner would bind in the window's R"
    # Retention: the barb crest must overlap the window edge, bare and painted.
    for label, clr in [("bare", g.FIT_CLR), ("painted", painted_clr)]:
        overlap = g.BARB - clr
        assert overlap >= g.MIN_RETAIN, f"{label}: barb overlaps the edge by {overlap:.2f}"
    # A painted web is 2*COAT_MAX thicker. Its front face must still land on the
    # 45 deg retaining face, not on the crest, so the grip stays snug.
    assert d["grip_z"] + 2 * g.COAT_MAX < d["crest_z"], "painted web overruns the barb"
    # Insertion: each finger bends inward by the barb's overlap plus its
    # clearance while the crest passes the edge. Root strain of a cantilever
    # loaded at the crest: 3 t delta / (2 L^2).
    delta = g.BARB - painted_clr
    arm = d["crest_z"] + g.BARB_LAND / 2 - g.FLANGE_T
    strain = 3 * g.WALL * delta / (2 * arm ** 2)
    assert strain <= g.MAX_STRAIN, f"finger root strain {strain:.0%} on insertion"
    assert 2 * delta < d["bore_h"], "the two fingers would meet before the barbs pass"
    assert d["barb_w"] > 0.5 * d["body_w"], "barbs too short to hold"

    # --- the beam ----------------------------------------------------------
    # The flange must bed on flat web, clear of both bends' outer radii.
    wz = (enclosure.BEAM_H - g.WIN_H) / 2.0
    bend = enclosure.BEAM_RI + enclosure.BEAM_T
    f_lo = wz - g.FLANGE_OV
    f_hi = wz + g.WIN_H + g.FLANGE_OV
    assert f_lo >= bend, f"flange runs onto the foot bend ({f_lo:.1f} < {bend:.1f})"
    assert f_hi <= enclosure.BEAM_H - bend, "flange runs onto the pad bend"
    # Neighbouring flanges must not meet, and the end ones stay on the beam.
    us = enclosure.beam_cable_u()
    gaps = [b - a - g.WIN_W - 2 * g.FLANGE_OV for a, b in zip(us, us[1:])]
    assert min(gaps) >= 2.0, f"two flanges come within {min(gaps):.1f} mm"
    left = us[0] - d["flange_w"] / 2 - enclosure.BEAM_U0
    right = enclosure.BEAM_U0 + enclosure.BEAM_LEN - us[-1] - d["flange_w"] / 2
    assert min(left, right) >= 2.0, "an end flange overhangs the beam end"
    # Installed in the real formed beam, every grommet is clear of the steel.
    beam = enclosure._beam_solid()
    for u, offset in g.placements():
        clash = beam.intersect(g.to_beam(solid, offset)).Volume()
        assert clash < 1e-3, f"grommet at u {u:.1f} cuts {clash:.3f} mm3 of the beam"
    return {"strain": strain, "painted_clr": painted_clr, "min_gap": min(gaps),
            "retain_bare": g.BARB - g.FIT_CLR, "retain_painted": g.BARB - painted_clr}


if __name__ == "__main__":
    report = check(g.build())
    for key, value in report.items():
        print(f"{key}: {value:.3f}")
