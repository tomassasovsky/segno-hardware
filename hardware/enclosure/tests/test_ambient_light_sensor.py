"""Ambient light sensor window and sleeve (tomassasovsky/segno#1564).

A Vishay TEPT5600 with its dome sanded off flat is glued in a hole at the
owner's spot A, with its flat face flush with the lid. A black PETG sleeve
bonded to the underside carries the flange, hides the body from the light
inside the console, and holds the lead with a cable tie.
"""
import json
import math
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import segno_enclosure as enclosure

LOGO = Path(__file__).resolve().parents[2] / "decals" / "reference" / "segno_logo_lid.json"


class SensorWindow(unittest.TestCase):

    def setUp(self):
        self.cuts = {c["ref"]: c for c in enclosure.faceplate_holes()}
        self.hole = self.cuts["ALS"]

    def test_spot_a_is_midway_between_clear_and_bank_on_the_logo_centre_line(self):
        clear, bank = self.cuts["CLEAR"], self.cuts["BANK"]
        mid = (clear["u"] + clear["w"] / 2 + bank["u"] + bank["w"] / 2) / 2
        self.assertAlmostEqual(self.hole["u"], mid, places=9)
        self.assertEqual(self.hole["v"], 385.0)
        xs = [p[0] for parts in json.loads(LOGO.read_text())["bodies"].values()
              for loop in parts for p in loop["pts"]]
        self.assertAlmostEqual(self.hole["u"], (min(xs) + max(xs)) / 2, delta=0.1)

    def test_the_smallest_painted_hole_clears_the_largest_body_by_the_fit(self):
        smallest = self.hole["d"] - enclosure.SHOP_TOL - 2 * enclosure.COAT_MAX
        largest = enclosure.TEPT_BODY_D + enclosure.TEPT_BODY_TOL
        self.assertGreaterEqual(smallest - largest, 0.20 - 1e-9)

    def test_the_hole_is_clear_of_every_other_opening_and_the_rear_fold(self):
        box = enclosure._bbox(self.hole)
        for ref, cut in self.cuts.items():
            if ref == "ALS":
                continue
            with self.subTest(ref=ref):
                self.assertFalse(enclosure._overlap(box, enclosure._bbox(cut), clr=20.0))
        self.assertGreater(enclosure.FP_V - box[3], 15.0)

    def test_the_laser_cuts_it(self):
        self.assertIn("ALS", {c["ref"] for c in enclosure.faceplate_metal_cuts()})


class CutFiles(unittest.TestCase):
    """The window in the files the shop cuts from, not just in the schedule:
    the generated lid DXF and the flat exported from the formed Fusion lid."""

    def sensor_circles(self, path):
        import ezdxf
        r = enclosure.ALS_HOLE_D / 2
        return [c for c in ezdxf.readfile(path).modelspace().query("CIRCLE")
                if abs(c.dxf.radius - r) < 1e-6]

    def test_the_generated_lid_drawing_cuts_it(self):
        path = Path(enclosure.OUT) / "segno_faceplate.dxf"
        if not path.exists():
            self.skipTest("run segno_enclosure.py first")
        circles = self.sensor_circles(path)
        self.assertEqual(len(circles), 1)
        c = circles[0]
        self.assertEqual(c.dxf.layer, "CUT")
        self.assertAlmostEqual(c.dxf.center.x, enclosure.LID_OX + enclosure.ALS_U, places=6)
        self.assertAlmostEqual(c.dxf.center.y, enclosure.LID_FRONT_FL + enclosure.LID_FRONT_EXTRA
                               + enclosure.ALS_V, places=6)

    def test_the_formed_flat_from_fusion_cuts_the_same_hole(self):
        path = Path(enclosure.HERE) / "formed" / "segno_faceplate_flat.dxf"
        circles = self.sensor_circles(path)
        self.assertEqual(len(circles), 1, "formed flat is stale: re-export it from Fusion")
        c = circles[0]
        # drawn from the opposite face: mirrored across the blank's width
        self.assertAlmostEqual(c.dxf.center.x, enclosure.LID_OX + enclosure.ALS_U - enclosure.LID_W,
                               places=4)
        self.assertAlmostEqual(c.dxf.center.y, enclosure.LID_FRONT_FL + enclosure.LID_FRONT_EXTRA
                               + enclosure.ALS_V, places=4)


