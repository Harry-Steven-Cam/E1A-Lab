import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from scipy import odr

from plot_style import *

# ============================================================
# SETTINGS
# ============================================================

save_plots = False
show_plots = True

base = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/7/display"
save_location = rf"{base}/scaling"

# --- component uncertainties (replace with multimeter / LCR values) ---
R_TOL = 0.01          # fractional uncertainty on R3
C_TOL = 0.05          # fractional uncertainty on C2
FREQ_FRAC_ERR = 0.005  # fractional uncertainty on f_in from freqFinder

# --- independent calibrations: (value, error); leave None to skip the comparison ---
K_D_MEAS = (None, None)   # V/rad,  slope of the Section 6.3 PC1 characteristic
K_O_MEAS = (None, None)   # Hz/V,   slope of the Section 6.5 sweep (same R1, R2, C)

# --- quality cuts on the fits ---
MIN_HALF = 1.5            # minimum half-periods resolved in the fit window
MAX_VFINAL_DISC = 0.15    # V, max |v_final_fit - v_final_direct|
MAX_RESID = 0.1           # V, max rms residual of the averaged trace


# ============================================================
# GENERIC HELPERS
# ============================================================
REQUIRED_COLS = [
    "model", "alpha", "alpha_err", "omega_n", "omega_n_err", "zeta", "zeta_err",
    "K", "f_d", "f_in", "f_ripple", "tau", "r3", "c2", "v_final_fit",
    "v_final_fit_err", "v_final_direct", "rms_resid", "n_half",
    "overshoot", "t_settle", "ripple_pp",
]


def load_summary(pc):
    """
    Read transient_summary.csv saved by the per-file analysis for comparator `pc`.
    Returns None if the file is missing, or if it lacks any column the scaling analysis
    needs (a CSV written by an older version of the per-file script); in the latter case
    the missing names are printed so you know to rerun that script.
    """
    path = f"{base}/PC{pc}/transient_summary.csv"
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"PC{pc} summary is out of date; missing columns: {missing}")
        print("Rerun the per-file analysis (with the Part 1 patch) to regenerate it.")
        return None
    return df


def quality_cuts(df):
    """
    Keep only underdamped fits that are trustworthy:
    - >= MIN_HALF half-periods resolved (otherwise alpha and omega_d are degenerate),
    - fitted and directly-measured settled voltage agree (record long enough to settle),
    - small rms residual (the 2nd-order model describes the data).
    Prints how many files survive.
    """
    d = df[df["model"] == "underdamped"].dropna(subset=["alpha", "alpha_err", "omega_n", "omega_n_err"]).copy()
    ok = (
        (d["n_half"] >= MIN_HALF)
        & (np.abs(d["v_final_fit"] - d["v_final_direct"]) < MAX_VFINAL_DISC)
        & (d["rms_resid"] < MAX_RESID)
    )
    print(f"quality cuts: kept {ok.sum()}/{len(d)} underdamped fits ({len(df)} files in total)")
    return d[ok]


def odr_line(x, y, sx, sy):
    """
    Straight-line fit y = m x + c by orthogonal distance regression with
    uncertainties on BOTH axes (scipy.odr).
    How: ODR minimises the distance from each point to the line, weighted by
    1/sx^2 and 1/sy^2; started from an ordinary polyfit. The covariance is
    cov_beta * res_var (scaled by the reduced chi^2, exactly as sd_beta is), so
    errors stay honest if the quoted sx, sy are wrong.
    Returns (beta = [m, c], 2x2 covariance, reduced chi^2).
    """
    x, y, sx, sy = (np.asarray(a, dtype=float) for a in (x, y, sx, sy))
    sx = np.maximum(sx, 1e-12 * np.max(np.abs(x)))   # ODR cannot take zero errors
    sy = np.maximum(sy, 1e-12 * np.max(np.abs(y)))
    m0, c0 = np.polyfit(x, y, 1)
    model = odr.Model(lambda B, xx: B[0] * xx + B[1])
    res = odr.ODR(odr.RealData(x, y, sx=sx, sy=sy), model, beta0=[m0, c0]).run()
    return res.beta, res.cov_beta * res.res_var, res.res_var


def propagate(grad, cov):
    """First-order error propagation sigma_f = sqrt(g^T C g) for a derived quantity f(params)."""
    grad = np.asarray(grad, dtype=float)
    return float(np.sqrt(grad @ cov @ grad))


