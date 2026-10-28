# Hardware

The physical parts of the Segno floor console: the printed circuit boards, the
sheet-metal enclosure, the printed parts that sit inside it, the decals, and
the documents that describe how to buy, build and wire one unit.

Most of this folder is generated. Python scripts produce the KiCad boards
(SKiDL for netlists, KiCad's own `pcbnew` Python module for layout) and the
mechanical parts (cadquery). When a generator and its output disagree, the
generator is the source; regenerate rather than editing the output.

The cadquery outputs (STEP, DXF, PDF, STL and the vendor archives under
`enclosure/out/`, `strip_ring/out_console/`, `pill_light_mask/out/`,
`decals/out/` and `ring_diffuser/out/`) are not tracked. `build.sh` builds
them; CI runs it on every PR and uploads the result as the `hardware-outputs`
artifact, and a `fab-*` tag attaches the same files to a GitHub release. The
KiCad boards, their Gerbers and `kicad/fab/` stay tracked: the routed boards
come from Freerouting, which does not reproduce a layout, and `kicad/fab/`
holds the archives that were sent to the board house. The Fusion 360
documents and the parts exported from them (`enclosure/fusion/`,
`enclosure/formed/`) also stay tracked.

The firmware for the boards, and the pedal link contract it shares with the
app, are in the Segno repository:
[`firmware/`](https://github.com/tomassasovsky/segno/blob/claude/segno-integration/firmware/README.md).

## Current design

The current console uses three boards and one enclosure revision. The
[manufacturing package](MANUFACTURING.md) is the reference for what to order:

| Part | Revision | Source |
| --- | --- | --- |
| Console board | v3, Pico 2 (RP2350) on the Pi's 40-pin header | [`kicad/console_board.py`](kicad/console_board.py), [`kicad/console_board_pcb.py`](kicad/console_board_pcb.py) |
| Ring carrier | XIAO RP2350, encoder and LED ring, white solder mask | [`kicad/ring_board.py`](kicad/ring_board.py), [`kicad/segno_pedal_ring.kicad_pcb`](kicad/segno_pedal_ring.kicad_pcb) |
| Screen power board | Revision P | [`kicad/screen_power/`](kicad/screen_power/README.md) |
| Enclosure | 2026-09-30 integrated revision | [`enclosure/segno_enclosure.py`](enclosure/segno_enclosure.py) |

The console board v2 is superseded by v3. Some documents written before the
change still call the console board "v2". The enclosure's fabrication release is
on hold pending the sheet-metal shop's tooling acceptance and a separate
structural assessment (#1019); [`enclosure/RELEASE_REVIEW.md`](enclosure/RELEASE_REVIEW.md)
lists the open items.

## Documents

| File | Contents |
| --- | --- |
| [`MANUFACTURING.md`](MANUFACTURING.md) | The manufacturing package for one console: the metal parts and their shops, 3D-printed parts, engraved pedal tiles, vinyl decals, PCBs, purchased parts and the screw and insert schedule. Start here to build or order anything. |
| [`segno_wiring.md`](segno_wiring.md) | System wiring: the block diagram, the 20 V USB-C power input and its two 5 V converters, the console board's internal cables, the Raspberry Pi connections, the rear panel and grounding. |
| [`segno_console_shopping_list.md`](segno_console_shopping_list.md) | Per-console bill of materials with local (Argentina) sourcing notes: compute and displays, audio, foot controls, LEDs, power, boards and mechanical parts. |
| [`segno_enclosure_design.md`](segno_enclosure_design.md) | Design notes for the sheet-metal enclosure: overall geometry, pedal platforms, faceplate layout, rear I/O, internal mounting, material, and the generator's assertion checks. |
| [`segno_console_board_v2_soldering_guide.md`](segno_console_board_v2_soldering_guide.md) | Hand-assembly guide for the console board v2, with [an illustration](segno_console_board_v2_soldering_guide.png). The v2-specific parts are historical; for the v3 boards use [`v3_soldering`](v3_soldering/README.md). |

## Folders

### [`kicad`](kicad/README.md)

The board sources. SKiDL scripts emit the netlists (`console_board.py`,
`ring_board.py`), and `pcbnew` scripts place, route and check the boards.
`segno.pretty/` holds the few footprints KiCad does not ship.
[`RING_ASSEMBLY.md`](kicad/RING_ASSEMBLY.md) and
[`RING_ENCODER.md`](kicad/RING_ENCODER.md) cover the ring carrier's assembly,
order settings and encoder fit. `screen_power/` is the screen power and touch
switch board, a self-contained KiCad project with its own build script.
`fab/` holds the Gerber archives and BOMs that were sent to the board
manufacturer, including earlier screen-power revisions; `out_console/` and
`out_ring/` hold the generated boards and Gerbers. Open the `.kicad_pcb` and
`.kicad_pro` files with KiCad.

### [`v3_soldering`](v3_soldering/README.md)

Solder order for the three current boards (console v3, ring carrier, screen
power Revision P): parts lists, numbered solder-order images and KiCad 3D
renders. `tools/build.sh` regenerates the images from the KiCad boards.

### `enclosure`

The parametric enclosure generator, `segno_enclosure.py` (cadquery). It runs a
set of geometry assertions, then writes STEP, DXF and PDF drawings and STL
print files to `out/`, and assembles the vendor archives. `tests/` holds the
enclosure tests. `formed/` holds the folded parts exported from the Fusion 360
model by `fusion_export_formed.py`, which the generator checks its flat
patterns against. `fusion/Segno_console_populated.f3d` is the populated Fusion
360 assembly. The Markdown files in this folder are working records:

- [`RELEASE_REVIEW.md`](enclosure/RELEASE_REVIEW.md): the evidence and open
  items for the current manufacturing release.
- [`SHOP_REVIEW.md`](enclosure/SHOP_REVIEW.md): internal supplier notes and
  draft messages; nothing in it has been sent.
- [`FUSION_MODELS.md`](enclosure/FUSION_MODELS.md): a dated log of changes to
  the Fusion 360 documents and how to edit them safely.
- [`HANDOFF_1019.md`](enclosure/HANDOFF_1019.md): a point-in-time handoff on
  the enclosure's load and stomp analysis (#1019).

The underscore-prefixed scripts are one-off checks and fit-test jigs, such as
the stomp finite-element runs and the print checks.

### `strip_ring`

`console_ring.py` (cadquery) generates the printed parts of the LED strip ring
that sits under the faceplate around the encoder: the diffuser, the cup that
carries the strip, the encoder retainer, spacer and centre cap, and a bench
faceplate. Outputs are STEP and STL in `out_console/`;
`test_console_ring.py` checks the geometry.

### [`pill_light_mask`](pill_light_mask/README.md)

The housings for the faceplate's indicator pills, each lit by an eight-LED
strip segment: a carrier, a white lens and mounting parts, generated with cadquery as
STEP and STL. [`PLATFORM_MOUNT.md`](pill_light_mask/PLATFORM_MOUNT.md)
describes the friction-fit housing for the printed pedal platforms.
`simulator.html` is a browser preview of the pill animation.

### `decals`

`decals.py` generates the two transfer-cut vinyl decals, the lid logo and the
rear connector labels, as DXF, SVG and PDF at 1:1, plus a cut sheet and
placement templates. `test_decals.py` checks them. Outputs are in `out/`.

### [`console`](console/README.md)

Notes on the console as a whole: power, thermals and how the enclosure, the
board and the Pi fit together.
[`grounding-and-bonding.md`](console/grounding-and-bonding.md) is the
grounding and chassis-bonding scheme. `stusb4500_pdo/` is an Arduino sketch, run from
an Arduino UNO, that reprograms the USB-C power-delivery trigger board when
the console board cannot reach it.

### [`bench`](bench/README.md)

Hardware bench tests that CI cannot run. `midi_din_test.py` runs on the
appliance and checks that the console board's two DIN MIDI sockets carry
exact bytes in both directions.

### [`switch_mount`](switch_mount/README.md)

A printed platform that holds a silent switch inside a Cherub WTB-006
footswitch. It is drawn by hand in Fusion 360; the folder holds its STEP and
STL exports.

### [`ring_diffuser`](ring_diffuser/README.md)

A snap-on diffuser for a 16-pixel NeoPixel ring, used on the bench before the
faceplate existed. Generated by `ring16_diffuser.py` (cadquery). It is not the
console's ring window and does not fit the current ring carrier.

### [`led_strip`](led_strip/README.md)

A single-LED WS2812B indicator board, generated with `pcbnew`. It is not used
by the console, which uses segments cut from a bare LED strip instead; the
design is kept because it is complete.

## Licence

The hardware design is licensed under
[CERN-OHL-S-2.0](../LICENSE). The repository [README](../README.md#licence)
lists the files that keep their own terms: GPL-3.0-or-later software, KiCad,
Seeed and Adafruit library material, a font, and two seller drawings.
