#!/usr/bin/env python3
"""S8 candidate: a real, luminance-calibrated night HDR photograph converted to the stimulus-pack
convention (linear Rec.709/D65 float32 EXR, Y = 0.2126R+0.7152G+0.0722B in cd/m^2, 32 px/deg,
plus a luminance-only PFM).  FORMAT CONVERSION ONLY - no vision model, no tone mapping.

Source: Mark Fairchild's HDR Photographic Survey, "Golden Gate (2)" (night, well after sunset).
  EXR   http://markfairchild.org/HDRPS/EXRs/GoldenGate(2).exr   (white-balanced Nikon D2x camera RGB)
  factor 0.28  (scene page + Data/GoldenGateData.xls row "(2)")
  camera->XYZ  D65-normalised matrix, D2xCharacterization.pdf p.1 / CIC15HDRSurvey.pdf Eq.1
  lens  18 mm (GoldenGateData.xls "Focal Length: 18mm"), Nikon D2x sensor 23.7 x 15.7 mm, 4288 x 2848 px
Writes ONLY to research-cache/datasets/S8/ (never stimuli/).  Licence: non-commercial research use,
"Mark Fairchild's HDR Photographic Survey" must be acknowledged; the outputs are derived data under the
same terms and are NOT to be committed.

Run:  nix develop -c python3 tracks/datasets/make_s8.py
"""
import json, math, os, hashlib
import numpy as np
import OpenImageIO as oiio

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "research-cache/datasets/fairchild/EXRs/GoldenGate(2).exr")
OUT = os.path.join(ROOT, "research-cache/datasets/S8")
FACTOR = 0.28
M_CAM2XYZ = np.array([[0.4024, 0.4610, 0.0871],
                      [0.1904, 0.7646, 0.0450],
                      [-0.0249, 0.1264, 0.9873]])
# CIE XYZ -> linear sRGB/Rec.709 (D65), IEC 61966-2-1
M_XYZ2709 = np.array([[3.2404542, -1.5371385, -0.4985314],
                      [-0.9692660, 1.8760108, 0.0415560],
                      [0.0556434, -0.2040259, 1.0572252]])
Yw = np.array([0.2126, 0.7152, 0.0722])
F_MM, SENSOR_W_MM, SENSOR_W_PX = 18.0, 23.7, 4288
PITCH_MM = SENSOR_W_MM / SENSOR_W_PX
PPD_NATIVE = F_MM * math.tan(math.radians(1.0)) / PITCH_MM      # px/deg at the optical axis
PPD = 32.0
W, H = 1024, 512
CROP_CENTRE = (2144.0, 1300.0)   # (x, y) native px; optical centre is (2144, 1423.5)
SKY_CHECK = dict(rows=(50, 550), cols=(1400, 1750), measured_Y=0.63, measured_xy=(0.26, 0.23))


def area_weights(n_out, x0, n_in_span, n_in):
    """1-D exact area-overlap resampling matrix: out pixel i covers native [x0+i*s, x0+(i+1)*s)."""
    s = n_in_span / n_out
    Wm = np.zeros((n_out, n_in))
    for i in range(n_out):
        a, b = x0 + i * s, x0 + (i + 1) * s
        for j in range(int(math.floor(a)), int(math.ceil(b))):
            ov = min(b, j + 1) - max(a, j)
            if ov > 0 and 0 <= j < n_in:
                Wm[i, j] = ov
        Wm[i] /= Wm[i].sum()
    return Wm


