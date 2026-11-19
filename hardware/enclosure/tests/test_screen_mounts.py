"""The screen mounts after #1070: closed where they can be, one mirrored 15.6in
tower, and adjustable on the floor. Since #1867 the 15.6in towers carry a folded
aluminium deck plate instead of a printed deck.

Owner review 2026-09-18: too many openings, 15.6in halves that were not mirror
images, and no adjustment for tolerances. Each test below pins one answer.
"""
from contextlib import redirect_stdout
import io
import itertools
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import segno_enclosure as enclosure

SLOPE = math.radians(enclosure.SLOPE_ANGLE)


class ScreenMountTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = tempfile.TemporaryDirectory(prefix='segno-screen-mounts-')
        cls.addClassCleanup(cls.output.cleanup)
        out = Path(cls.output.name)
        with patch.object(enclosure, 'OUT', str(out)), redirect_stdout(io.StringIO()):
            enclosure.build_screen7_tower_step()
            enclosure.build_screen16_stand_steps()
            enclosure.build_screen16_monitor_step()
            enclosure.build_screen7_deck_fit_test()
        cls.parts = {p.stem: cq.importers.importStep(str(p)).val()
                     for p in out.glob('*.step')}
        cls.tower = cls.parts['segno_screen7_tower']

    # --- 7in tower ---------------------------------------------------------

    def deck_point(self, x, y, depth):
        """Tower-frame point `depth` below the deck top, at in-plane (x, y)."""
        return cq.Vector(x,
                         y * math.cos(SLOPE) + depth * math.sin(SLOPE),
                         enclosure.S7T_H0 + y * math.sin(SLOPE) - depth * math.cos(SLOPE))

    def test_7in_deck_is_closed_except_the_connector_notch(self):
        """v3 had a 146 x 96 window here. Sample the deck skin every 5 mm across
        the module's footprint: every point is metal unless it lies in the
        connector notch. (The strip-ring carrier notch went when the ring moved
        down the slope, #1090.)"""
        x0, y0, x1, y1 = enclosure.S7C_MOD_BB
        ny0 = enclosure.S7C_PORTS_Y[0] - enclosure.S7T_PLUG_MARGIN
        ny1 = enclosure.S7C_PORTS_Y[1] + enclosure.S7T_PLUG_MARGIN
        nx0 = enclosure.S7C_PORTS_X0 - enclosure.S7T_PLUG_MARGIN
        open_points = []
        for i, j in itertools.product(range(int(x0) + 5, int(x1) - 4, 5),
                                      range(int(y0) + 5, int(y1) - 4, 5)):
            in_notch = i > nx0 - 0.5 and ny0 - 0.5 < j < ny1 + 0.5
            if any(math.dist((i, j), h) < 3.0 for h in enclosure.S7C_HOLES):
                continue                              # a tab boss's own pilot
            if not self.tower.isInside(self.deck_point(i, j, 1.0)):
                open_points.append((i, j))
                self.assertTrue(in_notch, f'deck open at ({i}, {j}), outside the connector notch')
        self.assertTrue(open_points, 'the connector notch is missing')

    def test_7in_tower_prints_flange_down_without_support(self):
        """Every downward face is either on the bed or leans at least 44 degrees
        from horizontal. The worst ones are the gables, where 45 degrees across the
        cell meets the 12.5 degree deck slope. A flat ceiling anywhere would need
        support inside a closed box, where nobody can remove it."""
        bed = enclosure.STAND_SHIM_NOM
        limit = math.cos(math.radians(44.0))
        for face in self.tower.Faces():
            if face.geomType() != 'PLANE':
                continue
            nz = face.normalAt().z
            if nz < -limit:
                self.assertAlmostEqual(face.BoundingBox().zmax, bed, places=6,
                                       msg=f'unsupported ceiling at {face.Center()}')

    def test_7in_connector_notch_clears_every_plug(self):
        """A plug envelope per connector, from the receptacle out past the tower,
        4 mm either side of its centre height and widened by the plug margin:
        nothing of the tower may be in it."""
        glass = (enclosure.S7C_MOD_DEPTH + enclosure.S7C_GAP
                 - enclosure.SCREEN_COATED_SETBACK)     # glass front above the deck top
        ports = ((30.95, 45.95), (16.85, 24.75), (3.75, 11.65), (-7.75, 1.25))
        m = enclosure.S7T_PLUG_MARGIN
        plane = (cq.Workplane('XY').workplane(offset=enclosure.S7T_H0)
                 .transformed(rotate=(enclosure.SLOPE_ANGLE, 0, 0)))
        for py0, py1 in ports:
            plug = (plane.workplane(offset=glass - 3.0)
                    .center((enclosure.S7C_PORTS_X0 + 120.0) / 2.0, (py0 + py1) / 2.0)
                    .rect(120.0 - enclosure.S7C_PORTS_X0, py1 - py0 + 2 * m)
                    .extrude(-(glass - 3.0) - 1.0).val())
            self.assertLess(self.tower.intersect(plug).Volume(), 1e-6, (py0, py1))

    def test_7in_ring_board_clears_the_closed_deck(self):
        """The front notch is gone; the PR #990 ring board must still clear the
        deck by 2 mm. Each probed part's underside rises rearward at the slope."""
        ref = json.loads((Path(enclosure.HERE) / 'reference/ring_board_envelope.json').read_text())
        tx, ty, tz = ref['tower_translation_mm']
        # The envelope was measured with the encoder at v 229.16; the ring board
        # rides the encoder axis, so shift the tower by the opposite of its move
        # along the slope (#1090).
        dv = enclosure.ENC_V - 229.15982117368537
        tower = self.tower.translate((tx, ty - dv*math.cos(SLOPE), tz - dv*math.sin(SLOPE)))
        gaps = []
        for body in ref['bodies']:
            (bx0, bx1), (by0, by1), (bz0, _) = body['x'], body['y'], body['z']
            rise = (by1 - by0) * math.tan(SLOPE)
            keep_out = (cq.Workplane('YZ').workplane(offset=bx0)
                        .polyline([(by0, bz0 - 2.0), (by1, bz0 + rise - 2.0),
                                   (by1, 200.0), (by0, 200.0)]).close()
                        .extrude(bx1 - bx0).val())
            self.assertLess(tower.intersect(keep_out).Volume(), 1e-6, body['part'])
            gaps.append(tower.distance(keep_out) + 2.0)
        self.assertGreater(min(gaps), 3.0)

    # --- 15.6in stand ------------------------------------------------------

    def test_15in6_towers_are_one_part_mirrored(self):
        left = self.parts['segno_screen16_stand_L']
        right = self.parts['segno_screen16_stand_R']
        mirrored = left.mirror('YZ', (enclosure.SCREEN_16_U, 0, 0))
        self.assertLess(mirrored.cut(right).Volume(), 1e-6)
        self.assertLess(right.cut(mirrored).Volume(), 1e-6)

    def test_15in6_tower_walls_reach_the_deck_plate(self):
        """v3 stopped the tube at the ribs' bottom edge, leaving a 15 mm slot in
        both end walls under the deck. Sample the outboard end wall of the left
        tower up to just under the plate's underside."""
        d = enclosure.s16_deck()
        stand = self.parts['segno_screen16_stand_L']
        x = d.towers[0][0] + enclosure.S16_WALL / 2.0
        for y in (d.yc - 30.0, d.yc, d.yc + 30.0):
            for z in range(12, int(d.plane_z(d.w_bot, y)) - 1, 3):
                self.assertTrue(stand.isInside(cq.Vector(x, y, z)), (y, z))

    def test_15in6_tower_prints_flange_down_without_support(self):
        """The insert bosses hang inside the tube on 45 degree cones; nothing
        else faces down except the feet on the bed."""
        limit = math.cos(math.radians(44.0))
        bed = enclosure.FLOOR_TOP + enclosure.STAND_SHIM_NOM
        stand = self.parts['segno_screen16_stand_L']
        for face in stand.Faces():
            if face.geomType() == 'PLANE' and face.normalAt().z < -limit:
                self.assertAlmostEqual(face.BoundingBox().zmax, bed, places=6,
                                       msg=f'unsupported ceiling at {face.Center()}')
        cones = [f for f in stand.Faces() if f.geomType() == 'CONE']
        self.assertEqual(len(cones), 2)

    def test_15in6_deck_is_one_plate_across_both_towers(self):
        """One folded plate, the full old deck width, bearing on both towers'
        tops and touching (never entering) either tower or the monitor."""
        d = enclosure.s16_deck()
        deck = self.parts['segno_monitor_deck']
        self.assertTrue(deck.isValid())
        self.assertEqual(len(deck.Solids()), 1)
        bb = deck.BoundingBox()
        self.assertAlmostEqual(bb.xmin, d.towers[0][0], places=6)
        self.assertAlmostEqual(bb.xmax, d.towers[1][1], places=6)
        # sheet volume: the blank less its cut-outs, times the thickness. The
        # solid's bend holds its mid-surface length (K = 0.5), not the K 0.33
        # development the flat pattern uses.
        mid = d.flat_d + (math.pi / 2 * (enclosure.RI + enclosure.T / 2) - enclosure.BA90)
        wx0, wx1, wL0, wL1 = d.win
        window = (wx1 - wx0) * (wL1 - wL0) - (4 - math.pi) * enclosure.R_FILLET ** 2
        holes = math.pi / 4 * (2 * enclosure.S16_VESA_CLR_D ** 2 + 4 * enclosure.D_M3_METAL ** 2)
        self.assertAlmostEqual(deck.Volume() / enclosure.T,
                               d.flat_w * mid - window - holes, delta=1.0)
        for side in ('L', 'R'):
            stand = self.parts['segno_screen16_stand_' + side]
            self.assertLess(stand.intersect(deck).Volume(), 1e-6)
            self.assertLess(stand.distance(deck), 1e-6)
        monitor = self.parts['segno_screen16_monitor']
        self.assertLess(deck.intersect(monitor).Volume(), 1e-6)
        self.assertLess(deck.distance(monitor), 1e-6)

    def test_15in6_deck_folds_down_at_the_front_and_is_flat_at_the_rear(self):
        d = enclosure.s16_deck()
        deck = self.parts['segno_monitor_deck']
        x = d.xc - 100.0
        inside = lambda L, w: deck.isInside(cq.Vector(*d.world(x, L, w)))
        # front flange: 1 mm in from its outside face, from the plate down to its tip
        for w in (d.w_bot - 3.0, d.w_front_tip + 0.5):
            self.assertTrue(inside(d.Lf + 1.0, w), w)
        self.assertFalse(inside(d.Lf + 1.0, d.w_front_tip - 0.5))
        self.assertFalse(inside(d.Lf + 1.0, d.w_top + 3.0))
        # rear edge: a plain cut, flat plate up to it and nothing above or below
        mid = (d.w_top + d.w_bot) / 2.0
        self.assertTrue(inside(d.Lr - 0.5, mid))
        self.assertFalse(inside(d.Lr + 0.5, mid))
        self.assertFalse(inside(d.Lr - 1.0, d.w_top + 1.0))
        self.assertFalse(inside(d.Lr - 1.0, d.w_bot - 1.0))
        bb = deck.BoundingBox()
        top = max(d.world(x, L, d.w_top)[2] for x in (d.x0,) for L in (d.Lf, d.Lr))
        self.assertAlmostEqual(bb.zmax, top, places=4)

    def test_15in6_deck_window_opens_over_the_pi(self):
        """Every point of the Pi's footprint behind the raised block sees through
        the window; the band in front of it is under solid plate, which the
        block bears on."""
        d = enclosure.s16_deck()
        deck = self.parts['segno_monitor_deck']
        u0, u1, v0, v1 = enclosure.pi_pcb_extent()
        w = (d.w_top + d.w_bot) / 2.0
        open_points = solid_points = 0
        for x in (u0 + 1.0, (u0 + u1) / 2.0, u1 - 1.0):
            for L in [d.win[2] + 4.0 + 2.0 * k for k in range(int((d.win[3] - d.win[2] - 8.0) / 2.0))]:
                self.assertFalse(deck.isInside(cq.Vector(*d.world(x, L, w))), (x, L))
                open_points += 1
            for L in (d.plane_L(w, v0), d.win[2] - 1.0):
                self.assertTrue(deck.isInside(cq.Vector(*d.world(x, L, w))), (x, L))
                solid_points += 1
        self.assertGreater(open_points, 50)

    def test_15in6_monitor_screws_are_fixed_and_the_washer_bears_all_round(self):
        """#1070: no float at the monitor. The two VESA holes are M4 clearance,
        75 mm apart, now in the aluminium deck, and an M4 DIN 125 washer (O9)
        covers either one fully even with the screw pushed to the side."""
        d = enclosure.S16_VESA_CLR_D
        self.assertLessEqual(d, 4.8 + 1e-9)
        self.assertGreater(9.0 / 2.0, d / 2.0 + (d - 4.0) / 2.0)
        deck = self.parts['segno_monitor_deck']
        xs = sorted({round(BRepAdaptor_Surface(f.wrapped).Cylinder().Location().X(), 2)
                     for f in deck.Faces() if f.geomType() == 'CYLINDER'
                     and abs(BRepAdaptor_Surface(f.wrapped).Cylinder().Radius() - d / 2.0) < 1e-6})
        self.assertEqual(len(xs), 2, xs)
        self.assertAlmostEqual(xs[1] - xs[0], enclosure.S16_VESA, delta=0.05)

    def test_15in6_pads_clamp_the_plate_and_meet_the_flat_back(self):
        """Each pad sits on the plate over its tower and reaches the monitor's
        flat back; its two screws pass the plate on the tower's insert axes."""
        dk = enclosure.s16_deck()
        deck = self.parts['segno_monitor_deck']
        monitor = self.parts['segno_screen16_monitor']
        pad = self.parts['segno_screen16_pad']
        dx = dk.towers[1][0] - dk.towers[0][0]
        for side, part in (('L', pad), ('R', pad.translate((dx, 0, 0)))):
            self.assertLess(part.intersect(deck).Volume(), 1e-6)
            self.assertLess(part.distance(deck), 1e-6)
            self.assertLess(part.intersect(monitor).Volume(), 1e-6)
            self.assertLess(part.distance(monitor), 1e-6)
            stand = self.parts['segno_screen16_stand_' + side]
            t0, t1 = dk.towers[0 if side == 'L' else 1]
            for x, L in dk.screws:
                if not t0 < x < t1:
                    continue
                # a screw axis along the deck normal: clear through pad and plate,
                # then into the tower's insert pilot
                for w in (dk.w_top + 1.0, (dk.w_top + dk.w_bot) / 2.0):
                    p = cq.Vector(*dk.world(x, L, w))
                    self.assertFalse(part.isInside(p) or deck.isInside(p), (side, x, w))
                p = cq.Vector(*dk.world(x, L, dk.w_bot - enclosure.INSERT_DEPTH + 0.5))
                self.assertFalse(stand.isInside(p), (side, x))
                ring = cq.Vector(*dk.world(x + enclosure.INSERT_PILOT_D / 2.0 + 1.0, L,
                                           dk.w_bot - 1.0))
                self.assertTrue(stand.isInside(ring), (side, x))

    # --- fit tests -----------------------------------------------------------

    def test_7in_deck_fit_test_has_the_towers_bosses_and_notch(self):
        """The jig is only useful if its bosses are the tower's: same diameter,
        height above the deck, insert pilot and screw clearance."""
        jig = self.parts['segno_screen7_deck_fit_test']
        self.assertTrue(jig.isValid())
        self.assertEqual(len(jig.Solids()), 1)
        dt = enclosure.S7T_DECK
        top = dt + (enclosure.S7C_MOD_DEPTH + enclosure.S7C_GAP
                    - enclosure.S7C_GLASS_TO_TABF - enclosure.S7C_TAB_T
                    - enclosure.SCREEN_COATED_SETBACK)
        self.assertAlmostEqual(jig.BoundingBox().zmax, top, places=6)
        for x, y in enclosure.S7C_HOLES:
            pilot = (cq.Workplane('XY').workplane(offset=top).center(x, y)
                     .circle(enclosure.S7T_INSERT_D / 2 - .01)
                     .extrude(-enclosure.S7T_INSERT_L + .01).val())
            clear = (cq.Workplane('XY').center(x, y)
                     .circle(enclosure.S7T_SCREW_CLR / 2 - .01).extrude(top).val())
            ring = (cq.Workplane('XY').workplane(offset=top - .1).center(x, y)
                    .circle(enclosure.S7T_BOSS_D / 2 - .01)
                    .circle(enclosure.S7T_INSERT_D / 2 + .01).extrude(.1).val())
            self.assertLess(jig.intersect(pilot).Volume(), 1e-7)
            self.assertLess(jig.intersect(clear).Volume(), 1e-7)
            self.assertLess(ring.cut(jig).Volume(), 1e-7)
        # the connector notch goes through the +x edge
        py = sum(enclosure.S7C_PORTS_Y) / 2.0
        self.assertFalse(jig.isInside(cq.Vector(88.0, py, dt / 2.0)))
        self.assertTrue(jig.isInside(cq.Vector(88.0, -40.0, dt / 2.0)))

    # --- both: floor interface ---------------------------------------------

    def test_shim_kit_is_binary_and_nominal_matches_the_lift(self):
        kit = enclosure.STAND_SHIM_SET
        stacks = {round(sum(c), 3) for r in range(len(kit) + 1)
                  for c in itertools.combinations(kit, r)}
        self.assertEqual(stacks, {round(0.2 * i, 3) for i in range(16)})
        self.assertAlmostEqual(sum(enclosure.STAND_SHIM_NOMINAL), enclosure.STAND_SHIM_NOM)
        # the nominal stack leaves room to go down as well as up
        self.assertGreaterEqual(enclosure.STAND_SHIM_NOM, 0.8)
        self.assertGreaterEqual(sum(kit) - enclosure.STAND_SHIM_NOM, 1.6)

    def test_each_shim_is_its_flange_footprint(self):
        """Stacked at nominal, the shims fill the gap under the flange exactly:
        touching it, never overlapping it, and covering its whole underside."""
        for stem, part, z0 in (('segno_screen7_shim', self.tower, 0.0),
                               ('segno_screen16_shim', self.parts['segno_screen16_stand_L'],
                                enclosure.FLOOR_TOP)):
            flange_area = sum(f.Area() for f in part.Faces()
                              if f.geomType() == 'PLANE' and f.normalAt().z < -.99999
                              and abs(f.Center().z - z0 - enclosure.STAND_SHIM_NOM) < 1e-6)
            z = z0
            for t in enclosure.STAND_SHIM_NOMINAL:
                shim = self.parts[f"{stem}_{str(t).replace('.', 'p')}"].translate((0, 0, z - z0))
                self.assertAlmostEqual(shim.Volume() / t, flange_area, places=3)
                self.assertLess(shim.intersect(part).Volume(), 1e-6)
                z += t
            self.assertLess(shim.distance(part), 1e-6)
            for t in enclosure.STAND_SHIM_SET:
                self.assertIn(f"{stem}_{str(t).replace('.', 'p')}", self.parts)


if __name__ == '__main__':
    unittest.main()
