#!/usr/bin/env python3
"""Reproducible digitization of Ginis et al. 2012 (J Vis 12(3):20) Fig. 7 (and Fig. 6 GP cross-check).
Label: DIGITIZED_EXTERNAL_VALIDATION.

  tracks/temporal-glare-2009/py.sh b1/c0_ginis/digitize.py
    reads  b1/c0_ginis/calib.json, b1/c0_ginis/.cache/fig-00{1,2}.jpg (pdfimages -j of the Artal-lab PDF; sha256 checked)
    writes b1/c0_ginis/ginis2012_fig7_digitized.csv       (per-pixel-column trace, log10 PSF [sr^-1] as printed)
           b1/c0_ginis/ginis2012_fig7_grid.csv            (0.25-deg grid + digitization uncertainty)
           b1/c0_ginis/.cache/digitize_meta.json

Method: linear least-squares pixel->data map from the tick centres in calib.json; curve pixels selected by an RGB
rule per curve; per pixel column the curve ordinate is the median row of the selected pixels (thick line centre).
Uncertainty: (a) 300 random perturbations of every tick centre by N(0, 2 px); (b) line-centre estimator
(median vs mean vs mid of min/max row). Both reported per grid angle; the total is their quadrature sum.
"""
import hashlib, json, os
import numpy as np
import matplotlib.image as mi

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "calib.json")))
RULES = {
    "GP": lambda r, g, b: (b - r > 35) & (b > 150) & (r < 185),
    "CS": lambda r, g, b: (r - b > 50) & (r > 180) & (g < 175),
    "VOS_VDB_1999_BLACK_SOLID": lambda r, g, b: np.maximum(np.maximum(r, g), b) < 90,
    "GP_RECONSTRUCTED": lambda r, g, b: (b - r > 60) & (b > 170),
}


def load(fig):
    p = os.path.join(HERE, C[fig]["image"])
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    assert h == C[fig]["image_sha256"], (p, h)
    im = mi.imread(p).astype(float)[..., :3]
    return im


def lin(ticks, rng=None, sd=0.0):
    v = np.array([float(k) for k in ticks]); px = np.array(list(ticks.values()))
    if rng is not None:
        px = px + rng.normal(0, sd, px.size)
    a, b = np.polyfit(px, v, 1)
    return lambda q: a * q + b, float(np.sqrt(np.mean((a * px + b - v) ** 2)))


def trace(fig, name):
    im = load(fig); r, g, b = im[..., 0], im[..., 1], im[..., 2]
    m = RULES[name](r, g, b)
    for x0, y0, x1, y1 in C[fig]["exclude_boxes_px"]:
        m[y0:y1, x0:x1] = False
    # stay inside the plot frame
    xt = C[fig]["x_ticks_px"]; yt = C[fig]["y_ticks_px"]
    xmin, xmax = min(xt.values()) + 4, max(xt.values()) - 4
    ymin, ymax = min(yt.values()) + 4, max(yt.values()) - 4
    m[:, : int(xmin)] = False; m[:, int(xmax):] = False; m[: int(ymin)] = False; m[int(ymax):] = False
    cols, med, mean, mid = [], [], [], []
    for x in range(m.shape[1]):
        rows = np.nonzero(m[:, x])[0]
        if rows.size < 3:
            continue
        if name == "VOS_VDB_1999_BLACK_SOLID":
            # lowest contiguous dark run in the column (solid curve lies below the dashed one beyond ~3 deg)
            splits = np.split(rows, np.nonzero(np.diff(rows) > 2)[0] + 1)
            rows = splits[-1]
            if rows.size < 2 or rows.size > 12:
                continue
        else:
            # keep the largest contiguous run (drops stray anti-aliasing pixels)
            splits = np.split(rows, np.nonzero(np.diff(rows) > 2)[0] + 1)
            rows = max(splits, key=len)
            if rows.size < 4:
                continue
        cols.append(x); med.append(np.median(rows)); mean.append(rows.mean()); mid.append(0.5 * (rows.min() + rows.max()))
    return np.array(cols, float), np.array(med), np.array(mean), np.array(mid)


