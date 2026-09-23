function ieInit()
% Octave shim for ISETCam utility/ieInit.m (wrapper, not a model).
% The upstream ieInit is a script whose local function localCalledFromUnitTest
% is defined after its first use; GNU Octave 11 cannot resolve that
% ("'localCalledFromUnitTest' undefined near line 42"). This shim performs the
% same Octave-specific steps the upstream file lists (pkg loads, ieInitSession)
% and nothing else.
pkg load general; pkg load image; pkg load io; pkg load optiminterp; pkg load signal; pkg load statistics;
warning('off','all');
close all;
evalin('base','clear global');
evalin('base','ieInitSession;');
end