def finish(fig, name):
    """Tidy layout, optionally save as SVG, then show or close the figure."""
    fig.tight_layout()
    if save_plots:
        os.makedirs(save_location, exist_ok=True)
        fig.savefig(f"{save_location}/{name}.svg")
    if show_plots:
        plt.show()
    else:
        plt.close(fig)


# ============================================================
# CHECK 2: FILTER TIME CONSTANT   alpha = 1/(2 tau_eff)
# ============================================================
def test_filter_time_constant(d):
    """
    tau_eff = 1/(2 alpha) should equal (R3 + R_out) C2, where R_out is the
    comparator's output impedance in series with R3.
    - Files with C2 fixed and >= 3 values of R3: fit tau_eff vs R3.
        slope = C2 (compared with the nominal value), intercept = C2 R_out
        -> R_out = intercept/slope, error by propagation with the fit covariance.
    - Files with R3 fixed and >= 3 values of C2: fit tau_eff vs C2.
        slope = R3 + R_out -> R_out = slope - R3, intercept = (R3 + R_out) C_stray.
    Returns the error-weighted mean (R_out, error) over all groups, (0, 0) if none.
    """
    r_outs = []
    for xcol, fixcol in (("r3", "c2"), ("c2", "r3")):
        for key, g in d.groupby(fixcol):
            if g[xcol].nunique() < 3:
                continue
            x = g[xcol].to_numpy(float)
            a = g["alpha"].to_numpy(float)
            y = 1 / (2 * a)                                   # tau_eff in s
            sy = g["alpha_err"].to_numpy(float) / (2 * a**2)  # d(1/2a) = da/(2a^2)
            sx = x * (R_TOL if xcol == "r3" else C_TOL)
            (m, c), cov, chi2 = odr_line(x, y, sx, sy)

            if xcol == "r3":
                nom_err = key * C_TOL
                nsig = (m - key) / np.hypot(np.sqrt(cov[0, 0]), nom_err)
                r_out, r_out_err = c / m, propagate([-c / m**2, 1 / m], cov)
                print(f"[tau vs R3, C2 = {key:.3g} F] slope = {m:.4g} +/- {np.sqrt(cov[0,0]):.2g} F "
                      f"(nominal C2: {nsig:+.1f} sigma), R_out = {r_out:.0f} +/- {r_out_err:.0f} ohm, "
                      f"chi2_red = {chi2:.2f}")
            else:
                r_out = m - key
                r_out_err = np.hypot(np.sqrt(cov[0, 0]), key * R_TOL)
                c_stray, c_stray_err = c / m, propagate([-c / m**2, 1 / m], cov)
                print(f"[tau vs C2, R3 = {key:.3g} ohm] slope = {m:.4g} ohm -> R_out = {r_out:.0f} +/- "
                      f"{r_out_err:.0f} ohm, C_stray = {c_stray:.3g} +/- {c_stray_err:.2g} F, chi2_red = {chi2:.2f}")
            r_outs.append((r_out, r_out_err))

            fig, ax = plt.subplots(figsize=(6, 4.5))
            ax.errorbar(x, y, xerr=sx, yerr=sy, fmt="x", color=colours[0], label="Fitted")
            xx = np.linspace(0, 1.05 * x.max(), 100)
            ax.plot(xx, m * xx + c, color=colours[1], ls="--", label="ODR fit")
            ax.set_xlabel(f"{xcol.upper()} (" + (r"$\Omega$)" if xcol == "r3" else "F)"))
            ax.set_ylabel(r"$\tau_{eff}=1/2\alpha$ (s)")
            ax.set_title(f"Filter time constant ({fixcol.upper()} = {key:.3g})")
            ax.legend()
            ax.grid(True)
            finish(fig, f"tau_vs_{xcol}_{fixcol}={key:.3g}")

    if not r_outs:
        print("[tau test] need >= 3 values of R3 (or C2) at fixed C2 (or R3); using R_out = 0")
        return 0.0, 0.0
    vals = np.array([r for r, _ in r_outs])
    errs = np.maximum(np.array([e for _, e in r_outs]), 1e-9)
    w = 1 / errs**2
    r_out, r_out_err = np.sum(w * vals) / np.sum(w), 1 / np.sqrt(np.sum(w))
    print(f"[tau test] weighted mean R_out = {r_out:.0f} +/- {r_out_err:.0f} ohm")
    return r_out, r_out_err


