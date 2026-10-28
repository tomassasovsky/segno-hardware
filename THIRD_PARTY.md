# Third-party material

The files below are not covered by this repository's CERN-OHL-S-2.0
licence. Each keeps the licence of its source. The routed boards, the board
STEP exports (`hardware/kicad/out_*/*.step`) and the Fusion 360 document place
these parts in the design and include their geometry; that geometry keeps the
same terms. The KiCad libraries' exception, quoted in
[`LIBRARY_LICENSE.txt`](hardware/kicad/screen_power/LIBRARY_LICENSE.txt),
lets designs and generated files use library material without taking on
CC-BY-SA-4.0.

## KiCad libraries

Licence: CC-BY-SA-4.0 with the KiCad library exception, unless the file's own
header says otherwise. Sources:
[kicad-footprints](https://gitlab.com/kicad/libraries/kicad-footprints) and
[kicad-packages3D](https://gitlab.com/kicad/libraries/kicad-packages3D).

| File | Source |
| --- | --- |
| `hardware/kicad/screen_power/models/C_Disc_D7.5mm_W4.4mm_P5.00mm.step` | `Capacitor_THT.3dshapes`. Its header grants GPL-3.0-or-later (copyright 2017, kicad StepUp). |
| `hardware/kicad/screen_power/models/D_DO-15_P10.16mm_Horizontal.step`, `D_DO-41_SOD81_P10.16mm_Horizontal.step` | `Diode_THT.3dshapes` |
| `hardware/kicad/screen_power/models/JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical.step`, `JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical.step` | `Connector_JST.3dshapes` |
| `hardware/kicad/screen_power/models/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step` | `Resistor_THT.3dshapes` |
| `hardware/kicad/screen_power/models/TO-220-3_Vertical.step`, `TO-92_Inline_Wide.step` | `Package_TO_SOT_THT.3dshapes` |
| `hardware/kicad/screen_power/models/licenses/` | The libraries' credit files for the models above |
| `hardware/kicad/screen_power/screen_power.pretty/Fuseholder_Schurter_OGN_0031.8201.kicad_mod` | Adapted from `Fuse:Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open` |
| `hardware/kicad/screen_power/screen_power.pretty/Relay_DPDT_AXICOM_IMSeries_Pitch5.08mm_D0.90mm.kicad_mod` | Adapted from `Relay_THT:Relay_DPDT_AXICOM_IMSeries_Pitch5.08mm` |
| `hardware/kicad/screen_power/screen_power.pretty/TO-220-3_IRLZ44N.kicad_mod` | Adapted from `Package_TO_SOT_THT:TO-220-3_Vertical` |
| `hardware/kicad/segno.pretty/RaspberryPi_Pico_SMD_or_THT_Debug.kicad_mod` | Adapted from `Module:RaspberryPi_Pico_SMD_HandSolder` and `Module:RaspberryPi_Pico_Common_THT` |

Our changes to the adapted footprints are shared under the same terms, as
CC-BY-SA-4.0 requires.

## Seeed Studio XIAO RP2350

| File | Source | Licence |
| --- | --- | --- |
| `hardware/kicad/segno.pretty/XIAO_RP2350_SMD.kicad_mod` | [Seeed-Studio/OPL_Kicad_Library](https://github.com/Seeed-Studio/OPL_Kicad_Library), `Seeed Studio XIAO Series Library/XIAO-RP2350-SMD.kicad_mod`, with the footprint name changed | CC-BY-SA-4.0 |
| `hardware/kicad/segno.pretty/XIAO_Module.step` | [Tircown/ERCF-easy-brd](https://github.com/Tircown/ERCF-easy-brd), `Kicad/ercf-easy-brd.pretty/packages3d/Seeeduino Xiao.step` | GPL-3.0, text in [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt) |

## Adafruit NeoPixel rings

| File | Source |
| --- | --- |
| `hardware/kicad/segno.pretty/NeoPixel_Ring16.step` | [adafruit/Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts), `1463 16x NeoPixel Ring` |
| `hardware/kicad/segno.pretty/NeoPixel_Ring24.step` | [adafruit/Adafruit_CAD_Parts](https://github.com/adafruit/Adafruit_CAD_Parts), `1586 NeoPixel Ring 24x` |

Licence: MIT, reproduced from the source repository.

```text
MIT License

Copyright (c) 2016 Adafruit Industries

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Fonts

`hardware/kicad/fonts/JetBrainsMono-Regular.ttf` is JetBrains Mono, under the
SIL Open Font License 1.1 in
[`OFL-JetBrainsMono.txt`](hardware/kicad/fonts/OFL-JetBrainsMono.txt).

## Seller drawings

`hardware/enclosure/reference/buck_dimensions.png` and
`hardware/enclosure/reference/usb3_dimensions.png` are dimension drawings
copied from the sellers' product listings for the buck converter and the
panel-mount USB 3 socket. They are kept as the reference the enclosure was
measured against. They are not ours, and no licence is granted for them.
