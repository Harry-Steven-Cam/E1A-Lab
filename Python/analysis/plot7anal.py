import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import re
from glob import glob
import time

from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from scipy.integrate import cumulative_trapezoid


from plot_style import *
from line_finder import freqFinder  # <-- change 'fitting' to whatever your second file is called

# ============================================================
# SETTINGS
# ============================================================

PC = 2
save_plots = True
show_plots = False
folder = rf"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/7/PC{PC}"

save_location = (
    rf"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/7/display/PC{PC}"
)

# ---- transient-analysis settings ----
V_DD = 5.0  # logic supply voltage (V)
K_O_HZ_PER_V = None  # VCO gain from your sweeps (Hz/V); set it to compare with theory
FIT_T_MIN = 0.0  # s after step; raise to skip an initial non-linear capture phase
FIT_T_MAX = None  # s after step; None = use all data


# ============================================================
# FILENAME PARSING
# ============================================================
def parse_transient_filename(name):
    """
    Pull the circuit parameters out of a filename such as
    Turn_on_PC1_capturetime=0.01s_R1=100K_R2=100K_C=100pF_f10.0(kHz)_R3=1.5K_C2=100.0nF_fc=1.06e+03(Hz)
    Works by lower-casing the name and using regexes on 'key=value' tokens
    (tokens are separated by '_'). The regex (?:^|_)c= only matches a token
    that is exactly 'c=', so 'c2=' is not confused with it.
    Returns a dict of floats (None if a key is missing); resistances in ohm,
    capacitances in F, frequencies in Hz. data_to_val (plot_style) converts
    strings like '1.5k' or '100.0nf' to SI values.
    """
    n = name.lower()

    def get(key):
        m = re.search(rf"(?:^|_){key}=([^_]+)", n)
        return m.group(1) if m else None

    out = {}
    m = re.search(r"pc(\d)", n)
    out["pc"] = int(m.group(1)) if m else None
    for key in ("r1", "r2", "c", "r3", "c2"):
        val = get(key)
        out[key] = data_to_val(val) if val else None
    # input frequency is written as f10.0(kHz)
    m = re.search(r"_f([0-9.]+)\(khz\)", n)
    out["f_in"] = float(m.group(1)) * 1e3 if m else None
    # filter cutoff written as fc=1.06e+03(Hz)
    m = re.search(r"fc=([0-9.eE+-]+?)\(hz\)", n)
    out["fc"] = float(m.group(1)) if m else None
    return out


# ============================================================
# PRE-PROCESSING
# ============================================================
def find_step_time(t, awg, n_base=200, frac=0.5):
    """
    Find the time at which the AWG input 'turns on'.
    The baseline is the median of the first n_base samples (pre-trigger).
    The step time is the first sample whose deviation from the baseline
    exceeds frac * (maximum deviation). Returns 0.0 if the AWG never moves.
    """
    base = np.median(awg[:n_base])
    dev = np.abs(awg - base)
    if dev.max() < 1e-3:
        return 0.0
    return t[np.argmax(dev > frac * dev.max())]


def boxcar_average(t, v, window):
    """
    Centred moving average of EXACT duration `window` (need not be a whole
    number of samples):
        <v>(t) = (1/window) * integral_{t-window/2}^{t+window/2} v dt'
    How: build the running integral I(t) with the trapezium rule, then
    evaluate I at t +/- window/2 by linear interpolation (np.interp) and
    difference. If window = ripple period, a periodic ripple integrates to
    zero exactly, and the centred window adds no time delay.
    Returns only points where the whole window lies inside the data.
    """
    I = cumulative_trapezoid(v, t, initial=0.0)
    t_c = t[(t - window / 2 >= t[0]) & (t + window / 2 <= t[-1])]
    avg = (np.interp(t_c + window / 2, t, I) - np.interp(t_c - window / 2, t, I)) / window
    return t_c, avg


def final_voltage_direct(t, v, f_r, frac=0.1):
    """
    Model-independent estimate of the settled voltage: the mean of the last
    ~frac of the record, truncated to a whole number of ripple periods so the
    ripple averages out. Used as a cross-check on the fitted v_inf.
    """
    n = max(1, int(np.floor(frac * t[-1] * f_r)))
    mask = t >= t[-1] - n / f_r
    return np.mean(v[mask])


# ============================================================
# FIT MODELS
# ============================================================
def underdamped(t, v_inf, A, alpha, omega, phi):
    """Damped oscillation v_inf + A exp(-alpha t) cos(omega t + phi) (2nd-order, zeta < 1)."""
    return v_inf + A * np.exp(-alpha * t) * np.cos(omega * t + phi)


def overdamped(t, v_inf, A1, r1, A2, r2):
    """Two decaying exponentials; fallback when no oscillation is resolved (zeta >= 1)."""
    return v_inf + A1 * np.exp(-r1 * t) + A2 * np.exp(-r2 * t)


