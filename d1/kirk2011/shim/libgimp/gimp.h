/* Shim (ours) replacing libgimp for a headless build.
   - glib scalar typedefs as glib defines them (gint = int, gfloat = float, ...).
   - The GIMP drawable / pixel-region calls used by reduceRange.cc's convertOutputToDrawable() (pure GIMP glue:
     it copies the finished 8-bit result into a GIMP layer) are declared here and implemented as no-ops in
     driver.cpp; reduceRange() also writes the same 8-bit result with cv::imwrite, which the driver uses.
   No donor arithmetic is touched. */
#pragma once
#include <stdlib.h>
typedef int gint; typedef unsigned int guint; typedef int gint32; typedef float gfloat; typedef double gdouble;
typedef gint gboolean; typedef unsigned char guchar; typedef char gchar; typedef void* gpointer;
#ifndef FALSE
#define FALSE (0)
#endif
#ifndef TRUE
#define TRUE (!FALSE)
#endif
#ifndef MIN
#define MIN(a,b) (((a) < (b)) ? (a) : (b))
#endif
#define g_new(type, n) ((type *) malloc(sizeof(type) * (size_t)(n)))
static inline void g_free(void *p) { free(p); }
typedef struct { gint32 drawable_id; guint width, height, bpp; } GimpDrawable;
typedef struct { void *dummy; } GimpPixelRgn;
void gimp_drawable_mask_bounds(gint32 id, gint *x1, gint *y1, gint *x2, gint *y2);
gint gimp_drawable_bpp(gint32 id);
guint gimp_tile_width(void);
void gimp_tile_cache_ntiles(gint n);
void gimp_pixel_rgn_init(GimpPixelRgn *r, GimpDrawable *d, gint x, gint y, gint w, gint h, gboolean dirty, gboolean shadow);
void gimp_pixel_rgn_get_row(GimpPixelRgn *r, guchar *buf, gint x, gint y, gint w);
void gimp_pixel_rgn_set_row(GimpPixelRgn *r, const guchar *buf, gint x, gint y, gint w);
