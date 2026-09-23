function ax = nexttile(varargin)
% Octave shim: MATLAB nexttile missing in Octave 11. Plot layout only; opens a new invisible figure.
figure('visible','off'); ax = gca;
end
