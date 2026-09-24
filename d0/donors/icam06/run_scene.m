% d0 driver: run the ORIGINAL iCAM06 V1.3 iCAM06_HDR on one raw float32 image.
% Env: ICAM_IN (raw float32, row-major H x W x 3, linear Rec.709/D65, Y in cd/m^2),
%      ICAM_H, ICAM_W, ICAM_OUT (raw uint8 row-major H x W x 3), ICAM_ARGS (e.g. "0 0.7 1.2" or "" for defaults)
src = getenv('ICAM_SRC'); addpath(src);       % d0/work/donors/icam06/src_pristine (d0/donors/icam06/setup.sh)
addpath(getenv('ICAM_SHIM'));                 % d0/work/donors/icam06/shim
pkg load image
H = str2double(getenv('ICAM_H')); W = str2double(getenv('ICAM_W'));
fid = fopen(getenv('ICAM_IN'),'r'); v = fread(fid, Inf, 'single=>double'); fclose(fid);
img = permute(reshape(v, [3 W H]), [3 2 1]); clear v
args = str2num(getenv('ICAM_ARGS'));
cd(src);
if isempty(args)
  outImage = iCAM06_HDR(img);                 % NATIVE_DEFAULT: max_L=20000, p=0.7, gamma_value=1
else
  outImage = iCAM06_HDR(img, args(1), args(2), args(3));
end
printf('out %s %s min %d max %d\n', class(outImage), mat2str(size(outImage)), min(outImage(:)), max(outImage(:)));
fid = fopen(getenv('ICAM_OUT'),'w'); fwrite(fid, permute(outImage,[3 2 1])(:), 'uint8'); fclose(fid);
