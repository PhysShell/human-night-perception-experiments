#!/usr/bin/env bash
# T2 diagnostic report (NOT a gate), modelled on Blender's render-test HTML report:
# reference / current / |difference| x8 / LDR-FLIP of the displayed image / HDR-FLIP of the
# scene radiance, for the golden cases, plus two "what a visible change looks like" pairs.
#
#   t2/report.sh [current_dir=t2/out/golden] [report_dir=t2/out/report]
#
# FLIP (NVlabs, nixpkgs flip 1.2) answers "would an observer notice this difference when
# flipping between the two images?" (default: 67 pixels/degree, 0.7 m from a 0.7 m 4K display).
# It does not say which image is more realistic, and here there is no ground-truth image of
# the scene, so it only characterises changes against the frozen baseline.
set -euo pipefail
CUR=$(realpath "${1:-t2/out/golden}"); REP=$(realpath -m "${2:-t2/out/report}"); REF=$(realpath t2/golden)
mkdir -p "$REP/img"
flipmean() { flip -r "$1" -t "$2" -d "$REP/img" -b "$3" 2>&1 | awk '/Mean:/{print $2; exit}'; }
row() { # label ref_png new_png ref_exr new_exr tag
  local label=$1 rp=$2 np=$3 re=$4 ne=$5 t=$6
  cp "$rp" "$REP/img/${t}_ref.png"; cp "$np" "$REP/img/${t}_new.png"
  oiiotool "$rp" "$np" --absdiff --mulc 8 -d uint8 -o "$REP/img/${t}_diff.png"
  local ldr hdr mx
  ldr=$(flipmean "$rp" "$np" "${t}_flip")
  hdr=$(flipmean "$re" "$ne" "${t}_hdrflip")
  mx=$( { idiff "$re" "$ne" 2>&1 || true; } | awk '/Max error/{print $4; exit}'); mx=${mx:-0}  # idiff exits 1 on a difference
  cat >> "$REP/index.html" <<ROW
<tr><th>$label<br><small>LDR-FLIP mean $ldr<br>HDR-FLIP mean $hdr<br>scene max |d| ${mx} cd/m&sup2;</small></th>
<td><img src="img/${t}_ref.png"></td><td><img src="img/${t}_new.png"></td><td><img src="img/${t}_diff.png"></td>
<td><img src="img/${t}_flip.png"></td><td><img src="img/${t}_hdrflip.png"></td></tr>
ROW
  printf "%-26s LDR-FLIP %-9s HDR-FLIP %-9s scene max|d| %s\n" "$label" "$ldr" "$hdr" "$mx"; }

cat > "$REP/index.html" <<'HEAD'
<!doctype html><html><head><meta charset="utf-8"><title>T2 render report</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#ddd}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141414;--fg:#e8e8e8;--mut:#999;--line:#333}}
body{background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif;margin:16px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:6px;vertical-align:top;text-align:left}
th small{color:var(--mut);font-weight:normal}img{width:100%;max-width:340px;image-rendering:pixelated}
.wrap{overflow-x:auto}
</style></head><body>
<h1>T2 render report</h1>
<p>Frozen baseline (<code>t2/golden</code>) vs current render; diagnostic only. FLIP maps: magma, brighter = more
noticeable when flipping between the images. The last two rows are deliberate changes, shown for scale.</p>
<div class="wrap"><table><tr><th></th><th>reference</th><th>current</th><th>|diff| &times;8</th><th>LDR-FLIP (display)</th><th>HDR-FLIP (scene)</th></tr>
HEAD
for a in vacuum clear mild; do
  row "$a: golden vs current" "$REF/${a}_display.png" "$CUR/${a}_display.png" "$REF/${a}_scene.exr" "$CUR/${a}_scene.exr" "$a"
done
row "vacuum -> clear (for scale)" "$REF/vacuum_display.png" "$REF/clear_display.png" "$REF/vacuum_scene.exr" "$REF/clear_scene.exr" vc
row "clear -> mild (for scale)" "$REF/clear_display.png" "$REF/mild_display.png" "$REF/clear_scene.exr" "$REF/mild_scene.exr" cm
echo "</table></div></body></html>" >> "$REP/index.html"
echo "report: $REP/index.html"
