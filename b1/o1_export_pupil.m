% B1.1 input (NATIVE ISETCam): the Thibos mean-eye pupil function at 550 nm on the B1.1 grid, exported so that
% b1/unified_pupil.py can add a scatter phase to the SAME complex pupil. Grid: B1_N samples on a B1_PLANE mm
% pupil plane (1.3303 um / sample = Arias 2018's pupil sampling -> scatter Nyquist ~11.8 deg at 550 nm).
% Exports, cropped to the pupil's bounding square (+2 samples): wavefront aberration W (um), aperture amplitude;
% and the ISET PSF's central 1025 x 1025 crop (for the exact scatter_off check).
eye = getenv('B1_EYE'); N = str2double(getenv('B1_N')); P = str2double(getenv('B1_PLANE'));
zc = wvfLoadThibosVirtualEyes(6);
switch eye, case 'native', c4 = zc(5); case 'zero', c4 = 0; end
zc(5) = c4;
wvf = wvfCreate('calc wavelengths', 550, 'zcoeffs', zc, 'name', eye, 'umPerDegree', 300, 'lcaMethod', 'human');
wvf = wvfSet(wvf, 'measured pupil diameter', 6); wvf = wvfSet(wvf, 'calc pupil diameter', 6);
wvf = wvfSet(wvf, 'spatial samples', N); wvf = wvfSet(wvf, 'ref pupil plane size', P);
wvf = wvfCompute(wvf);
pf = wvfGet(wvf, 'pupil function', 550); W = wvfGet(wvf, 'wavefront aberrations', 550);
if iscell(pf), pf = pf{1}; end; if iscell(W), W = W{1}; end
A = abs(pf); [r, c] = find(A > 0); r0 = min(r) - 2; r1 = max(r) + 2; c0 = min(c) - 2; c1 = max(c) + 2;
psf = wvfGet(wvf, 'psf', 550); m = floor(N/2) + 1; h = 512;
addpath(fullfile(getenv('REPO'), 'tracks', 'hdrvdp3'));
tag = sprintf('%s/b1/out/pupil_%s_N%d', getenv('REPO'), eye, N);
write_raw([tag '_W.raw'], W(r0:r1, c0:c1)); write_raw([tag '_A.raw'], A(r0:r1, c0:c1));
write_raw([tag '_psfcrop.raw'], psf(m-h:m+h, m-h:m+h));
f = fopen([tag '.json'], 'w');
fprintf(f, '{"eye":"%s","c4_um":%g,"N":%d,"plane_mm":%.6g,"dx_mm":%.9g,"crop_rows":[%d,%d],"crop_cols":[%d,%d],"grid_centre_1based":%d,"psf_arcmin_per_sample":%.9g,"psf_sum":%.12g,"psf_peak":%.12g,"amp_unique":[%s]}\n', ...
        eye, c4, N, P, P/N, r0, r1, c0, c1, m, wvfGet(wvf, 'psf arcmin per sample', 550), sum(psf(:)), max(psf(:)), sprintf('%g,', unique(round(A(A>0)*1e6)/1e6)(1:min(3,end)))(1:end-1));
fclose(f);
printf('%s: crop %dx%d, dx %.5g um, psf %.5g arcmin/sample, peak %.6g\n', eye, r1-r0+1, c1-c0+1, P/N*1e3, wvfGet(wvf, 'psf arcmin per sample', 550), max(psf(:)));
