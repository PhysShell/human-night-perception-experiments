function tf = contains(str, pat, varargin)
% Octave shim for MATLAB built-in contains() (string utility, missing in Octave 11).
% Supports char/cellstr str and char/cellstr pat, optional 'IgnoreCase',true.
ic = numel(varargin) >= 2 && strcmpi(varargin{1},'IgnoreCase') && varargin{2};
if ischar(pat), pat = {pat}; end
if ischar(str), str = {str}; wasChar = true; else, wasChar = false; end
tf = false(size(str));
for i = 1:numel(str)
  s = str{i}; if ic, s = lower(s); end
  for j = 1:numel(pat)
    p = pat{j}; if ic, p = lower(p); end
    if ~isempty(strfind(s, p)), tf(i) = true; break; end
  end
end
if wasChar, tf = tf(1); end
end
