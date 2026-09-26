"""Wanat & Mantiuk 2014 §4.1.1 global contrast retargeting (Eqs. 5-11), our implementation (no public code exists).
CSF: HDR-VDP-2.2.2 full CSF ncsf(rho,L)*MTF(rho)*sA(L) (tables from the official 2.2.2 hdrvdp_parse_options.m),
S = 8.6 (-> Mt = 0.409 % at 2 cpd, 100 cd/m^2; paper: 0.4 %). See d1/axis_a/PREREG.md."""
import numpy as np
from scipy.optimize import minimize

_P = np.array([[0.0160737, 0.991265, 3.74038, 0.50722, 4.46044], [0.383873, 0.800889, 3.54104, 0.682505, 4.94958],
               [0.929301, 0.476505, 4.37453, 0.750315, 5.28678], [1.29776, 0.405782, 4.40602, 0.935314, 5.61425],
               [1.49222, 0.334278, 3.79542, 1.07327, 6.4635], [1.46213, 0.394533, 2.7755, 1.16577, 7.45665]])
_LL = np.log10([0.002, 0.02, 0.2, 2, 20, 150])
_mp = [0.061466549455263, 0.99727370023777070]
_MA = [_mp[1] * 0.426, _mp[1] * 0.574, (1 - _mp[1]) * _mp[0], (1 - _mp[1]) * (1 - _mp[0])]; _MB = [0.028, 0.37, 37, 360]
_SA = [30.162, 4.0627, 1.6596, 0.2712]
S_ABS, RHO, G_REP, TAU, MT_CAP = 8.6, 2.0, 0.4, 1e-4, 0.999


def csf(rho, L):
    L = np.asarray(L, float); ll = np.clip(np.log10(L), _LL[0], _LL[-1])
    p = [np.interp(ll, _LL, _P[:, k + 1]) for k in range(4)]
    n = p[3] / ((1 + (p[0] * rho) ** p[1]) * 1 / (1 - np.exp(-(rho / 7) ** 2)) ** p[2]) ** 0.5
    mtf = sum(a * np.exp(-b * rho) for a, b in zip(_MA, _MB))
    sA = _SA[0] * ((_SA[1] / L) ** _SA[2] + 1) ** (-_SA[3])
    return n * mtf * sA


def Gt(logL):
    Mt = np.minimum(1.0 / (S_ABS * csf(RHO, 10.0 ** np.asarray(logL))), MT_CAP)
    return 0.5 * np.log10((1 + Mt) / (1 - Mt))


def tone_curve(lmin, lmax, dmin, dmax, n=30):
    """returns node positions l (log10 source) and T(l) (log10 display)"""
    l = np.linspace(lmin, lmax, n); d = l[1] - l[0]; lm = 0.5 * (l[1:] + l[:-1]); gl = Gt(lm)
    def obj(T):
        s = np.diff(T) / d; Tm = 0.5 * (T[1:] + T[:-1])
        return float(np.sum(((G_REP - gl) - (s * G_REP - Gt(Tm))) ** 2 + TAU * (lm - Tm) ** 2) * d)
    cons = [{"type": "ineq", "fun": lambda T: np.diff(T)}, {"type": "ineq", "fun": lambda T: T[0] - dmin},
            {"type": "ineq", "fun": lambda T: dmax - T[-1]}]
    x0 = np.clip(l, dmin, dmax) if (lmin >= dmin and lmax <= dmax) else dmin + (l - lmin) / (lmax - lmin) * (dmax - dmin)
    r = minimize(obj, x0, method="SLSQP", constraints=cons, options={"maxiter": 2000, "ftol": 1e-12})
    return l, r.x, r


def apply(T_l, T_v, Y):
    return 10.0 ** np.interp(np.log10(np.maximum(Y, 1e-30)), T_l, T_v)
