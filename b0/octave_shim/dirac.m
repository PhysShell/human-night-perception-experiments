function y = dirac(varargin)
% Octave compatibility shim for MATLAB's dirac (Symbolic Math Toolbox), used only because
% HDR-VDP 3.0.7 utils/hdrvdp_otf_cie99.m calls dirac(omega) and dirac(2, omega). MATLAB semantics
% for numeric input: dirac(x) = 0 for x ~= 0, Inf at 0; dirac(n, x) (n-th derivative) = 0 for
% x ~= 0, Inf at 0. hdrvdp_otf_cie99 only evaluates it at omega > 0 in practice and overwrites
% omega < 1e-4 with 1, so the CIE99 OTF is unchanged by this shim.
x = varargin{end};
y = zeros(size(x));
y(x == 0) = Inf;
end
