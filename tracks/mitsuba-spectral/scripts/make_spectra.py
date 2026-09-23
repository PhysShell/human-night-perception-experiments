"""Write the test emission spectra (relative spectral radiance, 360-830 nm, 1 nm) used by both
the mitsuba-spectral and iset tracks. Sources:
  HPS      = CIE illuminant HP1 (standard high-pressure sodium, CIE 15:2018) from colour-science
  LED_warm = CIE illuminant LED-B1 (phosphor-converted LED, ~2700 K, CIE 15:2018) from colour-science
  E        = equal-energy (flat)
  LPS      = CONSTRUCTED low-pressure-sodium-like D doublet: Gaussians at 588.995 / 589.592 nm
             (NIST Na I D2/D1), 2:1 ratio, FWHM 1.0 nm each (instrument-limited, not a lamp measurement)
  BLUE     = CONSTRUCTED blue LED-like Gaussian, 460 nm peak, FWHM 20 nm
Each column is normalised to unit photopic luminance (sum(S*V)*683*dl = 1), i.e. 1 cd/m^2 when
read as W m^-2 sr^-1 nm^-1. Usage: python make_spectra.py <out.csv>"""
import sys
import numpy as np
import colour

wl = np.arange(360, 831, 1.0)
shape = colour.SpectralShape(360, 830, 1)
def get(sd):
    return sd.copy().align(shape, extrapolator_kwargs={"method": "Constant", "left": 0, "right": 0}).values
def gauss(mu, fwhm):
    s = fwhm / 2.3548
    return np.exp(-0.5 * ((wl - mu) / s) ** 2)
spec = {
    "LPS": 2 * gauss(588.995, 1.0) + gauss(589.592, 1.0),
    "HPS": get(colour.SDS_ILLUMINANTS["HP1"]),
    "LED_warm": get(colour.SDS_ILLUMINANTS["LED-B1"]),
    "E": np.ones_like(wl),
    "BLUE": gauss(460.0, 20.0),
}
V = get(colour.colorimetry.SDS_LEFS_PHOTOPIC["CIE 1924 Photopic Standard Observer"])
for k in spec:
    spec[k] = spec[k] / (683.0 * np.sum(spec[k] * V))
out = sys.argv[1]
hdr = "wavelength_nm," + ",".join(spec)
np.savetxt(out, np.column_stack([wl] + [spec[k] for k in spec]), delimiter=",", header=hdr, comments="", fmt="%.6e")
print("wrote", out, list(spec))
