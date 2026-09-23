% NATIVE (K3): the documented example from the header of hdrvdp3.m (HDR-VDP 3.0.7, lines ~226-245):
% "The reference image is a luminance gradient from 0.1 to 1000 cd/m^2 ... distorts it with random noise
%  ... Note that the noise is more visible in the brighter part (bottom of the image)."
% The code below is the header example verbatim (plus fixed seed, no GPU, saving numbers).
repo = fileparts(fileparts(fileparts(mfilename('fullpath'))));
donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
out = fullfile(repo,'results','native','hdrvdp3');
pkg load statistics; pkg load image; addpath(donor); addpath(fullfile(donor,'utils'));
randn('state',0); rand('state',0);
% ---- verbatim from hdrvdp3.m header ----
reference = logspace( log10(0.1), log10(1000), 512 )' * ones( 1, 512 );
noise_contrast = 0.05;
test = reference .* (1 + (rand( 512, 512 )-0.5)*2*noise_contrast);
ppd = hdrvdp_pix_per_deg( 30, [1920 1200], 0.5 );
res = hdrvdp3( 'side-by-side', test, reference, 'luminance', ppd, { 'surround', 13 } );
% ----------------------------------------
P = res.P_map; rowsP = mean(P,2); L = reference(:,1);
bands = [0.1 1; 1 10; 10 100; 100 1000];
fid = fopen(fullfile(out,'NATIVE_K3_doc_example_ramp.json'),'w');
fprintf(fid,'{"label":"NATIVE","example":"hdrvdp3.m header example (luminance ramp 0.1-1000 cd/m^2 + 5%% noise, side-by-side, surround 13)","ppd":%.3f,"P_det":%.4f,"Q_JOD":%.4f,\n "mean_P_map_by_luminance_decade":{', ppd, res.P_det, res.Q_JOD);
for b = 1:size(bands,1)
  m = L>=bands(b,1) & L<bands(b,2);
  fprintf(fid,'%s"%g-%g cd/m2":%.4f', repmat(',',1,b>1), bands(b,1), bands(b,2), mean(rowsP(m)));
end
top = mean(rowsP(1:128)); bot = mean(rowsP(end-127:end));
fprintf(fid,'},\n "claim":"noise more visible in the brighter part (bottom)","top_quarter_P":%.4f,"bottom_quarter_P":%.4f,"claim_reproduced":%s}\n', top, bot, mat2str(bot>top));
fclose(fid); type(fullfile(out,'NATIVE_K3_doc_example_ramp.json'));
imwrite(hdrvdp_visualize('pmap', res.P_map), fullfile(out,'NATIVE_K3_doc_example_ramp_pmap.png'));
