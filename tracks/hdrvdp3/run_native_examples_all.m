% NATIVE (K2): run the other shipped HDR-VDP 3.0.7 example scripts verbatim, headless.
% Usage: tracks/hdrvdp3/octave.sh tracks/hdrvdp3/run_native_examples_all.m <example_name>
% Wrappers only: shims (imread 16-bit, hdrread, waitforbuttonpress), RNG seed, catching the
% headless plotting error, saving numbers + P-maps.
args = argv(); ex = args{end};
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
out = fullfile(repo,'results','native','hdrvdp3'); if ~exist(out,'dir'), mkdir(out); end
addpath(fullfile(repo,'tracks','hdrvdp3')); addpath(fullfile(repo,'tracks','hdrvdp3','shim'));
addpath(donor); addpath(fullfile(donor,'utils'));
addpath(fullfile(repo,'research-cache','hdrvdp3','build'));  % gaussian_columns.mex compiled by build_mex.sh from the unmodified utils/gaussian_columns.c
pkg load statistics; pkg load image;   % as instructed in the donor README.md, section Octave
randn('state',0); rand('state',0);
cd(fullfile(donor,'examples')); t0 = tic; plot_err = '';
try
    eval(ex);
catch err
    plot_err = err.message;
end
el = toc(t0);
fid = fopen(fullfile(out,['NATIVE_' ex '.json']),'w');
fprintf(fid, '{"label":"NATIVE","script":"examples/%s.m (HDR-VDP 3.0.7, unmodified)","octave":"%s","seconds":%.1f,"stopped_at":"%s"', ex, version(), el, strrep(plot_err,'"',''''));
if exist('ppd','var'), fprintf(fid, ',"ppd":%.4f', ppd); end
names = who();
for k = 1:numel(names)
    v = eval(names{k});
    if isstruct(v) && isfield(v,'Q_JOD') && isfield(v,'P_det')
        fprintf(fid, ',\n "%s":{"Q_JOD":%.4f,"Q":%.4f,"P_det":%.4f,"C_max":%.4f}', names{k}, v.Q_JOD, v.Q, v.P_det, v.C_max);
        if exist('I_context','var') && isfield(v,'P_map')
            imwrite(hdrvdp_visualize(v.P_map, I_context), fullfile(out, sprintf('NATIVE_%s_%s_pmap.png', ex, names{k})));
        end
    end
end
if exist('Qs','var') && exist('PPDs','var')
    fprintf(fid, ',\n "PPDs":[%s],"Qs":[%s]', strjoin(arrayfun(@(x) sprintf('%.4g',x), PPDs, 'uni', 0), ','), strjoin(arrayfun(@(x) sprintf('%.4f',x), Qs', 'uni', 0), ','));
end
if exist('vis','var') && iscell(vis) && exist('I_tmo','var')
    imwrite( cat( 1, cat( 2, I_tmo{1}, I_tmo{2}, I_tmo{3} ), cat( 2, vis{1}, vis{2}, vis{3} ) ), fullfile(out, ['NATIVE_' ex '_civdm_grid.png']) );
    fprintf(fid, ',\n "civdm_grid":"NATIVE_%s_civdm_grid.png (top: mai11, saturated, mantiuk06 tone maps; bottom: civdm visualisation)"', ex);
end
fprintf(fid, '}\n'); fclose(fid);
type(fullfile(out,['NATIVE_' ex '.json']));
