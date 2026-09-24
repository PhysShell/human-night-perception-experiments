% B1.0 oracle O3 (NATIVE ISETCam human/ijspeert.m, IJspeert, van den Berg & Spekreijse 1993):
% analytic foveal PSF over the full angular range, age 24, pupil 6 mm, pigmentation m (0.106 = mean brown
% Caucasian eye, the closest label to CIE p = 0.5 "brown eye"; 0.142 = Caucasian population mean).
% phi in radians, log-spaced 1e-7 .. pi/2; PSF as returned (sr^-1 per the model's f_beta).
% Writes b1/out/o3_ijspeert.csv: phi_rad, PSF_m0106, PSF_m0142, PSF_m0106_p3mm
phi = [logspace(-7, log10(pi/2), 40000)];
[~, P1] = ijspeert(24, 6, 0.106, 0:60, phi);
[~, P2] = ijspeert(24, 6, 0.142, 0:60, phi);
[~, P3] = ijspeert(24, 3, 0.106, 0:60, phi);
M = [phi(:), P1(:), P2(:), P3(:)];
f = fopen(fullfile(getenv('REPO'), 'b1', 'out', 'o3_ijspeert.csv'), 'w');
fprintf(f, 'phi_rad,psf_m0106_p6,psf_m0142_p6,psf_m0106_p3\n'); fprintf(f, '%.10g,%.10g,%.10g,%.10g\n', M'); fclose(f);
printf('ijspeert PSF at 1 arcmin (m .106, 6 mm): %g sr^-1\n', interp1(phi, P1, pi/180/60));
