% B0 variant V1 (ISET human optics): the point-spread image of ISETBio/ISETCam 'wvf human' optics
% (Thibos 2009 mean eye, LCA, focus 550 nm) for a single-pixel point with an HPS spectrum (CIE HP1,
% from tracks/mitsuba-spectral/spectra), pupil 6 mm (a night pupil; Thibos data exist for 3/4.5/6/7.5),
% on a 2 x 2 deg scene at 292 px/deg (4x the 73 px/deg output, binned by b0/apply_kernels.py). Unmodified sceneCreate/oiCreate/oiCompute; only the input is ours.
% Env: B0_OUT (dir), SPD_CSV. Output: iset_kernel.raw (luminance-weighted illuminance), iset_kernel.json
wave = (400:10:700)'; ss = str2double(getenv('B0_ISET_SS')); if isnan(ss), ss = 4; end; ppd = 73 * ss; N = 146 * ss; pupil = 6;   % 4x finer scene: a single 73-px/deg pixel as the point gave sinc 'cross' tails (square pixel); the caller area-bins 4x4
T = dlmread(getenv('SPD_CSV'), ',', 1, 0);
col = str2double(getenv('B0_SPD_COL')); if isnan(col), col = 3; end   % CSV columns: 2 LPS 3 HPS 4 LED_warm 5 E 6 BLUE
spd = interp1(T(:,1), T(:,col), wave, 'linear', 0);
if strcmp(getenv('B0_NARROW550'), '1'), spd = double(wave == 550); end   % B0-optics: monochromatic 550 nm (no LCA)
scene = sceneCreate('uniform ee', N, wave);
scene = sceneSet(scene, 'fov', N / ppd);
q = Energy2Quanta(wave, spd(:));
ph = zeros(N, N, numel(wave));
ph(N/2, N/2, :) = reshape(q, 1, 1, []);   % a point 1/4 of an output pixel wide
ph = ph + 1e-9 * max(ph(:));                                   % ISET dislikes exact zeros
scene = sceneSet(scene, 'photons', ph);
zc = [];   % default: the Thibos mean eye as ISET ships it (incl. its mean defocus c4 = +0.335 um at 6 mm, ~0.26 D)
if strcmp(getenv('B0_ZERO_DEFOCUS'), '1')   % MATCHED_OBSERVER: defocus 0 (OSA j=4 set to 0, other Thibos terms kept)
  zc = wvfLoadThibosVirtualEyes(pupil); zc(5) = 0;
end
oi = oiCreate('wvf human', pupil, zc, wave);
oi = oiCompute(oi, scene, 'pad value', 'zero');
E = oiGet(oi, 'illuminance'); sz = oiGet(oi, 'size'); fov = oiGet(oi, 'fov');
addpath(fullfile(getenv('REPO'), 'tracks', 'hdrvdp3'));
write_raw(fullfile(getenv('B0_OUT'), sprintf('iset_kernel%s.raw', getenv('B0_ISET_TAG'))), E);
fid = fopen(fullfile(getenv('B0_OUT'), sprintf('iset_kernel%s.json', getenv('B0_ISET_TAG'))), 'w');
fprintf(fid, '{"pupil_mm":%g,"spectrum":"%s","oi_size":[%d,%d],"oi_fov_deg":%g,"scene_fov_deg":%g,"scene_px":%d,"supersample":%d,"zero_defocus":%d}\n', pupil, getenv('B0_SPD_NAME'), sz(1), sz(2), fov, N/ppd, N, ss, strcmp(getenv('B0_ZERO_DEFOCUS'), '1'));
fclose(fid);
printf('oi size %dx%d fov %.4f deg (scene %.4f), max %.4g sum %.4g\n', sz(1), sz(2), fov, N/ppd, max(E(:)), sum(E(:)));
