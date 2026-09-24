function h = figure(varargin)
% SHIM (d0): headless octave-cli has no graphics toolkit; iCAM06_HDR.m calls
% "figure; imshow(outImage);" only for an on-screen preview. No-op.
h = [];
end