class SandedSensor(unittest.TestCase):

    def test_sanding_off_the_dome_leaves_the_chip_covered(self):
        self.assertAlmostEqual(enclosure.TEPT_SANDED_H, 5.15, places=9)
        self.assertGreater(enclosure.TEPT_CHIP_DEPTH - enclosure.TEPT_SAND_MAX, 1.5)

    def test_the_face_always_reaches_the_sheet_before_the_sleeve_reaches_the_lid(self):
        """Face-down assembly sets the face flush only if the sleeve never
        bottoms on the lid first: shortest sensor, thickest painted lid."""
        e = enclosure
        thinnest = e.TEPT_SANDED_H_MIN - e.ALS_LID_T_MAX - e.ALS_SEAT
        thickest = e.TEPT_SANDED_H_MAX - (e.T + 2 * e.COAT_MIN) - e.ALS_SEAT
        self.assertGreaterEqual(thinnest, e.ALS_GLUE_MIN - 1e-9)
        self.assertLess(thickest, 0.6)          # an epoxy line, not a gap
        self.assertAlmostEqual(e.ALS_SEAT + e.ALS_GLUE + e.ALS_LID_T, e.TEPT_SANDED_H, places=9)


class Sleeve(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.solid = enclosure._als_sleeve_solid()

    def test_bores_clear_the_largest_body_and_flange(self):
        self.assertGreater(enclosure.ALS_BODY_BORE, enclosure.TEPT_BODY_D + enclosure.TEPT_BODY_TOL)
        self.assertGreater(enclosure.ALS_FLANGE_BORE, enclosure.TEPT_FLANGE_D + 0.15)
        self.assertLess(enclosure.ALS_BODY_BORE, enclosure.TEPT_FLANGE_D - 0.15)

    def test_it_is_one_small_part_with_a_flat_bond_face(self):
        bb = self.solid.BoundingBox()
        self.assertAlmostEqual(bb.zmin, 0.0, places=6)
        reach = math.hypot(enclosure.ALS_SLEEVE_OD / 2, enclosure.ALS_TONGUE_W / 2)
        for v in self.solid.Vertices():
            self.assertLessEqual(math.hypot(v.X, v.Y), reach + 1e-6)
        bond = [f for f in self.solid.Faces()
                if f.geomType() == "PLANE" and abs(f.Center().z) < 1e-6]
        self.assertEqual(len(bond), 1)
        r_out, r_in = enclosure.ALS_SLEEVE_OD / 2, enclosure.ALS_BODY_BORE / 2
        self.assertAlmostEqual(bond[0].Area(), math.pi * (r_out**2 - r_in**2), delta=0.5)

    def test_its_envelope_clears_the_parts_under_the_rear_strip(self):
        """The sleeve hangs about 23 mm into the console. Keep it above the power
        group and inside the walls if either moves (Fusion measured 13.8 mm to the
        nearest body, the base, on 2026-11-03)."""
        e = enclosure
        (x, y, z), n = e.als_axis_world()
        length = e.ALS_GLUE + e.ALS_SLEEVE_H + e.ALS_TONGUE_L
        r = math.hypot(e.ALS_SLEEVE_OD / 2, e.ALS_TONGUE_W / 2)    # tongue corners
        # the axis runs down the inside normal; the rim adds r * the slope's sine/cosine
        lowest = z - length * n[2] - r * abs(n[1])
        y_rear = y - length * n[1] + r * n[2]
        x0, x1 = x - r, x + r
        self.assertLess(y_rear, e.D - e.T - 10.0)
        tops = []
        for _ref, u, v, _ears in e.buck_mounts():
            tops.append((u, v, e.BUCK_BODY[0], e.BUCK_BODY[1], e.T + e.RAIL_T + e.BUCK_BODY[2]))
        for _ref, u, v, _holes, (su, sv), so, tall in e.aux_board_mounts():
            tops.append((u, v, su, sv, e.T + so + e.AUX_PCB_T + tall))
        for u, v, su, sv, top in tops:
            if u + su / 2 < x0 - 10 or u - su / 2 > x1 + 10:
                continue
            with self.subTest(u=u, v=v):
                self.assertGreater(lowest - top, 20.0)

    def test_it_ships_in_the_print_package(self):
        archive = Path(enclosure.OUT) / "segno_3dprint.zip"
        if not archive.exists():
            self.skipTest("run segno_enclosure.py first")
        with zipfile.ZipFile(archive) as z:
            self.assertTrue({"segno_als_sleeve.step", "segno_als_sleeve.stl"} <= set(z.namelist()))


if __name__ == "__main__":
    unittest.main()
