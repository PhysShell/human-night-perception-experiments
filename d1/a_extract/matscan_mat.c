/* Prints the colour matrix pcond's matscan() applies for XYZE input: compxyz2rgbWBmat(mat, outprims),
   compiled verbatim against Radiance src/common/spec_rgb.c. Output primaries = Rec.709 as passed to pcond -p. */
#include <stdio.h>
#include "color.h"
int main(void) {
    RGBPRIMS pr = {{0.640f, 0.330f}, {0.300f, 0.600f}, {0.150f, 0.060f}, {0.3127f, 0.3290f}};
    COLORMAT m; if (!compxyz2rgbWBmat(m, pr)) return 1;
    for (int i = 0; i < 3; i++) printf("%.9g %.9g %.9g\n", m[i][0], m[i][1], m[i][2]);
    return 0;
}
