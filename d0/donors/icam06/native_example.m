% Native example exactly as in the iCAM06 V1.3 Readme.txt:
%   image = read_radiance('PeckLake.hdr'); outImage = iCAM06_HDR(image, 20000, 0.7, 1);
src = getenv('ICAM_SRC'); addpath(src);
addpath(getenv('ICAM_SHIM'));          % shim dir first on the path
pkg load image

cd(src);
image = read_radiance('PeckLake.hdr');
outImage = iCAM06_HDR(image, 20000, 0.7, 1);
printf('class %s size %s min %d max %d\n', class(outImage), mat2str(size(outImage)), min(outImage(:)), max(outImage(:)));
imwrite(outImage, getenv('NATIVE_OUT'));
