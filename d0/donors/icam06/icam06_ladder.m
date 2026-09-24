% D0.1 iCAM06 absolute-level ladder driver. Calls the ORIGINAL iCAM06 V1.3 sub-functions in exactly the order of
% iCAM06_HDR.m (max_L = 0 branch: input used as absolute cd/m^2), and additionally saves XYZ_tm, the model's output
% BEFORE iCAM06_disp (which divides by max Y and stretches the 1st-99th RGB percentiles to the display).
% Env: ICAM_IN (raw float32 H x W x 3 linear Rec.709, cd/m^2), ICAM_H, ICAM_W, ICAM_P, ICAM_GAMMA,
%      ICAM_OUT (uint8 sRGB, native display step), ICAM_XYZ (float32 XYZ_tm).
src = getenv('ICAM_SRC'); addpath(src); addpath(getenv('ICAM_SHIM')); pkg load image
H = str2double(getenv('ICAM_H')); W = str2double(getenv('ICAM_W'));
p = str2double(getenv('ICAM_P')); gamma_value = str2double(getenv('ICAM_GAMMA'));
fid = fopen(getenv('ICAM_IN'),'r'); v = fread(fid, Inf, 'single=>double'); fclose(fid);
img = permute(reshape(v, [3 W H]), [3 2 1]); clear v
cd(src);
M = [0.412424 0.212656 0.0193324; 0.357579 0.715158 0.119193; 0.180464 0.0721856 0.950444];   % as iCAM06_HDR.m
XYZimg = reshape(reshape(img, H*W, 3) * M, H, W, 3);
XYZimg(find(XYZimg<0.00000001)) = 0.00000001;
[base_img(:,:,1), detail_img(:,:,1)] = fastbilateralfilter(XYZimg(:,:,1));
[base_img(:,:,2), detail_img(:,:,2)] = fastbilateralfilter(XYZimg(:,:,2));
[base_img(:,:,3), detail_img(:,:,3)] = fastbilateralfilter(XYZimg(:,:,3));
white = iCAM06_blur(XYZimg, 2); XYZ_adapt = iCAM06_CAT(base_img, white);
white = iCAM06_blur(XYZimg, 3); XYZ_tc = iCAM06_TC(XYZ_adapt, white, p);
XYZ_d = XYZ_tc .* iCAM06_LocalContrast(detail_img, base_img);
XYZ_p = iCAM06_IPT(XYZ_d, base_img, gamma_value);
XYZ_tm = iCAM06_invcat(XYZ_p);
fid = fopen(getenv('ICAM_XYZ'),'w'); fwrite(fid, permute(XYZ_tm,[3 2 1])(:), 'single'); fclose(fid);
outImage = uint8(iCAM06_disp(XYZ_tm));
fid = fopen(getenv('ICAM_OUT'),'w'); fwrite(fid, permute(outImage,[3 2 1])(:), 'uint8'); fclose(fid);
printf('XYZ_tm Y min %g median %g max %g\n', min(min(XYZ_tm(:,:,2))), median(XYZ_tm(:,:,2)(:)), max(max(XYZ_tm(:,:,2))));
