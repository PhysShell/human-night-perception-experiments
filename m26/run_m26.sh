#!/usr/bin/env bash
# M2.6 sampling-density test. The first 2 s (48 frames) of clip B (walk 1 m/s, clear), same
# scene, path and frozen stack, rendered at 16 / 32 / 64 px/deg of the 60 deg view (960,
# 1920, 3840 px wide), then every version brought to ONE target display (1920 x 820, see
# m26/display_models_m26.json) with a proper filter. 16 px/deg = the M2.5 frames themselves;
# 32 and 64 render only the near half of the ribbon (M26_CROP) at full density and take the
# rest from the 16 px/deg frames (m26/composite.py).
# Stack per frame, ORDER=render (first run): haze + lamps -> pcond LC at the RENDER resolution
# -> resample to the target -> PBR Neutral on out-of-gamut pixels (the warm stills display,
# preferred by the viewer in M2.5) -> sRGB PNG -> lossless clip. This clips each lamp's core
# at the render pixel, so the finer the render, the more energy is thrown away above white
# before the target is formed: it cannot converge (measured: lamps dimmer and smaller at 64).
# ORDER=target (default): scene radiance resampled to the target display FIRST (a display
# pixel is the physical emitter: it shows the scene integrated over its own area), then pcond
# at the target resolution, then the same display step. Output in p<P>_t/.
#   [ORDER=target|render] nix develop -c m26/run_m26.sh
set -euo pipefail
O=${O:-m26/out}; B=m25/out/B_walk; N=${N:-48}; TW=1920; TH=820; CROP=0,0.5,0.44,0.62
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
mkdir -p "$O/occ"
common=(M25_FRAMES=240 M25_WALK=1 M25_FPS=24 M25_START=1 M25_END=$N)
# poplar mask at the target (for m25/check_clip.py and m25/analyse_clip.py)
[ -f "$O/occ/occ_$(printf %04d $N).exr" ] || env "${common[@]}" M26_RES=$TW,$TH M25_PASS=occluders \
  blender -b --factory-startup --python m1/scene.py -- "$O/occ/occ_####" 16 clear > "$O/occ.log" 2>&1
ORDER=${ORDER:-target}
for P in 16 32 64; do
  D=$O/p$P; SRC=$D; [ "$ORDER" = target ] && D=$O/p${P}_t; W=$((60 * P)); H=$(( (W * 410 + 480) / 960 )); mkdir -p "$SRC/src" "$D/lc" "$D/png_pbr"
  if [ $P != 16 ] && [ ! -f "$SRC/src/lampshr_done" ]; then
    SPP=$([ $P = 64 ] && echo 128 || echo 256)
    S=$SECONDS
    env "${common[@]}" M26_RES=$W,$H M26_CROP=$CROP M25_PASS=haze blender -b --factory-startup \
      --python m1/scene.py -- "$SRC/src/hazehr_####" 32 clear > "$SRC/haze.log" 2>&1
    echo "p$P haze: $((SECONDS - S)) s"; S=$SECONDS
    env "${common[@]}" M26_RES=$W,$H M26_CROP=$CROP M25_PASS=lamps M25_LAMP_PX=0.7 M25_SS=4 blender -b \
      --factory-startup --python m1/scene.py -- "$SRC/src/lampsss_####" $SPP clear > "$SRC/lamps.log" 2>&1
    for f in "$SRC"/src/lampsss_*.exr; do echo "$f" "${f/lampsss_/lampshr_}"; done | xargs python3 m25/resample.py 4
    rm -f "$SRC"/src/lampsss_*.exr; touch "$SRC/src/lampshr_done"
    echo "p$P lamps: $((SECONDS - S)) s"
  fi
  export D SRC P W H TW TH CROP B CFG ORDER
  frame() {
    local f=$1 t; t=$(mktemp -d)
    if [ "$P" = 16 ]; then cp "$B/haze_$f.exr" "$t/haze.exr"; cp "$B/lamps_$f.exr" "$t/lamps.exr"
    else python3 m26/composite.py $W $H $CROP "$B/haze_$f.exr" "$B/lamps_$f.exr" "$SRC/src/hazehr_$f.exr" \
           "$SRC/src/lampshr_$f.exr" "$t/haze.exr" "$t/lamps.exr"; fi
    python3 m26/to_target.py $TW $TH "$t/haze.exr" "$D/haze_$f.exr" "$t/lamps.exr" "$D/lamps_$f.exr"
    if [ "$ORDER" = target ]; then oiiotool "$D/haze_$f.exr" "$D/lamps_$f.exr" --add -o "$t/sum.exr"
    else oiiotool "$t/haze.exr" "$t/lamps.exr" --add -o "$t/sum.exr"; fi
    m1/pcond_colorimetric.sh "$t/sum.exr" 60 LC "$t/lc.hdr" 1 2>/dev/null
    echo "$f $(getinfo < "$t/lc.pcond.hdr" | sed -nE 's/.*EXPOSURE= *([0-9.eE+-]+).*/\1/p' | head -1)" > "$D/lc/$f.expo"
    oiiotool "$t/lc.hdr" -o "$t/lc.exr"
    python3 m26/to_target.py $TW $TH "$t/lc.exr" "$D/lc/$f.exr"
    local l="$D/lc/$f.exr"
    oiiotool "$l" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
    oiiotool --colorconfig "$CFG" "$l" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint8 -o "$t/std.png"
    oiiotool --colorconfig "$CFG" "$l" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint8 -o "$t/pbr.png"
    oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint8 -o "$D/png_pbr/$f.png"
    rm -rf "$t"; }
  export -f frame
  seq -f %04g 1 $N | xargs -P "$(nproc)" -I{} bash -c 'frame {}'
  cat "$D"/lc/*.expo > "$D/exposure.txt"
  for f in $(seq -f %04g 1 $N); do ln -sf "../occ/occ_$f.exr" "$D/occ_$f.exr"; done
  ffmpeg -loglevel error -y -framerate 24 -i "$D/png_pbr/%04d.png" -c:v libx264rgb -crf 0 -preset veryslow "$D/clip_pbr.mp4"
  echo "p$P done: $(cut -d' ' -f2 "$D/exposure.txt" | sort -u | tr '\n' ' ')"
done
