function write_raw( fname, I )
% Write single-precision H x W x C array into the raw container read by raw2exr.py.
I = single( I ); [h,w,c] = size( I );
fid = fopen( fname, 'w', 'ieee-le' ); fwrite( fid, [h w c 3], 'int32' );
fwrite( fid, permute( I, [3 2 1] ), 'single' ); fclose( fid );
end
