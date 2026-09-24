% B0 variant V1 (ISET human optics): the point-spread image of ISETBio/ISETCam 'wvf human' optics
% (Thibos 2009 mean eye, LCA, focus 550 nm) for a single-pixel point with an HPS spectrum (CIE HP1,
% from tracks/mitsuba-spectral/spectra), pupil 6 mm (a night pupil; Thibos data exist for 3/4.5/6/7.5),
% on a 2 x 2 deg scene at 292 px/deg (4x the 73 px/deg output, binned by b0/apply_kernels.py). Unmodified sceneCreate/oiCreate/oiCompute; only the input is ours.
% Env: B0_OUT (dir), SPD_CSV. Output: iset_kernel.raw (luminance-weighted illuminance), iset_kernel.json
wave = (400:10:700)'; ss = 4; ppd = 73 * ss; N = 146 * ss; pupil = 6;   % 4x finer scene: a single 73-px/deg pixel as the point gave sinc 'cross' tails (square pixel); the caller area-bins 4x4
T = dlmread(getenv('SPD_CSV'), ',', 1, 0);
spd = interp1(T(:,1), T(:,3), wave, 'linear', 0);            % column 3 = HPS
scene = sceneCreate('uniform ee', N, wave);
scene = sceneSet(scene, 'fov', N / ppd);
q = Energy2Quanta(wave, spd(:));
ph = zeros(N, N, numel(wave));
ph(N/2, N/2, :) = reshape(q, 1, 1, []);   % a point 1/4 of an output pixel wide
ph = ph + 1e-9 * max(ph(:));                                   % ISET dislikes exact zeros
scene = sceneSet(scene, 'photons', ph);
oi = oiCreate('wvf human', pupil, [], wave);
oi = oiCompute(oi, scene, 'pad value', 'zero');
E = oiGet(oi, 'illuminance'); sz = oiGet(oi, 'size'); fov = oiGet(oi, 'fov');
addpath(fullfile(getenv('REPO'), 'tracks', 'hdrvdp3'));
write_raw(fullfile(getenv('B0_OUT'), 'iset_kernel.raw'), E);
fid = fopen(fullfile(getenv('B0_OUT'), 'iset_kernel.json'), 'w');
fprintf(fid, '{"pupil_mm":%g,"spectrum":"HPS (CIE HP1)","oi_size":[%d,%d],"oi_fov_deg":%g,"scene_fov_deg":%g,"scene_px":%d,"supersample":%d}\n', pupil, sz(1), sz(2), fov, N/ppd, N, ss);
fclose(fid);
printf('oi size %dx%d fov %.4f deg (scene %.4f), max %.4g sum %.4g\n', sz(1), sz(2), fov, N/ppd, max(E(:)), sum(E(:)));
