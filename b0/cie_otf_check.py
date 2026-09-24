#!/usr/bin/env python3
"""B0 v3 normalisation check: is HDR-VDP 3.0.7's hdrvdp_otf_cie99 the 2-D OTF of the CIE 135/1 glare spread
function? A radially symmetric 2-D PSF has the Hankel transform as its OTF:
    OTF(rho) = int_0^inf PSF(theta) J0(2 pi rho theta) 2 pi theta dtheta     (theta in deg, PSF in deg^-2)
Computed numerically from the analytic GSF (b0/retinal_profiles.py cie_gsf, unit integral in sr) and compared
with HDR-VDP's closed form (its comment: "found by applying a Fourier transform using Matlab's symbolic
toolbox"; its terms 2 c^2 |w| K1(c |w|) are the 1-D Fourier transform of (1 + (x/c)^2)^-1.5, whose 2-D
transform is 2 pi c^2 exp(-2 pi c rho) instead). Age 24, p 0.5.
  python3 b0/cie_otf_check.py -> b0/results/cie_otf_check.json
"""
import json, math
import numpy as np
from scipy.special import j0, k0, k1
import importlib.util

spec = importlib.util.spec_from_file_location("rp", "b0/retinal_profiles.py")
src = open("b0/retinal_profiles.py").read()
ns = {}; exec(src[src.index("def cie_gsf"):src.index("tot = ")], {"np": np}, ns); cie_gsf = ns["cie_gsf"]

SR_PER_DEG2 = math.radians(1) ** 2
th = np.concatenate([np.linspace(0, 0.05, 200001)[:-1], np.geomspace(0.05, 60, 400001)])   # deg (small-angle)
psf = cie_gsf(th) * SR_PER_DEG2                                                                  # deg^-2


def otf_hankel(rho):
    return np.trapezoid(psf * j0(2 * np.pi * rho * th) * 2 * np.pi * th, th)


def otf_hdrvdp(rho, age=24.0, p=0.5):
    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 = 9.2e6, .08, .0046, 1.5e5, .045, 1.6, 400, .1, 3e-8, 1300, .8, 2.5e-3, .0417, .055
    def m(w):
        w = abs(w); a = age ** 4 / 70 ** 4
        return (p * (a * c6 + 1) * (2 * c8 * c11 * k0(c8 * w) + 2 * c8 ** 2 * c10 * w * k1(c8 * w))
                - (a * c2 - 1) * (2 * c1 * c3 ** 2 * w * k1(c3 * w) + 2 * c4 * c5 ** 2 * w * k1(c5 * w))
                + c7 * c8 * np.pi * np.exp(-c8 * w) * (c6 * age ** 4 + 70 ** 4) / 70 ** 4) / (p * (c13 + a * c14) + 1)
    return m(2 * np.pi * rho) / m(1e-4)   # as hdrvdp_otf_cie99: omega = 2 pi rho, normalised at omega = 1e-4 (dirac terms dropped off DC)


RHO = [0.1, 0.3, 1, 3, 10, 30]
res = {"integral_of_GSF_to_60deg_in_deg2": float(np.trapezoid(psf * 2 * np.pi * th, th)),
       "rho_cpd": RHO,
       "OTF_2D_hankel_of_CIE135_GSF": [float(otf_hankel(r)) for r in RHO],
       "OTF_hdrvdp_otf_cie99": [float(otf_hdrvdp(r)) for r in RHO]}
json.dump(res, open("b0/results/cie_otf_check.json", "w"), indent=1)
print(json.dumps(res, indent=1))