# ============================================================
# CHECK 3: LOOP GAIN   omega_n^2 = K / tau_eff
# ============================================================
def test_loop_gain(d, r_out):
    """
    From tau s^2 + s + K = 0:  omega_n^2 = K/tau_eff, so omega_n^2 vs 1/tau_eff
    is a straight line through the origin with slope K = K_D K_O.
    Two fits: free intercept (ODR; a significant intercept means an extra pole
    or delay) and through-origin weighted least squares (gives K).
    If fewer than 3 distinct tau, falls back to the mean of the per-file K.
    Returns (K, K_err).
    """
    if len(d) == 0:
        return np.nan, np.nan
    tau_eff = (d["r3"] + r_out) * d["c2"]
    x = (1 / tau_eff).to_numpy(float)
    sx = x * np.hypot(R_TOL, C_TOL)
    wn = d["omega_n"].to_numpy(float)
    y = wn**2
    sy = 2 * wn * d["omega_n_err"].to_numpy(float)    # d(w^2) = 2 w dw

    if len(np.unique(np.round(x / x.max(), 3))) < 3:
        K, K_err = d["K"].mean(), d["K"].std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.nan
        print(f"[gain test] < 3 distinct tau: K = {K:.4g} +/- {K_err:.2g} s^-1 (mean of per-file values)")
        return K, K_err

    (m, c), cov, chi2 = odr_line(x, y, sx, sy)
    print(f"[gain test] free intercept: slope = {m:.4g} +/- {np.sqrt(cov[0,0]):.2g} s^-1, "
          f"intercept = {c:.3g} +/- {np.sqrt(cov[1,1]):.2g} s^-2 ({c/np.sqrt(cov[1,1]):+.1f} sigma), "
          f"chi2_red = {chi2:.2f}")

    w = 1 / np.maximum(sy, 1e-12 * y.max()) ** 2
    K0 = np.sum(w * x * y) / np.sum(w * x * x)
    chi2_0 = np.sum(w * (y - K0 * x) ** 2) / (len(x) - 1)
    K0_err = np.sqrt(max(chi2_0, 1.0) / np.sum(w * x * x))   # inflate if chi2_red > 1
    print(f"[gain test] through origin: K = {K0:.4g} +/- {K0_err:.2g} s^-1, chi2_red = {chi2_0:.2f}")

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.errorbar(x, y, xerr=sx, yerr=sy, fmt="x", color=colours[0], label="Fitted")
    xx = np.linspace(0, 1.05 * x.max(), 100)
    ax.plot(xx, m * xx + c, color=colours[1], ls="--", label="Free intercept")
    ax.plot(xx, K0 * xx, color=colours[2], label=rf"Through origin, $K$ = {format_sci_err(K0, K0_err)} s$^{{-1}}$")
    ax.set_xlabel(r"$1/\tau_{eff}$ (s$^{-1}$)")
    ax.set_ylabel(r"$\omega_n^2$ (s$^{-2}$)")
    ax.legend()
    ax.grid(True)
    finish(fig, "omega_n2_vs_inv_tau")
    return K0, K0_err


# ============================================================
# CHECK 4: COMPARE K WITH THE OPEN-LOOP CALIBRATIONS
# ============================================================
def compare_K(K_fit, K_err):
    """
    Independent prediction K = K_D * (2 pi K_O), with K_D in V/rad (Section 6.3)
    and K_O in Hz/V (Section 6.5). Prints the discrepancy in standard deviations.
    """
    if any(v is None for v in (*K_D_MEAS, *K_O_MEAS)):
        print("[K comparison] set K_D_MEAS and K_O_MEAS to compare with the open-loop calibrations")
        return
    (K_D, sK_D), (K_O, sK_O) = K_D_MEAS, K_O_MEAS
    K_th = K_D * 2 * np.pi * K_O
    K_th_err = K_th * np.hypot(sK_D / K_D, sK_O / K_O)       # product: add relative errors in quadrature
    nsig = (K_fit - K_th) / np.hypot(K_err, K_th_err)
    print(f"[K comparison] K_transient = {K_fit:.4g} +/- {K_err:.2g}, K_D K_O = {K_th:.4g} +/- {K_th_err:.2g} "
          f"s^-1 -> {nsig:+.1f} sigma; ratio = {K_fit/K_th:.3f}")


