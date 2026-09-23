% COMMON (S0): stimuli/pack S0 (white D65 unresolved source, 800 cd at 3 km, night sky 4e-4 cd/m^2),
% 64x64 px crop at 32 px/deg (from c1_prepare.py), turned into an ISETCam spectral scene with the
% D65 SPD (the pack's stated white) scaled pixel-wise to the stimulus luminance, then imaged by
% ISETBio 'wvf human' optics at 3 mm and 7 mm pupils (unmodified oiCreate/oiCompute, GNU Octave).
% Env: ISET_OUT (output dir), C1_MAT (input .mat).
in = load(getenv('C1_MAT'));
Y = in.Y; N = size(Y,1);
wave = (400:10:700)';
scene = sceneCreate('uniform d65', N, wave);
scene = sceneSet(scene, 'fov', N / in.px_per_deg);
ph = sceneGet(scene,'photons');
ph = ph .* (Y / mean(Y(:)));                 % luminance is linear in photons
scene = sceneSet(scene,'photons', ph);
scene = sceneAdjustLuminance(scene, mean(Y(:)));
res.scene_lum = sceneGet(scene,'luminance');
res.scene_max = max(res.scene_lum(:));
res.scene_mean = sceneGet(scene,'mean luminance');
for p = [3 7]
  oi = oiCreate('wvf human', p, [], wave);
  oi = oiCompute(oi, scene, 'pad value', 'mean');
  tag = sprintf('p%d', p);
  res.(['illum_' tag]) = oiGet(oi,'illuminance');      % retinal illuminance (ISET 'lux')
  res.(['umpp_' tag]) = oiGet(oi,'sample spacing','um');
  res.(['oisize_' tag]) = oiGet(oi,'size');
  printf('pupil %d: oi size %dx%d, max illum %.4g, mean %.4g\n', p, res.(['oisize_' tag]), max(res.(['illum_' tag])(:)), mean(res.(['illum_' tag])(:)));
end
save('-v7', fullfile(getenv('ISET_OUT'), 'COMMON_S0_iset_wvfhuman.mat'), '-struct', 'res');
