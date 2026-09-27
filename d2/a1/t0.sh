#!/usr/bin/env bash
# T0 driver (d2/a1/PREREG_T0.md): build -> frozen A + extraction on the modified input -> eval (C1/C2/presence), per variant.
set -euo pipefail
export PATH=/root/.nix-profile/bin:$PATH
for V in atm glare25 glare70; do
  tracks/temporal-glare-2009/py.sh d2/a1/t0.py build $V
  nix develop -c d1/pipeline/axis_a.sh d2/a1/work/T0/${V}_cdm2.exr 60 d1/pipeline/.cache/A/T0_${V}.exr
  nix develop -c d1/a_extract/axis_a_x.sh d2/a1/work/T0/${V}_cdm2.exr 60 d1/a_extract/.cache/T0_${V}
  tracks/temporal-glare-2009/py.sh d2/a1/t0.py eval $V
done
