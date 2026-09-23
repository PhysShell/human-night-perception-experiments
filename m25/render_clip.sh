#!/usr/bin/env bash
# M2.5: render one clip of the frozen M2 scene as two passes (m1/scene.py, M25_*):
#   haze_####.exr   everything except the camera-visible lamp spheres   (HAZE_SPP, fixed)
#   lamps_####.exr  lamp spheres through the same extinction, enlarged to 0.7 px at
#                   constant intensity, see-through; rendered at 4x resolution with a box
#                   filter, 256 spp (= 4096 per output pixel, fixed, no adaptive sampling),
#                   only in the image band that contains lamps, then resampled with
#                   Cycles' own Blackman-Harris 1.5 px filter (m25/resample.py)
#   occ_####.exr    test aid only: white poplars on black (where a lamp may truly blink)
# haze + lamps is the one-pass render (m25/test_decomposition.py). Camera: eye height, walking
# along +x at WALK m/s (0 = static; one frame is rendered and repeated by the display step).
#   m25/render_clip.sh OUTDIR FRAMES WALK [HAZE_SPP=32] [SEED=0] [ATMOSPHERE=clear] [FPS=24]
set -euo pipefail
OUT=$1 FRAMES=$2 WALK=$3 HAZE_SPP=${4:-32} SEED=${5:-0} ATM=${6:-clear} FPS=${7:-24} DENOISE=${M25_DENOISE:-0}
mkdir -p "$OUT"
[ "$WALK" = 0 ] && FRAMES=1
common=(M2_HALF_RES=1 M25_FRAMES="$FRAMES" M25_WALK="$WALK" M25_FPS="$FPS" M25_SEED="$SEED" M25_DENOISE="$DENOISE")
S=$SECONDS
env "${common[@]}" M25_PASS=haze blender -b --factory-startup --python m1/scene.py -- \
  "$OUT/haze_####" "$HAZE_SPP" "$ATM" > "$OUT/haze.log" 2>&1
echo "haze: $FRAMES frames, $((SECONDS - S)) s"; S=$SECONDS
env "${common[@]}" M25_PASS=lamps M25_LAMP_PX=0.7 M25_SS=4 blender -b --factory-startup --python m1/scene.py -- \
  "$OUT/lampshr_####" 256 "$ATM" > "$OUT/lamps.log" 2>&1
for f in "$OUT"/lampshr_*.exr; do echo "$f" "${f/lampshr_/lamps_}"; done | xargs python3 m25/resample.py 4
rm -f "$OUT"/lampshr_*.exr
env "${common[@]}" M25_PASS=occluders blender -b --factory-startup --python m1/scene.py -- \
  "$OUT/occ_####" 16 "$ATM" > "$OUT/occ.log" 2>&1       # test aid: poplar mask (check_clip.py)
echo "lamps: $FRAMES frames, $((SECONDS - S)) s"
printf "frames=%s walk=%s fps=%s haze_spp=%s seed=%s atmosphere=%s denoise=%s\n" "$FRAMES" "$WALK" "$FPS" "$HAZE_SPP" "$SEED" "$ATM" "$DENOISE" > "$OUT/clip.txt"
