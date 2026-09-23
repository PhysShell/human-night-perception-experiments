#!/usr/bin/env bash
# L4 NATIVE: run the authors' own examples of ColorVideoVDP 0.5.7 (nix .#video) and FovVideoVDP 1.2.2
# (uv venv on the same nix python, --no-deps) from inside their pinned git checkouts, exactly as their
# READMEs say ("execute from the main directory: python examples/ex_<...>.py").
# Run inside:  nix develop .#video -c bash tracks/vdp-metrics/run_native_examples.sh
set -uo pipefail
REPO=$(cd "$(dirname "$0")/../.." && pwd)
RC=$REPO/research-cache/vdp-metrics
OUT=$REPO/results/native/vdp-metrics
mkdir -p "$OUT"
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
# fvvdp examples end with f.show(); plt.waitforbuttonpress(), which blocks forever headless (also under Agg):
# the runner replaces plt.waitforbuttonpress by a no-op; Agg backend + unbuffered output
export MPLBACKEND=Agg PYTHONUNBUFFERED=1
# Both packages read 16-bit PNG through imageio's FreeImage plugin, whose auto-download fails under the
# proxy (Python ssl VERIFY_X509_STRICT); the identical imageio-binaries file is fetched with curl instead:
#   https://raw.githubusercontent.com/imageio/imageio-binaries/master/freeimage/libfreeimage-3.16.0-linux64.so
#   sha256 8ba7be1e5d2bc8ffc94d111cb05f7de3dbbfd4af4d502a54eb22c4708021897c
export IMAGEIO_FREEIMAGE_LIB=$RC/freeimage/libfreeimage-3.16.0-linux64.so
[ -f "$IMAGEIO_FREEIMAGE_LIB" ] || { mkdir -p "$RC/freeimage"; curl -sSL -o "$IMAGEIO_FREEIMAGE_LIB" https://raw.githubusercontent.com/imageio/imageio-binaries/master/freeimage/libfreeimage-3.16.0-linux64.so; }
STAGE=${STAGE:-all}
cd "$RC/cvvdp-src"
if [[ $STAGE == all || $STAGE == cvvdp_py ]]; then
for ex in ex_simple_image ex_hdr_images ex_simple_video; do
  echo "== cvvdp examples/$ex.py" | tee "$OUT/NATIVE_cvvdp_$ex.log"
  nice -n 10 python3 -c "import sys; sys.path[:0]=['.','examples']; import runpy; runpy.run_path('examples/$ex.py', run_name='__main__')" 2>&1 | grep --line-buffered -v Warning | tee -a "$OUT/NATIVE_cvvdp_$ex.log"
done
fi
if [[ $STAGE == all || $STAGE == cvvdp_cli ]]; then
echo "== cvvdp CLI README aliasing example (standard_fhd)" | tee "$OUT/NATIVE_cvvdp_cli_aliasing.log"
nice -n 10 cvvdp --test example_media/aliasing/ferris-*-*.mp4 --ref example_media/aliasing/ferris-ref.mp4 --display standard_fhd --device cpu 2>&1 | tee -a "$OUT/NATIVE_cvvdp_cli_aliasing.log"
fi
cd "$RC/fvvdp-src"
if [[ $STAGE == all || $STAGE == fvvdp ]]; then
PYF=$RC/venv/bin/python
echo "== fvvdp README simple image (pytorch_examples/ex_simple_image.py)" | tee "$OUT/NATIVE_fvvdp_ex_simple_image.log"
nice -n 10 $PYF -c "import sys; sys.path.insert(0,'pytorch_examples'); import matplotlib.pyplot as plt; plt.waitforbuttonpress=lambda *a, **k: None; import runpy; runpy.run_path('pytorch_examples/ex_simple_image.py', run_name='__main__')" 2>&1 | grep --line-buffered -v Warning | tee -a "$OUT/NATIVE_fvvdp_ex_simple_image.log"
echo "== fvvdp README aliasing example (standard_fhd)" | tee "$OUT/NATIVE_fvvdp_cli_aliasing.log"
nice -n 10 $RC/venv/bin/fvvdp --test example_media/aliasing/ferris-*-*.mp4 --ref example_media/aliasing/ferris-ref.mp4 --display standard_fhd --gpu -1 2>&1 | grep --line-buffered -v Warning | tee -a "$OUT/NATIVE_fvvdp_cli_aliasing.log"
echo "== fvvdp pytorch_examples/ex_foveated_video.py" | tee "$OUT/NATIVE_fvvdp_ex_foveated_video.log"
nice -n 10 $PYF -c "import sys; sys.path.insert(0,'pytorch_examples'); import matplotlib.pyplot as plt; plt.waitforbuttonpress=lambda *a, **k: None; import runpy; runpy.run_path('pytorch_examples/ex_foveated_video.py', run_name='__main__')" 2>&1 | grep --line-buffered -v Warning | tee -a "$OUT/NATIVE_fvvdp_ex_foveated_video.log"
fi
