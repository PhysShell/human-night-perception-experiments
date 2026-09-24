// SPDX-License-Identifier: GPL-3.0-or-later
// Contains the call sequence of the plug-in's src/render.cc (GPL-3, Y. J. Lee), so this file is GPL-3.0-or-later.
// Headless driver (ours) for Y. J. Lee's "Low-Light Tone Mapper" GIMP plug-in (2012), which implements
// Kirk & O'Brien 2011. It replaces only the libgimp glue of src/render.cc and calls the plug-in's own,
// unmodified core functions in the same order with the same arguments:
//   HDRToLMSR (hdrToLMSR.cc) -> purkinje (purkinje.cc) -> lms2display (lms2display.cc)
//   -> tonemapping (tonemapping.cc: writes /tmp/BeforeDurandTonemapping.exr, runs `tone_mapping ... 50.0`)
//   -> imread("/tmp/AfterDurandTonemapping.ppm") -> reduceRange (reduceRange.cc: range reduction + blend with the
//      8-bit source image), exactly as render.cc does.
// The /tmp paths are hard-coded in the donor; run.py runs this driver in a private mount namespace in which /tmp
// is bind-mounted onto d1/kirk2011/.cache/tmp.
//
// Usage:
//   driver native8 <in_rgb8.raw> <w> <h> <exposure> <out_prefix>
//       the plug-in's own contract: 8-bit RGB image (as GIMP hands it over) scaled by `exposure` (default 64);
//       full pipeline. Writes <out_prefix>_core.f32 (lms2display output, float RGB),
//       <out_prefix>_blend.f32 (the purkinje() blend map), <out_prefix>_final.png (reduceRange output, 8-bit).
//   driver float <in_rgbf32.raw> <w> <h> <scale> <out_prefix>
//       ADAPTED: float linear RGB instead of 8-bit codes; hdrImage = input * scale (the same convertTo call
//       render.cc uses with the exposure). Stops after lms2display (the scene-domain core); writes _core.f32 and
//       _blend.f32. No Durand / reduceRange (they need the plug-in's 8-bit source image).
// Raw files: row-major, interleaved R,G,B (not OpenCV's BGR); run.py handles I/O.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include "cv.h"
#include "highgui.h"
#include <gtk/gtk.h>
#include <libgimp/gimp.h>
#include "main.h"
#include "hdrToLMSR.h"
#include "purkinje.h"
#include "lms2display.h"
#include "tonemapping.h"
#include "reduceRange.h"

using namespace cv;

// ---- libgimp glue replaced by no-ops (only used by convertOutputToDrawable, i.e. copying into a GIMP layer) ----
void gimp_drawable_mask_bounds(gint32, gint *x1, gint *y1, gint *x2, gint *y2) { *x1 = *y1 = *x2 = *y2 = 0; }
gint gimp_drawable_bpp(gint32) { return 3; }
guint gimp_tile_width(void) { return 64; }
void gimp_tile_cache_ntiles(gint) {}
void gimp_pixel_rgn_init(GimpPixelRgn *, GimpDrawable *, gint, gint, gint, gint, gboolean, gboolean) {}
void gimp_pixel_rgn_get_row(GimpPixelRgn *, guchar *, gint, gint, gint) {}
void gimp_pixel_rgn_set_row(GimpPixelRgn *, const guchar *, gint, gint, gint) {}

// Plug-in defaults: copied value-for-value from src/main.cc `default_tvals` (lines 79-95).
static MyTonemapVals plugin_defaults() {
  MyTonemapVals t;
  t.exposure = 64.0; t.redGreenVal = 0.0; t.blueYellowVal = 0.0; t.luminanceVal = 0.0; t.preview = 1;
  t.kappa1 = .33; t.kappa2 = .5; t.rho1 = .8; t.rho2 = .139; t.rho3 = .4; t.rho4 = .6; t.alpha = .6189;
  t.y = 15.0; t.z = .24;
  return t;
}

// bgr=true: OpenCV BGR Mat (flip to RGB). lms2display()'s output is already in R,G,B channel order (it is
// M^-1 applied to the L,M,S planes; tonemapping.cc writes channel 0 as "R"), so it is written with bgr=false.
static void write_f32(const std::string &path, const Mat &m, bool bgr) {
  FILE *f = fopen(path.c_str(), "wb");
  if (!f) { perror(path.c_str()); exit(2); }
  if (m.type() == CV_32FC3) {
    std::vector<float> row(m.cols * 3);
    for (int r = 0; r < m.rows; r++) {
      for (int c = 0; c < m.cols; c++) {
        const Vec3f &v = m.at<Vec3f>(r, c);
        for (int k = 0; k < 3; k++) row[c * 3 + k] = bgr ? v[2 - k] : v[k];
      }
      fwrite(row.data(), sizeof(float), row.size(), f);
    }
  } else {
    for (int r = 0; r < m.rows; r++) fwrite(m.ptr<float>(r), sizeof(float), m.cols, f);
  }
  fclose(f);
}