# ============================================================
# CHECK 5: DELAY MODEL   tau s^2 + s + K exp(-s T_d) = 0
# ============================================================
def loop_poles(tau, K, T_d):
    """
    Dominant complex pole pair of  s(1 + s tau) + K exp(-s T_d) = 0.
    Pade (1,1) for the delay: exp(-sT) ~ (1 - sT/2)/(1 + sT/2). Multiplying through by
    (1 + sT/2):
        (tau T/2) s^3 + (tau + T/2) s^2 + (1 - K T/2) s + K = 0.
    T_d = 0 drops the cubic term (np.roots strips the zero leading coefficient) and
    recovers tau s^2 + s + K = 0. Returns (alpha, omega_d) = (-Re s, Im s) of the
    complex root with the largest real part, or (nan, nan) if the roots are all real.
    """
    roots = np.roots([tau * T_d / 2, tau + T_d / 2, 1 - K * T_d / 2, K])
    cplx = roots[roots.imag > 1e-9 * np.abs(roots)]
    if len(cplx) == 0:
        return np.nan, np.nan
    s = cplx[np.argmax(cplx.real)]
    return -s.real, s.imag


def rms_frac(meas, pred):
    """RMS fractional deviation (meas - pred)/pred over finite pairs; robust to underestimated fit errors."""
    ok = np.isfinite(meas) & np.isfinite(pred)
    return np.sqrt(np.mean(((meas[ok] - pred[ok]) / pred[ok]) ** 2)) if ok.any() else np.nan


def test_delay_model(d, K, r_out):
    """
    Compare measured alpha, f_d, zeta with two predictions at the fitted K:
    (a) no delay (tau s^2 + s + K = 0), (b) delay T_d = T_r/2 = 1/(4 f_in) for PC1, i.e. half the
    ripple (update) period. Prints RMS fractional deviations and plots
    measured vs predicted alpha, f_d and zeta vs tau_eff.
    """
    if len(d) == 0 or not np.isfinite(K):
        return
    tau_eff = ((d["r3"] + r_out) * d["c2"]).to_numpy(float)
    T_d = 0.5 / d["f_ripple"].to_numpy(float)
    nod = np.array([loop_poles(t, K, 0.0) for t in tau_eff])
    wd = np.array([loop_poles(t, K, td) for t, td in zip(tau_eff, T_d)])
    a_m, f_m = d["alpha"].to_numpy(float), d["f_d"].to_numpy(float)
    z_m, z_err = d["zeta"].to_numpy(float), d["zeta_err"].to_numpy(float)

    print(f"[delay model] RMS fractional deviation  alpha: no delay {rms_frac(a_m, nod[:,0]):.3f}, "
          f"delay {rms_frac(a_m, wd[:,0]):.3f}")
    print(f"[delay model] RMS fractional deviation  f_d:   no delay {rms_frac(f_m, nod[:,1]/(2*np.pi)):.3f}, "
          f"delay {rms_frac(f_m, wd[:,1]/(2*np.pi)):.3f}")

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, meas, p_nod, p_wd, lab in (
        (a1, a_m, nod[:, 0], wd[:, 0], r"$\alpha$ (s$^{-1}$)"),
        (a2, f_m, nod[:, 1] / (2 * np.pi), wd[:, 1] / (2 * np.pi), r"$f_d$ (Hz)"),
    ):
        ax.plot(p_nod, meas, color=colours[0], label="No delay", **plot_styles)
        ax.plot(p_wd, meas, color=colours[1], label=r"Delay $T_d=T_r/2$", **plot_styles)
        lim = [0, 1.1 * np.nanmax(np.r_[meas, p_nod, p_wd])]
        ax.plot(lim, lim, color="grey", ls="--")
        ax.set_xlabel(f"Predicted {lab}")
        ax.set_ylabel(f"Measured {lab}")
        ax.legend()
        ax.grid(True)

    tg = np.geomspace(tau_eff.min() / 2, tau_eff.max() * 2, 200)   # tau grid for theory curves
    Td_med = np.median(T_d)
    z_nod = 1 / (2 * np.sqrt(K * tg))
    pw = np.array([loop_poles(t, K, Td_med) for t in tg])
    z_wd = pw[:, 0] / np.hypot(pw[:, 0], pw[:, 1])              # zeta = alpha/omega_n
    a3.errorbar(tau_eff, z_m, yerr=z_err, fmt="x", color=colours[0], label="Measured")
    a3.plot(tg, z_nod, color=colours[1], label="No delay")
    a3.plot(tg, z_wd, color=colours[2], ls="--", label=rf"Delay ($T_d$ = {Td_med*1e6:.1f} µs)")
    a3.set_xscale("log")
    a3.set_yscale("log")
    a3.set_xlabel(r"$\tau_{eff}$ (s)")
    a3.set_ylabel(r"$\zeta$")
    a3.legend()
    a3.grid(True)
    finish(fig, "delay_model")


