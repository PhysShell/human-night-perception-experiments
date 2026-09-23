function thisWindow = ieNewGraphWin(thisWindow, fType, varargin)
% Octave shim for ISETCam gui/ieNewGraphWin.m (GUI helper only, no computation).
% Upstream uses MATLAB graphics-object dot syntax (thisWindow.Name = ...), which
% fails in Octave ("scalar cannot be indexed with ."). Here: plain figure().
if nargin < 1 || isempty(thisWindow), thisWindow = figure('visible','off'); end
end
