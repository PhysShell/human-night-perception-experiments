% NATIVE wrapper: runs J. R. Frisvad's unmodified hippus.m (pupillary hippus model, Eq. 1 of
% Ritschel et al. 2009; https://people.compute.dtu.dk/jerf/code/hippus/hippus_matlab.zip) in Octave
% and saves the figure + the plotted curves. Usage (from repo root):
%   nix shell --inputs-from . nixpkgs#octave nixpkgs#gnuplot -c octave --no-gui -q tracks/temporal-glare-2009/run_hippus_native.m
src = fullfile(pwd, 'research-cache', 'temporal-glare-2009', 'hippus_matlab');
out = fullfile(pwd, 'results', 'native', 'temporal-glare-2009');
addpath(src);
graphics_toolkit('gnuplot');
figure('visible', 'off');
hippus;                          % author script, unmodified
h = get(gca, 'children');
fid = fopen(fullfile(out, 'NATIVE_hippus_curves.csv'), 'w');
fprintf(fid, 'curve,t_s,pupil_mm\n');
for c = 1:numel(h)
  x = get(h(c), 'xdata'); y = get(h(c), 'ydata');
  for k = 1:numel(x) fprintf(fid, '%d,%.4f,%.5f\n', c, x(k), y(k)); end
end
fclose(fid);
print(fullfile(out, 'NATIVE_hippus_matlab_octave.png'), '-dpngcairo');