def fit_underdamped(t, v, tau=None):
    """
    Least-squares fit of `underdamped` with scipy curve_fit.
    Initial guesses: v_inf = mean of the last 10 % of points, A = half the
    peak-to-peak, omega from the mean spacing of peaks (find_peaks),
    alpha = 1/(2 tau) from theory. The phase is poorly guessed, so the fit is
    started from four phases (0, pi/2, pi, 3pi/2) and the lowest-SSE result is
    kept (avoids local minima). Bounds force alpha, omega >= 0.
    Returns (popt, pcov, sse) or None if every start failed.
    """
    v_inf0 = np.mean(v[-max(5, len(v) // 10) :])
    peaks, _ = find_peaks(v, prominence=0.1 * np.ptp(v))
    omega0 = 2 * np.pi / np.mean(np.diff(t[peaks])) if len(peaks) >= 2 else 4 * np.pi / t[-1]
    alpha0 = 1 / (2 * tau) if tau else 3 / t[-1]
    A0 = np.ptp(v) / 2
    lower = [-np.inf, -np.inf, 0, 0, -2 * np.pi]
    upper = [np.inf, np.inf, np.inf, np.inf, 2 * np.pi]
    best = None
    for phi0 in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        try:
            popt, pcov = curve_fit(
                underdamped,
                t,
                v,
                p0=[v_inf0, A0, alpha0, omega0, phi0],
                bounds=(lower, upper),
                x_scale="jac",
                max_nfev=2000,
            )
        except (RuntimeError, ValueError):
            continue
        sse = np.sum((v - underdamped(t, *popt)) ** 2)
        if best is None or sse < best[2]:
            best = (popt, pcov, sse)
    return best


def fit_overdamped(t, v, tau=None):
    """
    Two-exponential fit, v_inf + A1 exp(-r1 t) + A2 exp(-r2 t), made robust by:
    - bounding both rates between 1/(20 T_window) (slower is indistinguishable
      from a constant over the record) and 1/(2 dt) (faster than the sampling
      is unresolvable), so exp() cannot overflow and r1 = r2 degeneracy is limited;
    - bounding amplitudes to +/- 10 x peak-to-peak, which stops the A1 = -A2 -> inf
      cancellation;
    - capping max_nfev so a bad start fails in seconds rather than hanging.
    Returns (popt, pcov, sse) or None on failure.
    """
    v_inf0 = np.mean(v[-max(5, len(v) // 10) :])
    A0 = v[0] - v_inf0
    T_win = t[-1] - t[0]
    dt = np.median(np.diff(t))
    r_lo, r_hi = 1 / (20 * T_win), 1 / (2 * dt)
    r1_0 = np.clip(1 / tau if tau else 3 / T_win, 2 * r_lo, r_hi / 10)
    A_max = 10 * np.ptp(v)
    try:
        popt, pcov = curve_fit(
            overdamped,
            t,
            v,
            p0=[v_inf0, A0 / 2, r1_0, A0 / 2, 5 * r1_0],
            bounds=([-np.inf, -A_max, r_lo, -A_max, r_lo], [np.inf, A_max, r_hi, A_max, r_hi]),
            x_scale="jac",
            max_nfev=500,
        )
    except (RuntimeError, ValueError):
        return None
    return popt, pcov, np.sum((v - overdamped(t, *popt)) ** 2)


def propagate(grad, cov):
    """
    First-order error propagation sigma_f = sqrt(g^T C g), where g is the
    gradient of the derived quantity wrt the fitted parameters and C their
    covariance sub-matrix (keeps the alpha-omega correlation).
    """
    grad = np.asarray(grad, dtype=float)
    return float(np.sqrt(grad @ cov @ grad))


# ============================================================
# MAIN ANALYSIS OF ONE FILE
# ============================================================
def analyse_file(path):
    """
    Full pipeline for one 'Turn_on' csv:
    1. read data, parse the filename, locate the step in awg_out;
    2. measure the input frequency (freqFinder) -> ripple frequency
       (2 f_in for PC1 XOR output, f_in for PC2 pulses);
    3. remove ripple with an exact-period boxcar average;
    4. fit a damped oscillation (or two exponentials if overdamped);
    5. derive alpha, f_d, omega_n, zeta, K (and K_O,eff) with errors,
       compare with the second-order theory for PC1;
    6. plot raw, averaged, fit, residuals. Returns a dict of results.
    """
    name = os.path.basename(path)[:-4]
    p = parse_transient_filename(name)
    pc = p["pc"] if p["pc"] else PC
    tau = p["r3"] * p["c2"] if (p["r3"] and p["c2"]) else None

    df = pd.read_csv(path)
    t_all = df["time"].to_numpy()
    awg = df["awg_out"].to_numpy()
    pll = df["pll_out"].to_numpy()

    # --- step location; t is now 'time after step' ---
    t0 = find_step_time(t_all, awg)
    post = t_all >= t0
    t = t_all[post] - t0
    v = pll[post]
    v_pre = np.mean(pll[t_all < t0]) if np.any(t_all < t0) else np.nan  # voltage before turn-on

    # --- input and ripple frequency ---
    f_meas = freqFinder(awg[post], t)
    f_in = f_meas if f_meas > 0 else p["f_in"]
    if p["f_in"] and abs(f_in - p["f_in"]) / p["f_in"] > 0.02:
        print(f"[warn] {name}: measured f_in = {f_in:.1f} Hz vs filename {p['f_in']:.1f} Hz")
    f_r = 2 * f_in if pc == 1 else f_in
    T_r = 1 / f_r

    # --- ripple removal and fit window ---
    t_a, v_a = boxcar_average(t, v, T_r)
    mask = t_a >= FIT_T_MIN
    if FIT_T_MAX is not None:
        mask &= t_a <= FIT_T_MAX
    t_f, v_f = t_a[mask], v_a[mask]
    step = max(1, len(t_f) // 2000)
    t_f, v_f = t_f[::step], v_f[::step]

    # --- fit: underdamped first, overdamped if no half-period is resolved ---
    res_u = fit_underdamped(t_f, v_f, tau)
    if res_u is None:
        print("    underdamped fit did not converge", flush=True)
        use_under = False
    else:
        n_half = res_u[0][3] * t_f[-1] / np.pi  # number of half-periods in the window
        print(f"    underdamped: alpha = {res_u[0][2]:.3g}, omega_d = {res_u[0][3]:.3g}, "
                f"{n_half:.2f} half-periods in window", flush=True)
        use_under = n_half > 1
    if use_under:
        popt, pcov, _ = res_u
        func, model = underdamped, "underdamped"
    else:
        res_o = fit_overdamped(t_f, v_f, tau)
        if res_o is None:
            raise RuntimeError(f"both fits failed for {name}")
        popt, pcov, _ = res_o
        func, model = overdamped, "overdamped"
    perr = np.sqrt(np.diag(pcov))
    resid = v_f - func(t_f, *popt)

    out = dict(
        file=name,
        PC=pc,
        tau=tau,
        f_in=f_in,
        f_ripple=f_r,
        v_pre=v_pre,
        v_final_fit=popt[0],
        v_final_fit_err=perr[0],
        v_final_direct=final_voltage_direct(t, v, f_r),
        model=model,
        alpha=np.nan,
        alpha_err=np.nan,
        f_d=np.nan,
        omega_n=np.nan,
        omega_n_err=np.nan,
        zeta=np.nan,
        zeta_err=np.nan,
        K=np.nan,
        K_err=np.nan,
        K_O_eff=np.nan,
        alpha_theory=np.nan,
        zeta_theory=np.nan,
        f_d_theory=np.nan,
        rms_resid=np.sqrt(np.mean(resid**2)),
    )

    if use_under:
        a, w = popt[2], popt[3]
        wn = np.hypot(a, w)
        cov_aw = pcov[2:4, 2:4]  # covariance of (alpha, omega)
        out.update(
            alpha=a,
            alpha_err=perr[2],
            f_d=w / (2 * np.pi),
            omega_n=wn,
            omega_n_err=propagate([a / wn, w / wn], cov_aw),
            zeta=a / wn,
            zeta_err=propagate([w**2 / wn**3, -a * w / wn**3], cov_aw),
        )
        if tau:
            # K = tau * omega_n^2 = K_D K_O from tau s^2 + s + K = 0
            out["K"] = tau * wn**2
            out["K_err"] = propagate([2 * tau * a, 2 * tau * w], cov_aw)
            if pc == 1:
                K_D = V_DD / np.pi  # XOR: mean output goes 0 -> V_dd over 0 -> pi
                out["K_O_eff"] = out["K"] / K_D  # (rad/s)/V, compare with 2 pi K_O from sweeps

    # --- theory (PC1 + simple RC only; PC2's tri-state output adds an integrator) ---
    if pc == 1 and tau:
        out["alpha_theory"] = 1 / (2 * tau)
        if K_O_HZ_PER_V is not None:
            K_th = (V_DD / np.pi) * 2 * np.pi * K_O_HZ_PER_V
            out["zeta_theory"] = 1 / (2 * np.sqrt(K_th * tau))
            wd2 = K_th / tau - 1 / (4 * tau**2)
            out["f_d_theory"] = np.sqrt(wd2) / (2 * np.pi) if wd2 > 0 else np.nan

    # --- plot ---
    matplot_styles()
    fig, (ax, axr) = plt.subplots(
        2, 1, sharex=True, figsize=(8, 6), gridspec_kw={"height_ratios": [3, 1]}
    )
    ax.plot(t, v, color=colours[0], lw=0.8, alpha=0.5, label="Experimental")
    ax.plot(t_a, v_a, color=colours[2], lw=1.5, label=f"Ripple-averaged ($T_r$ = {T_r*1e6:.1f} µs)")
    ax.plot(
        t_f, func(t_f, *popt), color=colours[1], ls="--", lw=1.8, label=f"{model.capitalize()} fit"
    )
    ax.axhline(popt[0], color=colours[3], ls=":", label="Fitted final voltage")
    fc = 1 / (2 * np.pi * tau) if tau else np.nan
    ax.set_title(rf"PC{pc}: $\tau$ = {format_sci(tau)} s, $f_c$ = {format_sci(fc)} Hz")
    ax.set_ylabel("PLL output voltage (V)")
    ax.legend()
    ax.grid(True)
    axr.plot(t_f, resid, color=colours[5], lw=1)
    axr.axhline(0, color="grey", lw=0.8)
    axr.set_xlabel("Time after step (s)")
    axr.set_ylabel("Residual (V)")
    axr.grid(True)
    fig.tight_layout()
    if save_plots:
        os.makedirs(save_location, exist_ok=True)
        fig.savefig(f"{save_location}/{name}.svg")
    if show_plots:
        plt.show()
    else:
        plt.close(fig)
    return out


def summary_plot(df):
    """
    Across all underdamped PC1 files: (left) fitted alpha vs 1/(2 tau), which
    should lie on y = x; (right) K = tau omega_n^2 vs tau, which should be
    constant if only the filter changed (K = K_D K_O fixed by the VCO).
    """
    d = df[(df["model"] == "underdamped") & (df["PC"] == 1)].dropna(subset=["tau"])
    if len(d) < 2:
        return
    matplot_styles()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.errorbar(1 / (2 * d["tau"]), d["alpha"], yerr=d["alpha_err"], fmt="x", color=colours[0])
    lim = [0, 1.1 * max((1 / (2 * d["tau"])).max(), d["alpha"].max())]
    a1.plot(lim, lim, color=colours[1], ls="--", label=r"$\alpha = 1/2\tau$")
    a1.set_xlabel(r"$1/2\tau$ (s$^{-1}$)")
    a1.set_ylabel(r"Fitted $\alpha$ (s$^{-1}$)")
    a1.legend()
    a2.errorbar(d["tau"], d["K"], yerr=d["K_err"], fmt="x", color=colours[0])
    a2.set_xlabel(r"$\tau = R_3C_2$ (s)")
    a2.set_ylabel(r"$K=\tau\omega_n^2$ (s$^{-1}$)")
    fig.tight_layout()
    if save_plots:
        os.makedirs(save_location, exist_ok=True)
        fig.savefig(f"{save_location}/transient_summary.svg")
    if show_plots:
        plt.show()
    else:
        plt.close(fig)


# ============================================================
# RUN OVER ALL FILES IN THE FOLDER
# ============================================================
if __name__ == "__main__":
    matplot_styles()
    files = sorted(glob(os.path.join(folder, f"Turn_on_PC{PC}_*.csv")))
    n_files = len(files)
    print(f"Found {n_files} files in {folder}\n")

    results = []
    failed = []  # (filename, error message) for files that crash
    t_start = time.time()

    for i, f in enumerate(files, start=1):
        name = os.path.basename(f)
        print(f"[{i}/{n_files}] {name}")
        t_file = time.time()
        try:
            r = analyse_file(f)
            results.append(r)
            # one-line summary of the fit so you can spot bad fits as they happen
            print(
                f"    {r['model']:<11} | alpha = {r['alpha']:.3g} s^-1 "
                f"(theory {r['alpha_theory']:.3g}) | f_d = {r['f_d']:.3g} Hz "
                f"| zeta = {r['zeta']:.3g} | rms resid = {r['rms_resid']:.3g} V "
                f"| {time.time() - t_file:.1f} s"
            )
        except Exception as e:  # keep going if one file fails
            failed.append((name, str(e)))
            print(f"    [skip] {e}")

        # estimated time remaining = mean time per file * files left
        elapsed = time.time() - t_start
        eta = elapsed / i * (n_files - i)
        print(f"    elapsed {elapsed:.0f} s, ETA {eta:.0f} s\n")

    print(
        f"Done: {len(results)} analysed, {len(failed)} failed, "
        f"total {time.time() - t_start:.0f} s"
    )
    for name, err in failed:
        print(f"  FAILED {name}: {err}")

    if results:
        summary = pd.DataFrame(results)
        print(summary.drop(columns=["file"]).to_string())
        if save_plots:
            os.makedirs(save_location, exist_ok=True)
            summary.to_csv(f"{save_location}/transient_summary.csv", index=False)
        summary_plot(summary)
