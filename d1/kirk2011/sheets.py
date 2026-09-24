#!/usr/bin/env python3
"""Contact sheets (VIEWING AID ONLY, not part of the donor).

    tracks/temporal-glare-2009/py.sh d1/kirk2011/sheets.py

Viewing aid (one rule for every scene-referred panel): scale the image so that ITS OWN log-average Rec.709
luminance is 0.18, clip to [0,1], sRGB OETF. The donor's core output is in arbitrary units (input x scale -> H ->
M^-1), so the input's key would saturate it; per-image key removes the absolute scale and keeps colour and relative
structure. Absolute/relative luminance numbers are in results.json. Display-referred 8-bit panels (plug-in final
output, its 8-bit input) are shown as their own sRGB codes, no aid.
  sheet_S1.png   : S1 input | NATIVE_DEFAULT final | DOCUMENTED_TARGET_CONFIG core | ladder x1e4, x1e6 core
  native_example.png : the plug-in's shipped 2012 intermediates (src/images): core output before Durand,
                       Durand stage (rebuilt here, byte-identical to the shipped file), shipped final output.png
"""
import os
import numpy as np
import OpenImageIO as oiio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
C = os.path.join(HERE, ".cache"); O = os.path.join(C, "out")
W = np.array([0.2126, 0.7152, 0.0722])


def rd(p):
    return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]


def aid(rgb):
    rgb = np.nan_to_num(np.maximum(rgb, 0))
    k = 0.18 / np.exp(np.mean(np.log(rgb @ W + 1e-9)))
    x = np.clip(rgb * k, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def sheet(panels, path, title, ncol):
    nrow = int(np.ceil(len(panels) / ncol))
    h, w = panels[0][1].shape[:2]
    fig, axs = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 4.2 * nrow * h / w + 0.6 * nrow), dpi=110)
    for ax in np.atleast_1d(axs).ravel():
        ax.axis("off")
    for ax, (lab, img) in zip(np.atleast_1d(axs).ravel(), panels):
        ax.imshow(np.clip(img, 0, 1), interpolation="lanczos"); ax.set_title(lab, fontsize=7.5)
    fig.suptitle(title, fontsize=8.5)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def main():
    s1 = rd(os.path.join(REPO, "d0/work/inputs/S1.exr"))
    fin = oiio.ImageBuf(os.path.join(O, "NATIVE_DEFAULT/S1_final.png")).get_pixels(oiio.FLOAT)[..., :3]
    panels = [("S1 input (abs. cd/m^2) [aid]", aid(s1)),
              ("NATIVE_DEFAULT: plug-in 8-bit input (= aid of S1)\n-> final output, own sRGB codes, no aid", fin),
              ("DOCUMENTED_TARGET_CONFIG core (7 mm pupil Td) [aid]", aid(rd(os.path.join(O, "DOCUMENTED_TARGET_CONFIG/S1.exr")))),
              ("SENSITIVITY_RUN S1 x1e2 core [aid]", aid(rd(os.path.join(O, "SENSITIVITY_RUN/S1_x1e2.exr")))),
              ("SENSITIVITY_RUN S1 x1e4 core [aid]", aid(rd(os.path.join(O, "SENSITIVITY_RUN/S1_x1e4.exr")))),
              ("SENSITIVITY_RUN S1 x1e6 core [aid]", aid(rd(os.path.join(O, "SENSITIVITY_RUN/S1_x1e6.exr"))))]
    sheet(panels, os.path.join(HERE, "sheet_S1.png"),
          "Kirk & O'Brien 2011 via Y. J. Lee GIMP plug-in, S1. [aid] = VIEWING AID, not part of the donor: "
          "each image scaled to its own log-average key 0.18, clip, sRGB", 3)
    S = os.path.join(C, "src/LOWLIGHT_LINUX/src/images")
    before = rd(os.path.join(S, "BeforeDurandTonemapping.exr"))
    after = oiio.ImageBuf(os.path.join(C, "native/After_rebuilt.ppm")).get_pixels(oiio.FLOAT)[..., :3]
    out = oiio.ImageBuf(os.path.join(S, "output.png")).get_pixels(oiio.FLOAT)[..., :3]
    sheet([("shipped core output (lms2display) [aid]", aid(before)),
           ("Durand stage rebuilt here (byte-identical to shipped\nAfterDurandTonemapping.ppm)", after),
           ("shipped final output.png (after reduceRange+blend)", out)],
          os.path.join(HERE, "native_example.png"),
          "Plug-in's shipped 2012 intermediates (src/images; original input not shipped). "
          "cmd: tone_mapping BeforeDurandTonemapping.exr out.ppm 50.0", 3)


if __name__ == "__main__":
    main()
