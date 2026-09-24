function y = dirac(varargin)
% Minimal numeric stand-in for the Symbolic Toolbox dirac() used by hdrvdp_otf_cie99 (GNU Octave only):
% dirac(x) or dirac(n, x): 0 away from x = 0, Inf at 0. Only the x ~= 0 values matter for the repro.
x = varargin{end}; y = zeros(size(x)); y(x == 0) = Inf;
end