def write_exr(path, img, half=False):
    h, w, c = img.shape
    spec = oiio.ImageSpec(w, h, c, oiio.HALF if half else oiio.FLOAT)
    spec.attribute("compression", "zip")
    b = oiio.ImageBuf(spec)
    b.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(img, np.float32))
    assert b.write(path), b.geterror()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    cam = oiio.ImageBuf(SRC).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)
    nh, nw = cam.shape[:2]
    raw_max = cam.max()
    clipped = (cam >= raw_max * 0.999).any(-1)
    xyz = cam @ M_CAM2XYZ.T * FACTOR
    Ycol = xyz[..., 1]
    rgb = xyz @ M_XYZ2709.T
    neg_frac = float((rgb < 0).any(-1).mean())
    rgb_c = np.maximum(rgb, 0.0)                      # gamut clip to Rec.709 (documented)
    Yc = rgb_c @ Yw
    dY_total = float(Yc.sum() / Ycol.sum() - 1)

    # calibration check against Fairchild's CS-100 point "(2) Sky Above Left Tower" 0.63 cd/m^2
    r0, r1 = SKY_CHECK["rows"]; c0, c1 = SKY_CHECK["cols"]
    sky = xyz[r0:r1, c0:c1].reshape(-1, 3)
    sky_Y = float(np.median(sky[:, 1]))
    sxyz = sky.mean(0); sky_xy = (float(sxyz[0] / sxyz.sum()), float(sxyz[1] / sxyz.sum()))

    # native full-frame copy (half EXR, Rec.709, cd/m^2) for users who want their own geometry
    write_exr(os.path.join(OUT, "S8_native_rec709_cdm2.exr"), rgb_c, half=True)

    # 32 px/deg crop, exact area resampling (preserves sum(L * Omega_px) up to rectilinear distortion)
    span_w, span_h = W * PPD_NATIVE / PPD, H * PPD_NATIVE / PPD
    x0, y0 = CROP_CENTRE[0] - span_w / 2, CROP_CENTRE[1] - span_h / 2
    Wx = area_weights(W, x0, span_w, nw)
    Wy = area_weights(H, y0, span_h, nh)
    img = np.stack([Wy @ rgb_c[..., c] @ Wx.T for c in range(3)], -1).astype(np.float32)
    clip32 = (Wy @ clipped.astype(float) @ Wx.T) > 0
    write_exr(os.path.join(OUT, "S8.exr"), img)
    y = oiio.ImageBuf(oiio.ImageSpec(W, H, 1, oiio.FLOAT))
    y.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 1), np.ascontiguousarray((img @ Yw)[..., None], np.float32))
    y.write(os.path.join(OUT, "S8_Y.pfm"))
    # clip mask: 32 px/deg pixels that contain any clipped native pixel
    write_exr(os.path.join(OUT, "S8_clipmask.exr"), clip32[..., None].astype(np.float32))

    # preview (log10 luminance, -3..+1.6 -> 0..255), informational only
    Y32 = img @ Yw
    v = np.clip((np.log10(np.maximum(Y32, 1e-4)) + 3.0) / 4.6, 0, 1)
    g = (np.repeat(v[..., None], 3, -1) * 255).astype(np.uint8)
    g[clip32] = [255, 0, 0]
    pb = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT8)); pb.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), g)
    pb.write(os.path.join(OUT, "S8_preview_log10Y_clipred.png"))

    # off-axis px/deg variation inside the crop (rectilinear: radial ppd ~ ppd0 / cos^2(theta))
    cx, cy = nw / 2, nh / 2
    corners = [(x0, y0), (x0 + span_w, y0), (x0, y0 + span_h), (x0 + span_w, y0 + span_h)]
    th = max(math.atan(math.hypot(px - cx, py - cy) * PITCH_MM / F_MM) for px, py in corners)

    meta = {
        "id": "S8",
        "status": "CANDIDATE (not in stimuli/pack; coordinator decides)",
        "label": "ADAPTED (format conversion of third-party calibrated data; no vision model applied)",
        "white_balance_note": "Fairchild's EXRs were white-balanced to the in-camera white point before merging "
                              "(CIC15HDRSurvey.pdf, 'Imaging Procedures'), so luminance is absolute but chromaticity "
                              "is NOT scene-absolute (sky: image xy vs CS-100 xy in calibration_check)",
        "what": "real night photograph: Golden Gate Bridge + San Francisco well after sunset, from Marin Headlands "
                "(Fairchild HDR Photographic Survey 'Golden Gate (2)'); distant unresolved bridge/city lamps at km range",
        "source": {"exr": "http://markfairchild.org/HDRPS/EXRs/GoldenGate(2).exr", "exr_sha256": sha(SRC),
                   "page": "http://markfairchild.org/HDRPS/Scenes/GoldenGate(2).html",
                   "data": "http://markfairchild.org/HDRPS/Data/GoldenGateData.xls",
                   "characterization": "http://markfairchild.org/HDRPS/D2xCharacterization.pdf"},
        "licence": "Copyright 2006-2007 Mark D. Fairchild, all rights reserved; free for research and non-commercial "
                   "publication; commercial publication prohibited; acknowledge \"Mark Fairchild's HDR Photographic Survey\". "
                   "Derived files: same terms, DO NOT COMMIT (fetch + regenerate instead).",
        "conversion": "camera RGB x D65-normalised D2x matrix -> XYZ, x luminance factor 0.28 -> cd/m^2, "
                      "XYZ -> linear Rec.709 (IEC 61966-2-1), negative channels clipped to 0, "
                      "exact area-average resampling to 32 px/deg (tracks/datasets/make_s8.py)",
        "luminance_factor": FACTOR,
        "units": "cd/m^2 (Y of linear Rec.709/D65 RGB)",
        "px_per_deg": PPD,
        "px_per_deg_native_estimated": PPD_NATIVE,
        "px_per_deg_basis": "ESTIMATED: 18 mm nominal zoom focal length (scene data sheet) and Nikon D2x 23.7 mm / 4288 px "
                            "sensor; no EXIF in the EXR; lens distortion unknown; image 4288x2847 so treated as uncropped "
                            "with optical centre at the image centre",
        "max_off_axis_deg_in_crop": math.degrees(th),
        "px_per_deg_radial_at_crop_corner_relative": 1 / math.cos(th) ** 2,
        "crop_native_px": {"x0": x0, "y0": y0, "w": span_w, "h": span_h},
        "size_px": [W, H], "fov_deg": [W / PPD, H / PPD], "frames": 1,
        "L_min": float(Y32.min()), "L_max": float(Y32.max()),
        "L_median": float(np.median(Y32)),
        "native_size_px": [nw, nh],
        "native_Y_max_cd_m2": float(Ycol.max()),
        "clipping": {"raw_max_value": float(raw_max), "native_px_at_ceiling": int(clipped.sum()),
                     "S8_px_touched_by_clipping": int(clip32.sum()),
                     "note": "the HDR merge has a hard ceiling (raw 128.875 -> ~36 cd/m^2): every lamp core is "
                             "CLIPPED, so lamp luminances/energies are LOWER BOUNDS; the scene is NOT a valid "
                             "photometric reference for the point sources themselves, only for the surround."},
        "gamut": {"frac_px_with_negative_rec709": neg_frac, "relative_change_of_total_Y_by_clip": dY_total},
        "camera_optics_note": "the photograph already contains the Nikkor lens PSF/flare and sensor MTF; any "
                              "eye-optics model applied on top double-counts some veiling glare near lamps",
        "calibration_check": {"reference": "GoldenGateData.xls row (2) 'Sky Above Left Tower' Y=0.63 cd/m^2 x=0.26 y=0.23 "
                                           "(Minolta CS-100, 1 deg)",
                              "region_native_rows_cols": [SKY_CHECK["rows"], SKY_CHECK["cols"]],
                              "image_median_Y": sky_Y, "image_mean_xy": sky_xy,
                              "ratio": sky_Y / SKY_CHECK["measured_Y"]},
        "files": ["S8.exr", "S8_Y.pfm", "S8_clipmask.exr", "S8_native_rec709_cdm2.exr",
                  "S8_preview_log10Y_clipred.png"],
    }
    meta["sha256"] = {f: sha(os.path.join(OUT, f)) for f in meta["files"]}
    with open(os.path.join(OUT, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps({k: meta[k] for k in ("px_per_deg_native_estimated", "L_min", "L_max", "L_median",
                                           "clipping", "gamut", "calibration_check", "max_off_axis_deg_in_crop")},
                     indent=1))


if __name__ == "__main__":
    main()
