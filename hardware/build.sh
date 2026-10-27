#!/usr/bin/env bash
# Builds every generated output under hardware/ from the Python sources:
# the enclosure's STEP/DXF/PDF/STL files and vendor archives, the strip ring,
# the pill housings, the decals and the ring diffuser. CI runs this on every
# PR and on fab-* tags (.github/workflows/outputs.yaml).
#
# Usage: hardware/build.sh [python]
#   python defaults to hardware/enclosure/.venv/bin/python, else python3.
#   Create the environment with hardware/enclosure/requirements.txt.
#
# The decals use macOS system fonts (Apple Chancery, Helvetica Neue), so a
# full build runs on macOS. The KiCad boards are not built here: they need
# KiCad and Freerouting, and their routed boards and Gerbers stay tracked.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
py="${1:-}"
if [ -z "$py" ]; then
  if [ -x "$here/enclosure/.venv/bin/python" ]; then
    py="$here/enclosure/.venv/bin/python"
  else
    py=python3
  fi
fi

run() { echo "== $1: ${*:2}"; (cd "$here/$1" && "$py" "${@:2}"); }

run enclosure segno_enclosure.py
run enclosure _pedal_base_fit_test.py
run enclosure _pedal_base_gauge.py
run strip_ring console_ring.py
run pill_light_mask tall_pill.py
run pill_light_mask top_mount.py
run pill_light_mask preview.py
run pill_light_mask top_mount_preview.py
run decals decals.py
run ring_diffuser ring16_diffuser.py
run ring_diffuser ring16_diffuser.py --skirt-only
