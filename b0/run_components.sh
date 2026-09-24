#!/usr/bin/env bash
# B0 (v2) step 1: every optics variant applied to the three linear components at the PHONE grid
# (73 px/deg): C_sky_nobar, C_sky_bar, C_src1. retinal(k, bar) = R(sky_bar) + k * R(src1) exactly,
# because every donor optics here is a linear convolution (HDR-VDP's clamp at 1e-5 cd/m^2 is
# checked in the sweep: it only lifts pixels below 1e-5, never the sky at 4e-4).
# Temporal glare is run in three window treatments (sensitivity test, frame 1 of the demo):
#   V5_temporal (taper + renormalised; the blind set), V5t_square (demo window as is),
#   V5t_norenorm (taper, cut energy not returned).
#   nix develop -c b0/run_components.sh           # v2 (warm HPS-like source, HDR-VDP OTFs at 2x)
#   B0_LAYER=ach nix develop -c b0/run_components.sh   # v3 B0-optics (achromatic): neutral source of the
#       same photopic luminance, ISET at monochromatic 550 nm (no LCA), defocus 0, temporal kernel luminance-weighted
#       on all channels, HDR-VDP/CIE99 OTFs at the production 4x grid (8x spot check: b0/cie_ss_check.py)
set -euo pipefail
R=$PWD; S=b0/out/stim; O=b0/out/comp; HSS=2
if [ "${B0_LAYER:-}" = ach ]; then
  S=b0/out/stim_ach; O=b0/out/comp_ach; HSS=4
  export ISET_KERNEL=$R/b0/out/kernels/iset_kernel_550z.raw TEMPORAL_ACHROMATIC=1   # 550 nm, defocus 0 (MATCHED_OBSERVER)
fi
mkdir -p $O
oct() { REPO=$R B0_IN=$1 B0_OUT_PREFIX=$2 B0_MTF=$3 B0_PPD=73 B0_SS=${4:-1} tracks/hdrvdp3/octave.sh b0/hdrvdp_optics.m; }
for c in C_sky_nobar C_sky_bar C_src1; do
  python3 tracks/hdrvdp3/img2raw.py $S/$c.exr $O/$c.raw
  cp $S/$c.exr $O/V0_none_$c.exr
  python3 b0/apply_kernels.py iset $S/$c.exr $O/V1_iset_$c.exr > $O/V1_iset_$c.json
  for m in hdrvdp:V2_hdrvdpmtf cie:V3_cie99; do
    if [ $c = C_src1 ]; then
      # HDR-VDP clamps its OTF output at >= 1e-5 cd/m^2; on a lamp-on-black component that floor would
      # scale with k. Run (src + 0.01) and (0.01) through the same optics and subtract (linear, exact).
      oiiotool $S/$c.exr --addc 0.01 -o $O/ped_src.exr; oiiotool $S/$c.exr --mulc 0 --addc 0.01 -o $O/ped.exr
      for q in ped_src ped; do
        python3 tracks/hdrvdp3/img2raw.py $O/$q.exr $O/$q.raw; oct $O/$q.raw $O/${m#*:}_$q ${m%%:*} $HSS | tail -1
        python3 b0/raw2exr.py $O/${m#*:}_${q}_retinal.raw $O/${m#*:}_$q.exr; rm -f $O/${m#*:}_${q}_*.raw $O/$q.raw
      done
      oiiotool $O/${m#*:}_ped_src.exr $O/${m#*:}_ped.exr --sub -o $O/${m#*:}_$c.exr
      rm -f $O/${m#*:}_ped_src.exr $O/${m#*:}_ped.exr $O/ped_src.exr $O/ped.exr
    else
      oct $O/$c.raw $O/${m#*:}_$c ${m%%:*} $HSS | tail -1
      python3 b0/raw2exr.py $O/${m#*:}_${c}_retinal.raw $O/${m#*:}_$c.exr; rm -f $O/${m#*:}_${c}_*.raw
    fi
  done
  blender -b --factory-startup --python m1/fog_glow.py -- $S/$c.exr $O/V4_spencer_$c.exr 12 > /dev/null 2>&1
  oiiotool $O/V4_spencer_$c.exr --ch R,G,B -o $O/V4_spencer_$c.exr
  for t in renorm:V5_temporal none:V5t_square norenorm:V5t_norenorm; do
    TAPER=${t%%:*} tracks/temporal-glare-2009/py.sh b0/apply_kernels.py temporal $S/$c.exr $O/${t#*:}_$c 1 > /dev/null
    mv $O/${t#*:}_${c}_0001.exr $O/${t#*:}_$c.exr; rm -f $O/${t#*:}_${c}_frames.json
  done
  rm -f $O/$c.raw
  echo "components done: $c"
done