def to_data(fig, cols, rows, rng=None, sd=0.0):
    fx, rx = lin(C[fig]["x_ticks_px"], rng, sd); fy, ry = lin(C[fig]["y_ticks_px"], rng, sd)
    return fx(cols), fy(rows), rx, ry


GRID = np.round(np.arange(0.5, 7.76, 0.25), 4)


def on_grid(x, y):
    o = np.argsort(x); x, y = x[o], y[o]
    out = np.interp(GRID, x, y, left=np.nan, right=np.nan)
    # refuse to interpolate across gaps wider than 0.1 deg (crossings / occlusion)
    for i, a in enumerate(GRID):
        if np.nan_to_num(np.min(np.abs(x - a)), nan=9) > 0.05:
            out[i] = np.nan
    return out


def main():
    rng = np.random.default_rng(12)
    meta = {"label": "DIGITIZED_EXTERNAL_VALIDATION", "curves": {}}
    rows_out = {}; grid_out = {"theta_deg": GRID}
    for fig, name in (("fig7", "GP"), ("fig7", "CS"), ("fig7", "VOS_VDB_1999_BLACK_SOLID"), ("fig6", "GP_RECONSTRUCTED")):
        cols, med, mean, mid = trace(fig, name)
        x, y, rx, ry = to_data(fig, cols, med)
        if name == "VOS_VDB_1999_BLACK_SOLID":
            k = x >= 3.0; cols, med, mean, mid, x, y = cols[k], med[k], mean[k], mid[k], x[k], y[k]
        rows_out[name] = (x, y)
        g0 = on_grid(x, y)
        pert = np.array([on_grid(*to_data(fig, cols, med, rng, 2.0)[:2]) for _ in range(300)])
        sd_cal = np.nanstd(pert, 0)
        alt = np.array([on_grid(*to_data(fig, cols, e)[:2]) for e in (mean, mid)])
        sd_ctr = np.nanmax(np.abs(alt - g0), 0)
        grid_out[name] = g0; grid_out[name + "_unc"] = np.sqrt(sd_cal ** 2 + sd_ctr ** 2)
        meta["curves"][name] = {"figure": fig, "n_columns": int(cols.size), "theta_range_deg": [float(x.min()), float(x.max())],
                                "tick_fit_rms_x_deg": rx, "tick_fit_rms_y_log": ry,
                                "unc_calibration_max_log": float(np.nanmax(sd_cal)), "unc_centre_max_log": float(np.nanmax(sd_ctr))}
    with open(os.path.join(HERE, "ginis2012_fig7_digitized.csv"), "w") as f:
        f.write("# DIGITIZED_EXTERNAL_VALIDATION; Ginis et al. 2012 J Vis 12(3):20; y = Log(PSF) as printed (log10 of PSF in sr^-1, see README)\n")
        f.write("curve,theta_deg,log10_psf\n")
        for name, (x, y) in rows_out.items():
            for a, b in sorted(zip(x, y)):
                f.write(f"{name},{a:.4f},{b:.4f}\n")
    keys = list(grid_out)
    with open(os.path.join(HERE, "ginis2012_fig7_grid.csv"), "w") as f:
        f.write("# DIGITIZED_EXTERNAL_VALIDATION; log10 PSF [sr^-1]; *_unc = 1-sigma digitization uncertainty (log10); NaN = not resolvable\n")
        f.write(",".join(keys) + "\n")
        for i in range(GRID.size):
            f.write(",".join(f"{grid_out[k][i]:.4f}" for k in keys) + "\n")
    os.makedirs(os.path.join(HERE, ".cache"), exist_ok=True)
    json.dump(meta, open(os.path.join(HERE, ".cache", "digitize_meta.json"), "w"), indent=1)
    print(json.dumps(meta, indent=1))
    for i in range(0, GRID.size, 2):
        print(GRID[i], *[f"{k}={grid_out[k][i]:.3f}" for k in keys[1:]])


if __name__ == "__main__":
    main()
