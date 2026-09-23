#!/usr/bin/env bash
# M2.5: viewing copies of the clips for people (the lossless clip.mp4 files are for metrics).
#   full   960x410, H.264 4:4:4 CRF 8 (near-lossless on these dark frames), both displays
#   crop   left half of the ribbon (near lamps, poplars) 2x nearest-neighbour, so that the
#          sub-pixel behaviour is visible on a phone; watching it magnified changes the
#          viewing condition (32 px/deg instead of 16), so judge the full clip first
#   m25/export_view.sh [indir=m25/out] [outdir=docs/m25-results]
set -euo pipefail
I=${1:-m25/out} O=${2:-docs/m25-results}
mkdir -p "$O"
enc() { ffmpeg -loglevel error -y -i "$1" "${@:3}" -c:v libx264 -pix_fmt yuv444p -profile:v high444 -crf 8 -preset slow "$2"; }
for c in A_static B_walk; do
  for v in clip clip_pbr; do
    [ -f "$I/$c/$v.mp4" ] || continue
    tag=${v/clip/}; tag=${tag:-_clipgamut}
    enc "$I/$c/$v.mp4" "$O/${c}${tag}.mp4"
    enc "$I/$c/$v.mp4" "$O/${c}${tag}_crop2x.mp4" -vf "crop=480:110:0:145,scale=960:220:flags=neighbor"
  done
done
ls -la "$O"