# ============================================================
# CHECK 6: LOCK VOLTAGE vs INPUT FREQUENCY
# ============================================================
def test_lock_voltage(d):
    """
    In lock the VCO frequency equals f_in, so the settled control voltage must lie on the
    open-loop VCO characteristic f = K_O v + f_0 (K_O in Hz/V). Fits f_in vs v_inf (ODR) and
    compares the slope with K_O_MEAS if given. Needs >= 3 distinct f_in.
    """
    if d["f_in"].nunique() < 3:
        print("[lock voltage] need >= 3 distinct f_in; skipped")
        return
    x = d["v_final_fit"].to_numpy(float)
    sx = np.maximum(d["v_final_fit_err"].to_numpy(float), 0.01)   # floor at ~ADC resolution
    y = d["f_in"].to_numpy(float)
    sy = FREQ_FRAC_ERR * y
    (m, c), cov, chi2 = odr_line(x, y, sx, sy)
    msg = f"[lock voltage] K_O = {m:.4g} +/- {np.sqrt(cov[0,0]):.2g} Hz/V, f_0 = {c:.4g} Hz, chi2_red = {chi2:.2f}"
    if K_O_MEAS[0] is not None:
        msg += f"; open-loop {K_O_MEAS[0]:.4g}: {(m - K_O_MEAS[0]) / np.hypot(np.sqrt(cov[0,0]), K_O_MEAS[1]):+.1f} sigma"
    print(msg)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.errorbar(x, y, xerr=sx, yerr=sy, fmt="x", color=colours[0], label="Locked data")
    xx = np.linspace(x.min(), x.max(), 100)
    ax.plot(xx, m * xx + c, color=colours[1], ls="--", label="ODR fit")
    if K_O_MEAS[0] is not None:
        ax.plot(xx, K_O_MEAS[0] * xx + (c + (m - K_O_MEAS[0]) * x.mean()), color=colours[2], ls=":",
                label="Open-loop slope (offset matched)")
    ax.set_xlabel(r"Settled control voltage $v_\infty$ (V)")
    ax.set_ylabel(r"$f_{in}$ (Hz)")
    ax.legend()
    ax.grid(True)
    finish(fig, "lock_voltage")


# ============================================================
# CHECK 7: PC1 vs PC2
# ============================================================
def compare_pc(df1, df2):
    """
    Empirical (model-free) comparison of the comparators at the same filter settings:
    overshoot fraction, 5 % settling time and in-lock ripple vs tau. Prints the
    per-tau medians and plots all files.
    """
    metrics = [("overshoot", "Overshoot fraction"), ("t_settle", "5 % settling time (s)"),
               ("ripple_pp", "Ripple p-p in lock (V)")]
    for pc, df in ((1, df1), (2, df2)):
        print(f"\nPC{pc} medians per tau:")
        print(df.groupby("tau")[[m for m, _ in metrics]].median().to_string())
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (col, lab) in zip(axes, metrics):
        for df, pc, c in ((df1, 1, colours[0]), (df2, 2, colours[1])):
            ax.plot(df["tau"] * 1e6, df[col], color=c, label=f"PC{pc}", **plot_styles)
        ax.set_xscale("log")
        ax.set_xlabel(r"$\tau = R_3C_2$ (µs)")
        ax.set_ylabel(lab)
        ax.legend()
        ax.grid(True)
    finish(fig, "pc1_vs_pc2")


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    matplot_styles()
    df1, df2 = load_summary(1), load_summary(2)

    if df1 is not None:
        d1 = quality_cuts(df1)
        r_out, r_out_err = test_filter_time_constant(d1)
        K_fit, K_err = test_loop_gain(d1, r_out)
        compare_K(K_fit, K_err)
        test_delay_model(d1, K_fit, r_out)
        test_lock_voltage(d1)
    else:
        print(f"No PC1 summary found in {base}/PC1")

    if df1 is not None and df2 is not None:
        compare_pc(df1, df2)