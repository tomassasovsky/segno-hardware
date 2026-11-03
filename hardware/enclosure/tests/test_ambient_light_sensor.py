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

    def test_the_largest_body_passes_the_smallest_painted_hole(self):
        smallest = self.hole["d"] - enclosure.SHOP_TOL - 2 * enclosure.COAT_MAX
        self.assertGreaterEqual(smallest, enclosure.TEPT_BODY_D + enclosure.TEPT_BODY_TOL - 1e-9)

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


class SandedSensor(unittest.TestCase):

    def test_sanding_off_the_dome_leaves_the_chip_covered(self):
        self.assertAlmostEqual(enclosure.TEPT_SANDED_H, 5.15, places=9)
        self.assertGreater(enclosure.TEPT_CHIP_DEPTH - enclosure.TEPT_SAND_MAX, 1.5)

    def test_the_flat_face_is_flush_with_the_painted_lid_on_the_seat(self):
        self.assertAlmostEqual(enclosure.ALS_SEAT + enclosure.ALS_GLUE + enclosure.ALS_LID_T,
                               enclosure.TEPT_SANDED_H, places=9)


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
        self.assertLessEqual(bb.xlen, enclosure.ALS_SLEEVE_OD + 1e-6)
        self.assertLessEqual(bb.ylen, enclosure.ALS_SLEEVE_OD + 1e-6)
        bond = [f for f in self.solid.Faces()
                if f.geomType() == "PLANE" and abs(f.Center().z) < 1e-6]
        self.assertEqual(len(bond), 1)
        r_out, r_in = enclosure.ALS_SLEEVE_OD / 2, enclosure.ALS_BODY_BORE / 2
        self.assertAlmostEqual(bond[0].Area(), math.pi * (r_out**2 - r_in**2), delta=0.5)

    def test_it_ships_in_the_print_package(self):
        archive = Path(enclosure.OUT) / "segno_3dprint.zip"
        if not archive.exists():
            self.skipTest("run segno_enclosure.py first")
        with zipfile.ZipFile(archive) as z:
            self.assertTrue({"segno_als_sleeve.step", "segno_als_sleeve.stl"} <= set(z.namelist()))


if __name__ == "__main__":
    unittest.main()
