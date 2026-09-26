/* pcond's gamut step, verbatim: clipgamut() linked from Radiance src/common/spec_rgb.c; greypoint() copied verbatim
   from src/px/pcond2.c:143-158 (static there). Reads N float RGB triples, writes the clipped triples.
   usage: clipgamut in.f32 out.f32 N */
#include <stdio.h>
#include <stdlib.h>
#include "color.h"
static double
greypoint(			/* compute gamut mapping grey target */
	COLOR col
)
{
	COLOR	gryc;
	int	i;
				/* improves saturated color rendering */
	copycolor(gryc, col);
	for (i = 3; i--; )
		if (gryc[i] > 1)
			gryc[i] = 1;
		else if (gryc[i] < 0)
			gryc[i] = 0;
	return(bright(gryc));
}
int main(int argc, char **argv) {
    long n = atol(argv[3]); float *b = malloc(n * 3 * sizeof(float)); FILE *f = fopen(argv[1], "rb");
    if (fread(b, sizeof(float), n * 3, f) != (size_t)(n * 3)) return 1; fclose(f);
    for (long i = 0; i < n; i++) { COLOR c; setcolor(c, b[3*i], b[3*i+1], b[3*i+2]);
        clipgamut(c, greypoint(c), CGAMUT, cblack, cwhite); b[3*i] = c[0]; b[3*i+1] = c[1]; b[3*i+2] = c[2]; }
    f = fopen(argv[2], "wb"); fwrite(b, sizeof(float), n * 3, f); fclose(f); return 0;
}
