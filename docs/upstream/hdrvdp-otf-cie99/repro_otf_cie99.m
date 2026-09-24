% Minimal repro: HDR-VDP 3.0.7 hdrvdp_otf_cie99 vs the 2-D CIE 135/1 (Vos & van den Berg 1999) glare PSF.
% Input: a point source (delta). Expected: the 2-D radially symmetric CIE glare spread function, sr^-1.
% Actual: the point image after the OTF returned by hdrvdp_otf_cie99 (as hdrvdp_mtf(...,'cie') does).
% Usage (MATLAB or GNU Octave):  HDRVDP=/path/to/hdrvdp-3.0.7  then  run repro_otf_cie99.m
% Octave has no dirac(); octave_shim/dirac.m is added only when dirac is missing.
hd = getenv('HDRVDP'); addpath(fullfile(hd, 'utils'));
if exist('dirac') == 0, addpath(fullfile(fileparts(mfilename('fullpath')), 'octave_shim')); end
age = 24; p = 0.5; ppd = 60; N = 1024;                  % 60 px/deg, 17 x 17 deg field
Om = (pi/180/ppd)^2;                                    % sr per pixel

% --- the CIE 135/1 glare spread function, sr^-1, theta in deg (unit integral up to ~1 %) -------------
a4 = (age/70)^4;
gsf = @(t) ((1 - 0.08*a4) * (9.2e6 ./ (1 + (t/0.0046).^2).^1.5 + 1.5e5 ./ (1 + (t/0.045).^2).^1.5) ...
          + (1 + 1.6*a4) * ((400 ./ (1 + (t/0.1).^2) + 3e-8 * t.^2) ...
                           + p * (1300 ./ (1 + (t/0.1).^2).^1.5 + 0.8 ./ (1 + (t/0.1).^2).^0.5)) ...
          + 2.5e-3 * p) / (1 + p * (0.0417 + 0.055*a4));

% --- ACTUAL: delta through hdrvdp_otf_cie99, 2x padded FFT convolution as in hdrvdp_visual_pathway ----
I = zeros(2*N); c = N + 1; I(c, c) = 1;                  % unit energy at the centre of a 2N x 2N canvas
rho = create_cycdeg_image([2*N 2*N], ppd);
A = real(ifft2(fft2(I) .* hdrvdp_otf_cie99(rho, age, p)));

% --- EXPECTED: the same GSF integrated over each pixel (32x32 sub-samples in the central 9x9 pixels) ---
[X, Y] = meshgrid((1:2*N) - c); R = hypot(X, Y) / ppd;  % deg
E = gsf(R) * Om;
s = ((1:32) - 16.5) / 32;
for dy = -4:4, for dx = -4:4
  [sx, sy] = meshgrid(dx + s, dy + s); E(c+dy, c+dx) = mean(gsf(hypot(sx(:), sy(:)) / ppd)) * Om;
end, end

% --- CONTROL: the 2-D (Hankel) OTF of the same GSF, tabulated and applied with the same FFT pipeline ----
t = [linspace(0, 0.05, 200001)(1:end-1), logspace(log10(0.05), log10(60), 400001)];   % deg
w = gsf(t) * (pi/180)^2 .* 2 * pi .* t;                 % deg^-2 * 2 pi theta
q = [0, logspace(-3, log10(ppd), 300)];
H = arrayfun(@(f) trapz(t, w .* besselj(0, 2*pi*f*t)), q); H = H / H(1);
C = real(ifft2(fft2(I) .* reshape(interp1(q, H, rho(:)), size(rho))));

% --- what to look at -------------------------------------------------------------------------------
ra = R * 60;                                            % arcmin
printf('energy in the %d x %d deg canvas: actual %.4f, expected %.4f\n', 2*N/ppd, 2*N/ppd, sum(A(:)), sum(E(:)));
printf('\nradial PSF [sr^-1] (annulus mean, +-0.5 px)\n  radius   actual      expected    control(2-D OTF)  expected/actual\n');
for r = [3 10 18 30 60 120 300]
  m = abs(ra - r) < 0.5 * 60 / ppd;
  printf('%6d''  %10.3g  %10.3g  %10.3g      %8.2f\n', r, mean(A(m)) / Om, mean(E(m)) / Om, mean(C(m)) / Om, mean(E(m)) / mean(A(m)));
end
printf('min of the point image: actual %.3g, control %.3g (a positive PSF has none below 0)\n', min(A(:)), min(C(:)));
printf('\nencircled energy (pixel centres within r)\n  r        actual   expected  control\n');
for r = [1 3 10 30 60 180 480]
  m = ra <= r; printf('%6d''  %7.4f  %7.4f  %7.4f\n', r, sum(A(m)), sum(E(m)), sum(C(m)));
end
% --- the OTFs themselves: 2-D (Hankel) transform of the GSF vs hdrvdp_otf_cie99 -----------------------
printf('\nOTF   rho[cpd]   2-D Hankel of GSF   hdrvdp_otf_cie99\n');
for q = [0.1 0.3 1 3 10 30]
  printf('      %6.1f     %8.4f            %8.4f\n', q, trapz(t, w .* besselj(0, 2*pi*q*t)), hdrvdp_otf_cie99(q, age, p));
end
printf(['\nNote: the terms 2 c^2 |w| K1(c |w|) in hdrvdp_otf_cie99 are the 1-D Fourier transform of (1+(x/c)^2)^-1.5;\n' ...
        'its 2-D (radial, Hankel) transform is 2 pi c^2 exp(-2 pi c rho).\n']);
