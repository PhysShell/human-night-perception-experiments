% Vangorp local adaptation (HDR-VDP 3.0.7 hdrvdp_local_adapt, model-#7 descendant) for a list of raw
% retinal images: each line of B0_LIST = "<in.raw> <out.txt> <x> <y>" -> writes L_la at pixel (x,y)
% (0-based) and at the far-sky corner. One Octave session for all.
repo = getenv('REPO'); donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
pkg load image; addpath(donor); addpath(fullfile(donor,'utils')); addpath(fullfile(repo,'tracks','hdrvdp3'));
ppd = str2double(getenv('B0_PPD'));
fid = fopen(getenv('B0_LIST')); L = textscan(fid, '%s %s %d %d'); fclose(fid);
for i = 1:numel(L{1})
  I = double(read_raw(L{1}{i}));
  Y = 0.2126*I(:,:,1) + 0.7152*I(:,:,2) + 0.0722*I(:,:,3);
  la = hdrvdp_local_adapt(Y, ppd);
  f = fopen(L{2}{i}, 'w'); fprintf(f, '%g %g\n', la(L{4}(i)+1, L{3}(i)+1), median(reshape(la(1:40,1:40),[],1))); fclose(f);
end