int main(int argc, char **argv) {
  if (argc != 7) { fprintf(stderr, "usage: %s native8|float in.raw w h exposure out_prefix\n", argv[0]); return 1; }
  std::string mode = argv[1], in = argv[2], out = argv[6];
  int cols = atoi(argv[3]), rows = atoi(argv[4]);
  MyTonemapVals tv = plugin_defaults();
  tv.exposure = (gfloat)atof(argv[5]);
  MyTonemapVals *tvals = &tv;

  FILE *f = fopen(in.c_str(), "rb");
  if (!f) { perror(in.c_str()); return 2; }
  Mat *inputImg = new Mat(rows, cols, CV_8UC3);
  Mat inputF;
  if (mode == "native8") {
    // render.cc: inputImg->at<Vec3b>(i,j)[2-k] = row[k]  (GIMP RGB -> OpenCV BGR)
    std::vector<unsigned char> row(cols * 3);
    for (int i = 0; i < rows; i++) {
      if (fread(row.data(), 1, row.size(), f) != row.size()) { fprintf(stderr, "short read\n"); return 2; }
      for (int j = 0; j < cols; j++) for (int k = 0; k < 3; k++) inputImg->at<Vec3b>(i, j)[2 - k] = row[3 * j + k];
    }
  } else if (mode == "float") {
    inputF = Mat(rows, cols, CV_32FC3);
    std::vector<float> row(cols * 3);
    for (int i = 0; i < rows; i++) {
      if (fread(row.data(), sizeof(float), row.size(), f) != row.size()) { fprintf(stderr, "short read\n"); return 2; }
      for (int j = 0; j < cols; j++) for (int k = 0; k < 3; k++) inputF.at<Vec3f>(i, j)[2 - k] = row[3 * j + k];
    }
  } else { fprintf(stderr, "bad mode\n"); return 1; }
  fclose(f);

  // ---- from here on: render.cc, lines "tonemapping" .. "reduceRange", with the GIMP calls removed ----
  Mat *LMtx = new Mat(rows, cols, CV_32FC1);
  Mat *MMtx = new Mat(rows, cols, CV_32FC1);
  Mat *SMtx = new Mat(rows, cols, CV_32FC1);
  Mat *RMtx = new Mat(rows, cols, CV_32FC1);
  Mat *hdrImage = new Mat(rows, cols, CV_32FC3);
  Mat *lms = new Mat(rows, cols, CV_32FC3);
  Mat *blend = new Mat(rows, cols, CV_32FC1);
  Mat *lms2displayOutput = new Mat(rows, cols, CV_32FC3);
  float scaleToHDR = tvals->exposure;
  printf("scaleToHDR is %f\n", scaleToHDR);
  if (mode == "native8") inputImg->convertTo(*hdrImage, CV_32FC3, scaleToHDR, 0.0);
  else inputF.convertTo(*hdrImage, CV_32FC3, scaleToHDR, 0.0);  // ADAPTED: float source, same call
  HDRToLMSR(hdrImage, LMtx, MMtx, SMtx, RMtx);
  purkinje(LMtx, MMtx, SMtx, RMtx, lms, blend, tvals);
  lms2display(lms, lms2displayOutput);
  write_f32(out + "_core.f32", *lms2displayOutput, false);
  write_f32(out + "_blend.f32", *blend, false);
  if (mode == "float") { printf("core done\n"); return 0; }

  tonemapping(lms2displayOutput);
  Mat reduceRangeInput = imread("/tmp/AfterDurandTonemapping.ppm", 1);
  if (reduceRangeInput.empty()) { fprintf(stderr, "Durand stage produced no output\n"); return 3; }
  GimpDrawable dummy; dummy.drawable_id = 0; dummy.width = cols; dummy.height = rows; dummy.bpp = 3;
  std::string png = out + "_final.png";
  reduceRange(&reduceRangeInput, blend, rows, cols, png.c_str(), *inputImg, &dummy);
  printf("full pipeline done\n");
  return 0;
}
