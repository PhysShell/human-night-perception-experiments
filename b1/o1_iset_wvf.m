% B1.0 oracle O1 (NATIVE ISETCam wavefront toolbox): the Thibos mean virtual eye PSF on its OWN grid,
% no scene/oi convolution. Monochromatic 550 nm (= ISET's measured wavelength, so no LCA shift),
% 6 mm pupil, Thibos 6 mm Zernike set; defocus convention from B1_EYE (native | zero | best).
% Sampling from env: B1_N (spatial samples), B1_PLANE (reference pupil-plane size, mm).
%   PSF sample = lambda / plane (rad); support = +-N/2 samples.
% Writes b1/out/o1_<eye>_N<N>_P<plane>.raw (+ .json).
eye = getenv('B1_EYE'); N = str2double(getenv('B1_N')); P = str2double(getenv('B1_PLANE'));
zc = wvfLoadThibosVirtualEyes(6);
switch eye
  case 'native', c4 = zc(5);
  case 'zero',   c4 = 0;
  case 'best',   c4 = 0.05;          % BEST_FOCUS_550 grid optimum (b0/results/through_focus.json)
end
zc(5) = c4;
wvf = wvfCreate('calc wavelengths', 550, 'zcoeffs', zc, 'name', eye, 'umPerDegree', 300, 'lcaMethod', 'human');
wvf = wvfSet(wvf, 'measured pupil diameter', 6); wvf = wvfSet(wvf, 'calc pupil diameter', 6);
wvf = wvfSet(wvf, 'spatial samples', N); wvf = wvfSet(wvf, 'ref pupil plane size', P);
wvf = wvfCompute(wvf);
psf = wvfGet(wvf, 'psf', 550); dmin = wvfGet(wvf, 'psf arcmin per sample', 550);
addpath(fullfile(getenv('REPO'), 'tracks', 'hdrvdp3'));
tag = sprintf('%s/b1/out/o1_%s_N%d_P%g', getenv('REPO'), eye, N, P);
write_raw([tag '.raw'], psf);
f = fopen([tag '.json'], 'w');
fprintf(f, '{"eye":"%s","c4_um":%g,"wavelength_nm":550,"pupil_mm":6,"spatial_samples":%d,"pupil_plane_mm":%g,"arcmin_per_sample":%.8g,"support_half_arcmin":%.6g,"sum":%.10g}\n', ...
        eye, c4, N, P, dmin, dmin * (N - 1) / 2, sum(psf(:)));
fclose(f);
printf('%s: %d samples, %.4f arcmin/sample, support +-%.1f arcmin, sum %.6f\n', eye, N, dmin, dmin * (N - 1) / 2, sum(psf(:)));
