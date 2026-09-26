// Headless driver (ours) for Filament's scotopicAdaptation() (google/filament, Apache-2.0,
// filament/src/details/ColorGrading.cpp). The function is #included VERBATIM from the pinned commit (setup.sh).
//   scotopic in.f32 out.f32 N nightAdaptation      (N float3 triplets, linear Rec.709, scaled by the caller)
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <math/vec3.h>
#include <math/vec4.h>
#include <math/mat3.h>
using namespace filament::math;
#include "scotopicAdaptation.inc"
int main(int argc, char** argv) {
    if (argc != 5) { fprintf(stderr, "usage: %s in.f32 out.f32 N nightAdaptation\n", argv[0]); return 1; }
    size_t n = strtoull(argv[3], nullptr, 10); float a = strtof(argv[4], nullptr);
    std::vector<float> buf(3 * n);
    FILE* f = fopen(argv[1], "rb"); if (!f || fread(buf.data(), sizeof(float), buf.size(), f) != buf.size()) return 2; fclose(f);
    for (size_t i = 0; i < n; i++) {
        float3 o = scotopicAdaptation(float3{buf[3 * i], buf[3 * i + 1], buf[3 * i + 2]}, a);
        buf[3 * i] = o.x; buf[3 * i + 1] = o.y; buf[3 * i + 2] = o.z;
    }
    f = fopen(argv[2], "wb"); fwrite(buf.data(), sizeof(float), buf.size(), f); fclose(f);
    return 0;
}
