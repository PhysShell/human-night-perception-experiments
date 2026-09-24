% Octave side of run_hdrvdp.sh (see there). Reads env vars HV_*.
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
pkg load statistics; pkg load image;
addpath(donor); addpath(fullfile(donor,'utils')); addpath(fullfile(repo,'tracks','hdrvdp3')); addpath(fullfile(repo,'b0','octave_shim'));  % dirac() for the 'cie' MTF under Octave (b0/octave_shim/dirac.m)
warning('off','Octave:data-file-in-path'); addpath(fullfile(donor,'data'));  % utils/hdrvdp_iturgb2native.m:6 dlmread('ciexyz31.csv') needs data/ on the path
g = @(k) getenv(k);
out = g('HV_OUT'); target = g('HV_TARGET'); disp_mode = g('HV_DISP');
dt = jsondecode(fileread(fullfile(repo,'stimuli','display_targets.json')));
key = [upper(target) '_TARGET'];
if ~isfield(dt, key), error('unknown target %s (PHONE|DESKTOP)', target); end
T = dt.(key);
ppd = T.px_per_deg_centre; peak = T.peak_cd_m2; contrast = T.contrast; E_amb = T.E_ambient_lux;
black = peak/contrast + E_amb*0.005/pi;
test = double(read_raw(g('HV_TEST_RAW'))); ref = double(read_raw(g('HV_REF_RAW')));
nch = size(ref,3);
if nch == 1, enc = 'luminance'; elseif nch >= 3, enc = 'rgb-bt.709'; test = test(:,:,1:3); ref = ref(:,:,1:3); else error('bad channels'); end
lumY = @(I) (size(I,3)==1)*I(:,:,1) + (size(I,3)==3)*(0.2126*I(:,:,1)+0.7152*I(:,:,2)+0.0722*I(:,:,3));
stats = @(I) [min(I(:)) median(I(:)) max(I(:))];
inY_ref = stats(lumY(ref)); inY_test = stats(lumY(test));
clipped_ref = 0; clipped_test = 0;
switch disp_mode
  case 'clip'
    clipped_ref = nnz(any(ref>peak,3)); clipped_test = nnz(any(test>peak,3));
    ref = min(max(ref,0),peak) + black; test = min(max(test,0),peak) + black;
  case 'none'
  otherwise, error('display mode clip|none');
end
surr = g('HV_SURR'); if ~isnan(str2double(surr)), surr = str2double(surr); end
opts = { 'use_gpu', false, 'mtf', g('HV_MTF'), 'surround', surr };
age_str = g('HV_AGE'); if isempty(age_str), age_str = 'null'; else opts = [opts, {'age', str2double(age_str)}]; end  % donor default age = 24 (hdrvdp_parse_options.m:64)
tasks = strsplit(strtrim(g('HV_TASKS')), ' ');
fid = fopen(fullfile(out,'run.json'),'w');
fprintf(fid, '{"label":"COMMON","metric":"HDR-VDP %g (hdrvdp_version.m; release 3.0.7) Octave %s","test":"%s","ref":"%s","target":"%s","ppd":%g,"peak_cd_m2":%g,"contrast":%g,"black_cd_m2":%g,"E_ambient_lux":%g,\n', ...
  hdrvdp_version(), version(), g('HV_TEST'), g('HV_REF'), key, ppd, peak, contrast, black, E_amb);
fprintf(fid, ' "color_encoding":"%s","display_model":"%s","mtf":"%s","age":%s,"surround":"%s","size":[%d,%d],\n', enc, disp_mode, g('HV_MTF'), age_str, num2str(surr), size(ref,2), size(ref,1));
fprintf(fid, ' "input_Y_ref_min_med_max":[%g,%g,%g],"input_Y_test_min_med_max":[%g,%g,%g],"pixels_clipped_ref":%d,"pixels_clipped_test":%d,\n', inY_ref, inY_test, clipped_ref, clipped_test);
fprintf(fid, ' "results":{');
for t = 1:numel(tasks)
  tk = tasks{t}; t0 = tic;
  res = hdrvdp3( tk, test, ref, enc, ppd, opts );
  el = toc(t0);
  P = res.P_map; 
  fprintf(fid, '%s\n  "%s":{"P_det":%.6f,"C_max":%.6g,"Q":%.4f,"Q_JOD":%.4f,"P_map_max":%.6f,"pixels_P_gt_0.5":%d,"pixels_P_gt_0.75":%d,"seconds":%.1f}', ...
     repmat(',',1,t>1), tk, res.P_det, res.C_max, res.Q, res.Q_JOD, max(P(:)), nnz(P>0.5), nnz(P>0.75), el);
  ctx = lumY(ref);
  imwrite(hdrvdp_visualize(P, ctx/max(ctx(:))), fullfile(out, sprintf('hdrvdp_%s_pmap.png', tk)));
  imwrite(uint16(round(min(max(P,0),1)*65535)), fullfile(out, sprintf('hdrvdp_%s_Pmap16.png', tk)));
end
fprintf(fid, '}}\n'); fclose(fid); type(fullfile(out,'run.json'));
