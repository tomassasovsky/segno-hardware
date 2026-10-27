# segno-hardware

The physical parts of [Segno](https://github.com/tomassasovsky/segno), the
looper floor console: the circuit boards, the sheet-metal enclosure, the
printed parts inside it, the decals, and the documents for buying, building
and wiring one unit. [`hardware/README.md`](hardware/README.md) describes the
current design and every folder; [`hardware/MANUFACTURING.md`](hardware/MANUFACTURING.md)
is the manufacturing package.

The history was extracted from `tomassasovsky/segno` with git-filter-repo,
from every branch that changed `hardware/`. Issue and PR references in commit
messages (`#123`) were rewritten to `tomassasovsky/segno#123`, because those
numbers belong to that repository; issues for this work stay there.

## Layout

| Path | Contents |
| --- | --- |
| `hardware/enclosure/` | The parametric enclosure generator (`segno_enclosure.py`, cadquery), its tests, the Fusion 360 documents (`fusion/`) and the parts exported from them (`formed/`). |
| `hardware/kicad/` | Board sources (SKiDL netlists, `pcbnew` layout scripts), the routed boards and Gerbers (`out_console/`, `out_ring/`), the screen power board (`screen_power/`) and the archives sent to the board house (`fab/`). |
| `hardware/strip_ring/`, `pill_light_mask/`, `ring_diffuser/`, `decals/` | Generators for the LED strip ring, the indicator pill housings, the ring diffuser and the vinyl decals. |
| `hardware/v3_soldering/`, `bench/`, `console/`, `led_strip/`, `switch_mount/` | Solder-order guides, bench tests, console notes and older parts. |
| `hardware/build.sh` | Builds every generated output. |

## Building the outputs

The cadquery outputs are not tracked. To build them locally (macOS, because
the decals use macOS system fonts):

```sh
python3.12 -m venv hardware/enclosure/.venv
hardware/enclosure/.venv/bin/pip install -r hardware/enclosure/requirements.txt
hardware/build.sh
```

The files land in `out/` (or `out_console/`) next to each generator. The
KiCad scripts need KiCad's own Python and Freerouting; see
[`hardware/kicad/README.md`](hardware/kicad/README.md). Their routed boards,
Gerbers and fabrication archives stay tracked, as do the Fusion 360 documents
and their exports.

## Where fabrication files live

- **Pull requests:** CI builds and checks every output and uploads them as the
  `hardware-outputs` artifact on the run's summary page.
- **Releases:** an order is frozen by pushing a `fab-*` tag on the commit it
  was built from. CI rebuilds the outputs and attaches them, with a
  `SHA256SUMS` file, to a GitHub release named after the tag. The release is
  the record of what was sent.

```sh
git tag fab-2026-10-27-metal
git push origin fab-2026-10-27-metal
```

## What stays in Segno

The firmware for the console board and the ring carrier, and the pedal link
contract between the firmware and the app, stay in
[`tomassasovsky/segno`](https://github.com/tomassasovsky/segno) under
`firmware/`, where the app's CI tests them together. A change that touches a
board's pin map or the pedal link needs a PR in each repository, linked to
each other.

## License

GPL-3.0-or-later, the same as Segno. See [`LICENSE`](LICENSE). Some files
under `hardware/kicad/screen_power/` carry third-party terms for material
from the KiCad libraries, and `hardware/kicad/fonts/` holds JetBrains Mono
under the SIL Open Font License.
