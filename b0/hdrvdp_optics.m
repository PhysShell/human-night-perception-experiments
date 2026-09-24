% B0 variants V2/V3 and the Vangorp adaptation oracle, using HDR-VDP 3.0.7's own functions unmodified:
%   V2 'hdrvdp' : HDR-VDP's custom-fit eye MTF (hdrvdp_mtf.m, 'hdrvdp')
%   V3 'cie'    : CIE 135/1 (Vos & van den Berg 1999) glare spread function as an OTF (hdrvdp_otf_cie99.m),
%                 age 24, iris pigmentation 0.5 (donor defaults)
% applied per channel as in hdrvdp_visual_pathway.m l.83-92 (create_cycdeg_image at 2x size,
% fast_conv_fft, clamp), then hdrvdp_local_adapt.m (Vangorp 2015, model #7) on the retinal luminance.
% Env: B0_IN (raw), B0_OUT_PREFIX, B0_MTF, B0_PPD. Writes <prefix>_retinal.raw and <prefix>_Lla.raw.
repo = getenv('REPO'); donor = fullfile(repo,'research-cache','hdrvdp3','src','hdrvdp-3.0.7');
pkg load statistics; pkg load image;
addpath(donor); addpath(fullfile(donor,'utils')); addpath(fullfile(repo,'tracks','hdrvdp3')); addpath(fullfile(repo,'b0','octave_shim'));
I = double(read_raw(getenv('B0_IN'))); ppd = str2double(getenv('B0_PPD')); mtf = getenv('B0_MTF');
ss = str2double(getenv('B0_SS')); if isnan(ss), ss = 1; end
% ss > 1: evaluate the donor OTF on an ss-times finer grid (pixel replication keeps radiance),
% then area-bin back. At the output grid the donor OTFs are not zero at Nyquist, which showed
% as a dashed cross through the lamp at pcond's exposure; the OTFs themselves are unchanged.
I0 = I; I = repelem(I, ss, ss, 1); ppd0 = ppd; ppd = ppd * ss;
mp = hdrvdp_parse_options('side-by-side', {'mtf', mtf, 'pixels_per_degree', ppd, 'use_gpu', false});
L = zeros(size(I));
if strcmp(mtf, 'none')
  L = I;
else
  rho2 = create_cycdeg_image(size(I(:,:,1))*2, ppd, false);
  F = hdrvdp_mtf(rho2, mp);
  for k = 1:size(I,3)
    L(:,:,k) = clamp(fast_conv_fft(I(:,:,k), F, 'replicate'), 1e-5, 1e10);
  end
end
if ss > 1
  [h, w, c] = size(I0); Lb = zeros(h, w, c);
  for k = 1:c, Lb(:,:,k) = reshape(sum(sum(reshape(L(:,:,k), ss, h, ss, w), 1), 3), h, w) / ss^2; end
  L = Lb; I = I0; ppd = ppd0;
end
Y = 0.2126*L(:,:,1) + 0.7152*L(:,:,2) + 0.0722*L(:,:,3);
Lla = hdrvdp_local_adapt(Y, ppd);
write_raw([getenv('B0_OUT_PREFIX') '_retinal.raw'], L);
write_raw([getenv('B0_OUT_PREFIX') '_Lla.raw'], Lla);
printf('%s: energy in/out %.6g / %.6g\n', mtf, sum(I(:)), sum(L(:)));
