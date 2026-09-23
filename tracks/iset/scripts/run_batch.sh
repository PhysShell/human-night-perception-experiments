#!/usr/bin/env bash
# Run the selected ISETCam/ISETBio tutorials, examples and isetvalidate scripts under Octave.
REPO=$(cd "$(dirname "$0")/../../.." && pwd); C=$REPO/research-cache/iset; L=$REPO/results/native/iset/logs
mkdir -p $L
for s in \
  isetcam/tutorials/oi/t_oiIntroduction.m \
  isetbio/tutorials/wavefront/t_wvfHuman.m \
  isetbio/examples/human/s_humanOptics.m \
  isetbio/examples/human/s_humanLSF.m \
  isetbio/tutorials/optics/t_humanLineSpreadOI.m \
  isetbio/tutorials/outersegment/t_osFoveaPeriphery.m \
  isetvalidate/isetcam/oi/v_icam_oiWVF.m \
  isetvalidate/isetcam/optics/v_icam_opticsWVF.m \
  isetvalidate/isetcam/optics/v_icam_opticsFlare.m \
  isetvalidate/isetcam/wavefront/v_icam_wvfWaveDefocus.m \
  isetvalidate/isetbio/calibration/v_ibio_calibrationRods.m \
  isetvalidate/isetbio/calibration/v_ibio_calibrationPugh.m \
  isetvalidate/isetbio/cones/v_ibio_pigments.m \
  isetvalidate/isetbio/cones/v_ibio_coneAdaptation.m \
  isetvalidate/isetbio/oi/v_ibio_photonNoise.m ; do
  echo "== $s"; "$REPO/tracks/iset/scripts/run_octave.sh" "$C/$s" "$L/$(basename $s .m).log"
done
