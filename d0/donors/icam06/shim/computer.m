function c = computer(varargin)
% SHIM (d0): iCAM06 V1.3 selects its output branch with strcmp(computer,'PCWIN');
% any other value selects the author's Apple HD Cinema LCD profile branch.
% Returning 'PCWIN' selects the author's documented sRGB output branch unchanged.
c = 'PCWIN';
end
