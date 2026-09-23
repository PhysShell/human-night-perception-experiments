function I = hdrread( fname )
% Format shim (tracks/hdrvdp3): Octave has no hdrread (MATLAB Image Processing Toolbox function).
% Decode Radiance .hdr with OpenImageIO (nix develop python) and return single RGB, unchanged values.
repo = fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
tmp = [tempname() '.raw'];
cmd = sprintf( 'cd "%s" && PATH=/nix/var/nix/profiles/default/bin:$PATH nix develop -c python3 tracks/hdrvdp3/img2raw.py "%s" "%s" 2>/dev/null', ...
    repo, make_absolute_filename( fname ), tmp );
[st, msg] = system( cmd );
if st ~= 0, error( 'shim hdrread: OIIO conversion failed: %s', msg ); end
I = read_raw( tmp ); delete( tmp );
end
