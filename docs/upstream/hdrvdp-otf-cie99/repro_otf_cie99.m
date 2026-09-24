% Minimal repro for HDR-VDP 3.0.7 utils/hdrvdp_otf_cie99.m (MATLAB or GNU Octave).
%   input    : a single-pixel point source (unit energy)
%   expected : the CIE 135/1 (Vos & van den Berg 1999) glare spread function, a positive radial 2-D PSF
%   actual   : the point image after the OTF from hdrvdp_otf_cie99 (what hdrvdp_mtf does for 'cie')
%   control  : the zero-order Hankel transform of the same GSF, tabulated, through the SAME FFT pipeline
% Usage: set HDRVDP=/path/to/hdrvdp-3.0.7, then run this file. Writes repro_profile.csv next to it.
% dirac(): hdrvdp_otf_cie99 calls dirac(), which MATLAB takes from the Symbolic Math Toolbox. It only
% matters at omega = 0 exactly, and the function itself overwrites M(omega < 1e-4) = 1 there. Where dirac
% is missing (Octave), the repro runs the function with two different stand-ins (0 everywhere; Inf at 0)
% and prints the largest difference between the two OTFs: the result does not depend on the stand-in.
here = fileparts(mfilename('fullpath')); addpath(fullfile(getenv('HDRVDP'), 'utils'));

% ---- conventions (all numbers below depend on these; the SIGN and SHAPE findings do not) ----------------
age = 24; p = 0.5;          % CIE observer: age, iris pigmentation (HDR-VDP defaults)
ppd = 60;                   % pixels per degree
N = 1024;                   % visible field N x N pixels = 17.1 deg; canvas 2N x 2N (34.1 deg), as HDR-VDP pads 2x
Om = (pi/180/ppd)^2;        % sr per pixel (small-angle mapping of the sphere to the plane)
printf('age %g, p %g, %g px/deg, canvas %d x %d px = %.1f deg, point at the canvas centre\n', age, p, ppd, 2*N, 2*N, 2*N/ppd);

a4 = (age/70)^4;            % CIE 135/1 GSF in sr^-1 (theta in deg), divided by its own integral factor
gsf = @(t) ((1 - 0.08*a4) * (9.2e6 ./ (1 + (t/0.0046).^2).^1.5 + 1.5e5 ./ (1 + (t/0.045).^2).^1.5) ...
          + (1 + 1.6*a4) * ((400 ./ (1 + (t/0.1).^2) + 3e-8 * t.^2) ...
                           + p * (1300 ./ (1 + (t/0.1).^2).^1.5 + 0.8 ./ (1 + (t/0.1).^2).^0.5)) ...
          + 2.5e-3 * p) / (1 + p * (0.0417 + 0.055*a4));

rho = create_cycdeg_image([2*N 2*N], ppd);              % HDR-VDP's own frequency grid (cycles/deg)
if exist('dirac') == 2 || exist('dirac') == 5
  M = hdrvdp_otf_cie99(rho, age, p); printf('dirac: native\n');
else
  addpath(fullfile(here, 'shim_zero')); Ma = hdrvdp_otf_cie99(rho, age, p); rmpath(fullfile(here, 'shim_zero'));
  addpath(fullfile(here, 'shim_inf'));  clear dirac hdrvdp_otf_cie99; Mb = hdrvdp_otf_cie99(rho, age, p); rmpath(fullfile(here, 'shim_inf'));
  printf('dirac: missing; two stand-ins give max |OTF_a - OTF_b| = %g (independent of the stand-in)\n', max(abs(Ma(:) - Mb(:))));
  M = Ma; addpath(fullfile(here, 'shim_zero'));             % keep one stand-in for the table below
end

I = zeros(2*N); c = N + 1; I(c, c) = 1;
A = real(ifft2(fft2(I) .* M));                           % ACTUAL

t = [linspace(0, 0.05, 200001)(1:end-1), logspace(log10(0.05), log10(60), 400001)];   % deg
w = gsf(t) * (pi/180)^2 .* 2 * pi .* t;
q = [0, logspace(-3, log10(ppd), 300)];
H = arrayfun(@(f) trapz(t, w .* besselj(0, 2*pi*f*t)), q); H = H / H(1);
C = real(ifft2(fft2(I) .* reshape(interp1(q, H, rho(:)), size(rho))));   % CONTROL

[X, Y] = meshgrid((1:2*N) - c); R = hypot(X, Y) / ppd;  % deg
E = gsf(R) * Om;                                         % EXPECTED: GSF integrated over each pixel
s = ((1:32) - 16.5) / 32;
for dy = -4:4, for dx = -4:4
  [sx, sy] = meshgrid(dx + s, dy + s); E(c+dy, c+dx) = mean(gsf(hypot(sx(:), sy(:)) / ppd)) * Om;
end, end
printf('energy on the canvas: actual %.4f (OTF normalised at omega -> 0), control %.4f, expected %.4f (GSF not renormalised on the canvas)\n', ...
       sum(A(:)), sum(C(:)), sum(E(:)));

% ---- headline: shape and sign of the point image (independent of any normalisation) -------------------
% log bins r/1.05 .. r*1.05 average out the pixel-lattice ringing; 'min' shows the negative excursions
ra = R * 60; bin = @(r) ra >= r/1.05 & ra < r*1.05;
printf('\nradial PSF [sr^-1], mean over log bins r/1.05..r*1.05 (actual: also the bin minimum)\n');
printf('  radius   actual(mean)  actual(min)   control     expected\n');
for r = [3 10 18 30 60 120]
  m = bin(r); printf('%6d''  %11.3g  %11.3g  %10.3g  %10.3g\n', r, mean(A(m)) / Om, min(A(m)) / Om, mean(C(m)) / Om, mean(E(m)) / Om);
end
printf('minimum of the point image: actual %.3g, control %.3g, expected %.3g (unit total energy)\n', min(A(:)), min(C(:)), min(E(:)));
printf('actual: pixels < 0 beyond 10'': %.0f %%; total energy in negative pixels %.2e (control %.2e)\n', ...
       100 * mean(A(ra > 10) < 0), -sum(A(A < 0)), -sum(C(C < 0)));
printf('\nOTF   rho[cpd]   control (Hankel)   hdrvdp_otf_cie99\n');
for f = [0.1 0.3 1 3 10 30]
  printf('      %6.1f     %8.4f           %8.4f\n', f, interp1(q, H, f), hdrvdp_otf_cie99(f, age, p));
end
% secondary (depends on the conventions above): encircled energy, expected also renormalised on the canvas
printf('\nencircled energy, pixel centres within r (secondary; convention-dependent)\n  r       actual   control  expected  expected/canvas-sum\n');
for r = [1 10 60]
  m = ra <= r; printf('%5d''  %7.4f  %7.4f  %7.4f   %7.4f\n', r, sum(A(m)), sum(C(m)), sum(E(m)), sum(E(m)) / sum(E(:)));
end

% ---- radial profile for the plot -----------------------------------------------------------------------
rr = logspace(log10(0.8), log10(120), 70);                % arcmin, log bins r/1.05..r*1.05
f = fopen(fullfile(here, 'repro_profile.csv'), 'w'); fprintf(f, 'r_arcmin,actual_mean,actual_min,control_mean,expected_mean\n');
for r = rr, m = bin(r); fprintf(f, '%g,%g,%g,%g,%g\n', r, mean(A(m)) / Om, min(A(m)) / Om, mean(C(m)) / Om, mean(E(m)) / Om); end
fclose(f);
