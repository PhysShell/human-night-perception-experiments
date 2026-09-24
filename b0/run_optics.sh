#!/usr/bin/env bash
# B0 step 1: the six optics variants on every B0 stimulus -> retinal cd/m^2 EXRs, plus the Vangorp
# local-adaptation map (HDR-VDP-3's hdrvdp_local_adapt, model #7) of each retinal image.
#   V0_none      physical, no eye optics (the M2.6 state)
#   V1_iset      ISETBio/ISETCam 'wvf human' (Thibos mean eye, 6 mm, HPS spectrum)
#   V2_hdrvdpmtf HDR-VDP 3.0.7 custom-fit eye MTF
#   V3_cie99     CIE 135/1 (Vos & van den Berg 1999) glare spread, age 24 (HDR-VDP implementation)
#   V4_spencer   Spencer 1995 photopic PSF = our calibrated Blender Fog Glow adapter (m1/fog_glow.py)
#   V5_temporal  Temporal Glare co-author demo PSF (hippus), frame 1 here; sequences in run_b0.sh
#   nix develop -c b0/run_optics.sh
set -euo pipefail
R=$PWD; O=b0/out/optics; mkdir -p $O
oct() { REPO=$R B0_IN=$1 B0_OUT_PREFIX=$2 B0_MTF=$3 B0_PPD=73 B0_SS=${4:-1} tracks/hdrvdp3/octave.sh b0/hdrvdp_optics.m; }
[ -f $O/iset_kernel.raw ] || { echo "run b0/iset_kernel.m first (see README)"; exit 1; }
for k in 1 10 100; do for b in bar nobar; do
  S=b0/out/stim/B0_k${k}_${b}.exr; n=k${k}_${b}
  python3 tracks/hdrvdp3/img2raw.py $S $O/$n.raw
  cp $S $O/V0_none_$n.exr
  python3 b0/apply_kernels.py iset $S $O/V1_iset_$n.exr > $O/V1_iset_$n.json
  for m in hdrvdp:V2_hdrvdpmtf cie:V3_cie99; do
    oct $O/$n.raw $O/${m#*:}_$n ${m%%:*} 2 | tail -1   # OTF on a 2x grid, area-binned (no Nyquist cross)
    python3 b0/raw2exr.py $O/${m#*:}_${n}_retinal.raw $O/${m#*:}_$n.exr
  done
  blender -b --factory-startup --python m1/fog_glow.py -- $S $O/V4_spencer_$n.exr 12 > $O/V4_spencer_$n.log 2>&1
  tracks/temporal-glare-2009/py.sh b0/apply_kernels.py temporal $S $O/V5_temporal_$n 1 > /dev/null
  mv $O/V5_temporal_${n}_0001.exr $O/V5_temporal_$n.exr
  for v in V0_none V1_iset V2_hdrvdpmtf V3_cie99 V4_spencer V5_temporal; do     # Vangorp adaptation map
    python3 tracks/hdrvdp3/img2raw.py $O/${v}_$n.exr $O/tmp.raw
    oct $O/tmp.raw $O/${v}_${n}_la none > /dev/null
    python3 b0/raw2exr.py $O/${v}_${n}_la_Lla.raw $O/${v}_${n}_Lla.exr
  done
  rm -f $O/*.raw.tmp $O/*_retinal.raw $O/*_la_retinal.raw $O/*_la_Lla.raw $O/tmp.raw
  echo "optics done: $n"
done; done
