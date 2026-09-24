"""O2 CIE 135/1 complete visual spread function (eq. 8 form, + age factor), sr^-1, theta in deg. Shared by b1/oracles.py and b1/unified_pupil.py."""
import numpy as np
AGE, P_CIE = 24.0, 0.5


def cie_raw(t_deg, age=AGE, p=P_CIE):
    t, a4 = np.asarray(t_deg, float), (age / 70.0) ** 4
    return ((1 - 0.08 * a4) * (9.2e6 / (1 + (t / 0.0046) ** 2) ** 1.5 + 1.5e5 / (1 + (t / 0.045) ** 2) ** 1.5)
            + (1 + 1.6 * a4) * ((400 / (1 + (t / 0.1) ** 2) + 3e-8 * t ** 2)
                                + p * (1300 / (1 + (t / 0.1) ** 2) ** 1.5 + 0.8 / (1 + (t / 0.1) ** 2) ** 0.5))
            + 2.5e-3 * p)
