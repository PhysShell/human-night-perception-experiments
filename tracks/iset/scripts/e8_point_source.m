% E8/E9 (ADAPTED: unmodified ISETCam/ISETBio functions, our point-source spectra, GNU Octave).
% A single unresolved point source with five spectra (LPS, HPS=CIE HP1, warm LED=CIE LED-B1,
% E, BLUE) imaged through ISETBio 'wvf human' optics (Thibos 2009 mean Zernikes + human LCA +
% Lens) at pupils 3/4.5/6/7 mm. Saves (1) the per-wavelength PSFs of the wvf model (E9) and
% (2) the spectral retinal irradiance of the point for each spectrum/pupil (E8) to .mat (v7).
% Run through tracks/iset/scripts/run_octave.sh (needs ISET_OUT, the output dir).
out = getenv('ISET_OUT');
repo = fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
if isempty(repo) || ~exist(fullfile(repo,'tracks'),'dir'), repo = getenv('REPO'); end
S = dlmread(fullfile(repo,'tracks','mitsuba-spectral','spectra','test_spectra_unitlum.csv'), ',', 1, 0);
names = {'LPS','HPS','LED_warm','E','BLUE'};
wave = (400:5:700)';
N = 129;                 % scene pixels
arcminPerPix = 0.5;      % 129 px * 0.5 arcmin = 64.5 arcmin field
pupils = [3 4.5 6 7];
psfWaves = [450 500 550 590 650];
res = struct();
for ip = 1:numel(pupils)
  p = pupils(ip);
  [oi, wvf] = oiCreate('wvf human', p, [], wave);
  % ---- E9: the model's own PSF per wavelength (arcmin support)
  for iw = 1:numel(psfWaves)
    w = psfWaves(iw);
    psf = wvfGet(wvf,'psf',w);
    samp = wvfGet(wvf,'psf spatial samples','min',w);
    res.(sprintf('psf_p%02d_w%d', round(p*10), w)) = single(psf);
    res.(sprintf('psfsamp_p%02d_w%d', round(p*10), w)) = samp(:)';
  end
  % ---- E8: point source scene per spectrum
  for is = 1:numel(names)
    spd = interp1(S(:,1), S(:,1+is), wave, 'linear', 0);   % W m^-2 sr^-1 nm^-1 per (cd/m^2)
    scene = sceneCreate('uniform ee', N, wave);
    scene = sceneSet(scene,'fov', N*arcminPerPix/60);
    ph = zeros(N,N,numel(wave));
    c = (N+1)/2;
    ph(c,c,:) = reshape(Energy2Quanta(wave, spd(:)), 1,1,[]);
    scene = sceneSet(scene,'photons', ph);
    oic = oiCompute(oi, scene, 'pad value', 'zero');
    tag = sprintf('%s_p%02d', names{is}, round(p*10));
    res.(['oiphotons_' tag]) = single(oiGet(oic,'photons'));
    res.(['oiillum_' tag]) = single(oiGet(oic,'illuminance'));
    res.(['oiumperpix_' tag]) = oiGet(oic,'sample spacing','um');
    printf('done %s\n', tag); fflush(stdout);
  end
  res.(sprintf('lens_transmittance_p%02d', round(p*10))) = oiGet(oi,'optics transmittance');
end
res.wave = wave; res.names = names; res.pupils = pupils; res.arcminPerPix = arcminPerPix;
res.umPerDegree = wvfGet(wvf,'um per degree');
save('-v7', fullfile(out,'ADAPTED_e8_point_source_octave.mat'), '-struct', 'res');
printf('saved\n');
