function y = dirac(varargin)
% GNU Octave stand-in for the Symbolic Toolbox dirac() (variant B: Inf at x == 0, else 0).
x = varargin{end}; y = zeros(size(x)); y(x == 0) = Inf;
end
