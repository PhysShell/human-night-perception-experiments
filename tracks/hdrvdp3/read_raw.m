function I = read_raw( fname )
% Read the trivial raw container written by img2raw.py / write_raw.m (format conversion only).
fid = fopen( fname, 'r', 'ieee-le' ); hdr = fread( fid, 4, 'int32' )';
types = { 'uint8', 'uint16', 'single' };
d = fread( fid, prod(hdr(1:3)), [types{hdr(4)} '=>' types{hdr(4)}] ); fclose( fid );
I = permute( reshape( d, [hdr(3) hdr(2) hdr(1)] ), [3 2 1] );
end
