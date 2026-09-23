#!/usr/bin/env bash
# NATIVE run of the author glare_demo (J. R. Frisvad, DTU 2009; build: build_glare_demo.sh) on its own
# bundled example (glare/candle.png + glare/overlay.png) under Xvfb + Mesa llvmpipe.
# Frames are grabbed from the X root window with `xwd` at a fixed wall-clock interval with timestamps.
#
# RUNTIME WORKAROUND (documented, no source change): FFT::FFT() calls init_display_lists(0) before
# size[1] is assigned (FFT.cpp constructor loop), so the dimension-0 butterfly quads are compiled with an
# UNINITIALISED height. On 2009 Windows/MSVC the heap garbage happened to be large (reference screenshot
# https://people.compute.dtu.dk/jerf/code/images/glare_demo.png shows full glare); with glibc it is 0 and
# the PSF is black. We make the uninitialised heap bytes deterministic and large with glibc's own
# tunables (tcache off so every allocation is perturbed; fill byte 0xFE -> size[1] = 4278124286), which
# makes the dimension-0 quads cover the whole 512x512 viewport, as intended by the author.
#
# LIBGL_SHOW_FPS=1 makes Mesa print the swap rate once per second (one swap per simulate() step of
# 20 ms simulated hippus time), which gives the simulated time base of the captured frames.
# Usage: run_glare_demo_native.sh <outdir> <mode: glare|psf> [seconds] [interval_s]
#   glare = default view (image + glare convolution);  psf = after pressing the demo's own 'c' key
#   (convolution off -> tone-mapped PSF itself, as in the left panel of the reference screenshot).
set -euo pipefail
export PATH=/nix/var/nix/profiles/default/bin:$PATH NIX_SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
REPO=/home/user/human-night-perception-experiments
BIN=$REPO/research-cache/temporal-glare-2009/build/glare_demo
SRC=$REPO/research-cache/temporal-glare-2009/glare_demo/glare   # unmodified example images
OUTDIR=${1:?outdir}; MODE=${2:?mode}; SECS=${3:-60}; DT=${4:-0.25}
mkdir -p "$OUTDIR/xwd"; rm -f "$OUTDIR/timestamps.txt"
cd "$REPO"
MESA=$(nix build --inputs-from . --no-link --print-out-paths nixpkgs#mesa | sed -n 1p)
cat > "$OUTDIR/inner.sh" <<INNER
set -e
cd "$SRC"
LIBGL_SHOW_FPS=1 GLIBC_TUNABLES=glibc.malloc.tcache_count=0:glibc.malloc.perturb=1 nice -n 10 "$BIN" candle.png overlay.png > "$OUTDIR/glare_demo_stdout.txt" 2>&1 &
PID=\$!
sleep 8
W=\$(xdotool search --name "Glare demo" | head -1)
if [ "$MODE" = psf ]; then xdotool key --window \$W c; sleep 3; fi
T0=\$(date +%s.%N); i=0
while :; do
  NOW=\$(date +%s.%N)
  awk -v a=\$NOW -v b=\$T0 -v s=$SECS 'BEGIN{exit !(a-b<s)}' || break
  f=\$(printf "%05d" \$i)
  xwd -root -silent -out "$OUTDIR/xwd/\$f.xwd"
  echo "\$f \$NOW" >> "$OUTDIR/timestamps.txt"
  i=\$((i+1)); sleep $DT
done
ps -o pid,etime,time -p \$PID >> "$OUTDIR/glare_demo_stdout.txt" || echo "glare_demo died" >> "$OUTDIR/glare_demo_stdout.txt"
kill \$PID || true
INNER
nix shell --inputs-from . nixpkgs#xvfb-run nixpkgs#xwd nixpkgs#xdotool nixpkgs#ffmpeg-headless -c bash -c "
export __GLX_VENDOR_LIBRARY_NAME=mesa GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=2
export LIBGL_DRIVERS_PATH=$MESA/lib/dri LD_LIBRARY_PATH=$MESA/lib
xvfb-run -a -s '-screen 0 512x512x24 +extension GLX' bash $OUTDIR/inner.sh
mkdir -p $OUTDIR/png
ffmpeg -loglevel error -y -i $OUTDIR/xwd/%05d.xwd $OUTDIR/png/%05d.png && rm -rf $OUTDIR/xwd
"
wc -l "$OUTDIR/timestamps.txt"
