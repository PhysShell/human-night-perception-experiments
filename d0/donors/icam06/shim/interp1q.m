function yi = interp1q(x, y, xi)
% SHIM (d0): MATLAB interp1q (quick 1-D linear interpolation, NaN outside the range)
% is not provided by GNU Octave 11. interp1 with its default 'linear' method and
% NaN extrapolation is the same operation. Used only by percentile() in iCAM06_disp.m.
yi = interp1(x, y, xi);
end
