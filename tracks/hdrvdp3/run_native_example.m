% NATIVE: run the shipped examples/example_octave.m of HDR-VDP 3.0.7 unmodified.
% Usage (from repo root): tracks/hdrvdp3/octave.sh tracks/hdrvdp3/run_native_example.m [raw8]
%  default : 16-bit PNG read correctly through shim/imread.m (MATLAB-equivalent input)
%  raw8    : Octave's own imread (8-bit GraphicsMagick) -> documents the as-shipped Octave failure mode
% Wrappers only: waitforbuttonpress/imread shims, fixed RNG seed, catching the (headless) plotting
% error at the end of the example, saving the numbers.
args = argv(); mode = 'shim16'; if numel(args) >= 1 && strcmp(args{end},'raw8'), mode = 'raw8'; end
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
out = fullfile(repo,'results','native','hdrvdp3'); if ~exist(out,'dir'), mkdir(out); end
addpath(fullfile(repo,'tracks','hdrvdp3'));
addpath(fullfile(repo,'tracks','hdrvdp3','shim'));
if strcmp(mode,'raw8'), rmpath(fullfile(repo,'tracks','hdrvdp3','shim')); addpath(fullfile(repo,'tracks','hdrvdp3','shim_nogfx')); end
randn('state',0); rand('state',0);
cd(fullfile(donor,'examples'));
t0 = tic; plot_err = '';
try
    example_octave;          % the shipped script, verbatim
catch err
    plot_err = err.message;  % expected: 'no graphics toolkits are available!' (headless octave-cli)
end
el = toc(t0);
fprintf('I_ref class after /(2^16-1): max=%g\n', max(I_ref(:)));
tag = ['NATIVE_example_octave_' mode];
fid = fopen(fullfile(out,[tag '.json']),'w');
fprintf(fid, '{"label":"NATIVE","script":"examples/example_octave.m (HDR-VDP 3.0.7, unmodified)","imread":"%s","octave":"%s","ppd":%.4f,"I_ref_max":%.6f,\n', mode, version(), ppd, max(I_ref(:)));
fprintf(fid, ' "side_by_side":{"Q_JOD":%.4f,"P_det":%.4f,"C_max":%.4f},\n', res_noise_sbs.Q_JOD, res_noise_sbs.P_det, res_noise_sbs.C_max);
fprintf(fid, ' "flicker":{"Q_JOD":%.4f,"P_det":%.4f,"C_max":%.4f},"seconds":%.1f,"plot_error":"%s"}\n', res_noise_flicker.Q_JOD, res_noise_flicker.P_det, res_noise_flicker.C_max, el, plot_err);
fclose(fid);
imwrite(hdrvdp_visualize(res_noise_sbs.P_map, I_context), fullfile(out,[tag '_pmap_sbs.png']));
imwrite(hdrvdp_visualize(res_noise_flicker.P_map, I_context), fullfile(out,[tag '_pmap_flicker.png']));
type(fullfile(out,[tag '.json']));
