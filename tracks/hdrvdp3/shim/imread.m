function I = imread( fname, varargin )
% Headless/format shim (tracks/hdrvdp3). The nixpkgs Octave 11.3 image stack is built on an
% 8-bit (Q8) GraphicsMagick and returns 16-bit PNGs as uint8 ("your version of GraphicsMagick
% limits images to 8 bits per pixel"), which silently makes HDR-VDP's shipped examples
% 257x too dark (they divide by 2^16-1). For 16-bit PNGs only we decode with OpenImageIO
% (nix develop python) and return uint16 exactly as MATLAB's imread would. All other files
% go to Octave's own imread.
repo = fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
is16 = false;
[~,~,ext] = fileparts( fname );
if strcmpi( ext, '.png' )
    fid = fopen( fname, 'r' ); hdr = fread( fid, 25, 'uint8' ); fclose( fid );
    is16 = numel(hdr) >= 25 && hdr(25) == 16;
end
if is16
    tmp = [tempname() '.raw'];
    cmd = sprintf( 'cd "%s" && PATH=/nix/var/nix/profiles/default/bin:$PATH nix develop -c python3 tracks/hdrvdp3/img2raw.py "%s" "%s" 2>/dev/null', ...
        repo, make_absolute_filename( fname ), tmp );
    [st, msg] = system( cmd );
    if st ~= 0, error( 'shim imread: OIIO conversion failed: %s', msg ); end
    I = read_raw( tmp ); delete( tmp );
else
    w = warning('off','all');
    oldp = path(); rmpath( fileparts( mfilename('fullpath') ) );
    try
        I = imread( fname, varargin{:} );
    catch err
        path( oldp ); warning(w); rethrow( err );
    end
    path( oldp ); warning(w);
end
end
