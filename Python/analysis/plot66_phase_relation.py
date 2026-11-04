import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

# -----------------------------
# Settings
# -----------------------------
#NEEDS BETTER WORKING

PC = 2
save_data = True
show_plot = False

# Measurement uncertainties
t_min = 10e-7
vco_in_err = get_voltage_errors(1)  # V
phase_err_deg = 0.1  # Original measurement uncertainty in degrees
phase_err = np.deg2rad(phase_err_deg)

folder = rf"./data/6.6/PC{PC}/RCvary"
save_location = rf"./analysis_images/6.6/PC{PC}/RCvary/phaseAnalysis"

# Ratio tolerance for considering a point locked
ratio_tolerance = 0.001

# Minimum percentage of points that must be locked
minimum_locked_fraction = 0.10

os.makedirs(save_location, exist_ok=True)

file_names = sorted([f for f in os.listdir(folder) if f.lower().endswith(".csv")])

print("Running")
# Store K_O results from all CSV files
ko_results = []
kd_results = []

component_fraction = 0.05


def calculate_weighted_mean(results, value_name, systematic_fraction=0.05):

    values = np.array([result[value_name] for result in results], dtype=float)

    errors = np.array([result["stat_error"] for result in results], dtype=float)

    # Remove invalid results
    valid = np.isfinite(values) & np.isfinite(errors) & (errors > 0)

    values = values[valid]
    errors = errors[valid]

    if len(values) == 0:
        return None

    # Inverse variance weighting
    weights = 1 / errors**2

    weighted_mean = np.sum(weights * values) / np.sum(weights)

    # Statistical uncertainty
    statistical_error = np.sqrt(1 / np.sum(weights))

    # Check consistency between measurements
    chi_squared = np.sum(((values - weighted_mean) / errors) ** 2)

    degrees_of_freedom = len(values) - 1

    if degrees_of_freedom > 0:

        reduced_chi_squared = chi_squared / degrees_of_freedom

        # Inflate uncertainty if measurements scatter more
        # than expected from their quoted statistical errors
        if reduced_chi_squared > 1:
            statistical_error *= np.sqrt(reduced_chi_squared)

    else:
        reduced_chi_squared = np.nan

    # Common systematic uncertainty from components
    systematic_error = abs(weighted_mean) * systematic_fraction

    # Final combined uncertainty
    total_error = np.sqrt(statistical_error**2 + systematic_error**2)

    return {
        "mean": weighted_mean,
        "stat_error": statistical_error,
        "systematic_error": systematic_error,
        "total_error": total_error,
        "reduced_chi_squared": reduced_chi_squared,
        "number": len(values),
    }


for csv in file_names:

    # -----------------------------
    # Read CSV
    # -----------------------------

    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    awg_freq = df["awg_freq"].values
    vco_freq = df["vco_freq"].values
    phase_diff = np.deg2rad(df["phase_diff"].values)
    vco_in_val = df["vco_in_val"].values

    # Extract ratio
    if "ratio" in df.columns:
        ratio = df["ratio"].values
    else:
        ratio = awg_freq / vco_freq

    # -----------------------------
    # Extract filename parameters
    # -----------------------------

    params = parse_filename(csv)

    r1 = params["r1"] or "N/A"
    r2 = params["r2"] or "N/A"
    c = params["c"] or "N/A"
    fc = params["fc"] or "N/A"

    title = (
        rf"$PC{PC},\ R_1$={format_val(r1)}, "
        rf"$R_2$={format_val(r2)}, "
        rf"$C$={format_val(c)}, "
        rf"$f_c$={format_sci(data_to_val(fc))}Hz"
    )

    save_name = f"fc={fc},{min(awg_freq)}to{max(awg_freq)}"

    # =====================================================
    # 1. FIND LOCKED REGION
    # =====================================================

    valid_ratio = np.isfinite(ratio)

    lock_mask = valid_ratio & np.isclose(ratio, 1.0, rtol=0, atol=ratio_tolerance)

    total_valid = np.sum(valid_ratio)
    n_locked = np.sum(lock_mask)

    if total_valid == 0:
        print(f"\nSkipping {csv}: no valid ratio data.")
        continue

    locked_fraction = n_locked / total_valid

    # Only continue if MORE than 30% of the data is locked
    if locked_fraction <= minimum_locked_fraction:
        print("Skipping: less than or equal to 30% locked.")
        continue

    locked_freq = awg_freq[lock_mask]

    # =====================================================
    # 2. AWG FREQUENCY AGAINST VCO INPUT VOLTAGE
    # =====================================================

    ko_mask = lock_mask & np.isfinite(awg_freq) & np.isfinite(vco_in_val)

    voltage_ko = vco_in_val[ko_mask]

    # Convert frequency from kHz to Hz
    frequency_hz = awg_freq[ko_mask] * 1e3

    # Create uncertainty arrays
    voltage_err = np.full(len(voltage_ko), vco_in_err)
    frequency_err = frequency_err = t_min * frequency_hz**2

    if len(voltage_ko) >= 3 and np.unique(voltage_ko).size >= 2:

        # SciPy ODR fit (includes uncertainties in both axes)
        voltage_fit, frequency_fit, p, p_err = get_poly_fit(
            voltage_ko, frequency_hz, order=1, error_x=voltage_err, error_y=frequency_err
        )

        gradient_hz = p[0]
        intercept_hz = p[1]

        K_O_stat_err = p_err[0]

        # Convert to angular frequency gradient
        K_O = 2 * np.pi * gradient_hz
        K_O_err = 2 * np.pi * K_O_stat_err
        ko_results.append(
            {
                "file": csv,
                "K_O": K_O,
                "error": K_O_err,
                "stat_error": K_O_stat_err,
                "locked_percentage": locked_fraction * 100,
            }
        )

        # Plot
        matplot_styles()

        fig, ax = plt.subplots(figsize=(8, 6))

        ax.errorbar(
            voltage_ko,
            awg_freq[ko_mask],
            xerr=voltage_err,
            yerr=frequency_err / 1e3,
            fmt="x",
            markersize=6,
            capsize=3,
            elinewidth=1,
        )

        ax.plot(
            voltage_fit,
            frequency_fit / 1e3,
            label=(rf"$K_{{O}}$ = {format_sci_err(K_O,K_O_err)} " rf"Hz/V"),
        )

        ax.set_xlabel("VCO input voltage (V)")
        ax.set_ylabel("AWG frequency (kHz)")
        ax.set_title(title)
        ax.legend()

        fig.tight_layout()

        if save_data:
            fig.savefig(
                os.path.join(save_location, save_name + "_KO.svg"), dpi=300, bbox_inches="tight"
            )

        if show_plot:
            plt.show()

        plt.close(fig)
    else:
        print("Not enough valid points to calculate K_O.")

    # =====================================================
    # 3. VCO INPUT VOLTAGE AGAINST PHASE DIFFERENCE (K_D)
    # =====================================================

    phase_mask = lock_mask & np.isfinite(phase_diff) & np.isfinite(vco_in_val)

    phase = phase_diff[phase_mask]
    voltage_phase = vco_in_val[phase_mask]

    phase_unc = np.full(len(phase), phase_err)
    voltage_unc = np.full(len(voltage_phase), vco_in_err)

    if len(phase) >= 3 and np.unique(phase).size >= 2:

        # ODR fit: voltage against phase (both in SI units)
        phase_fit, voltage_fit, p, p_err = get_poly_fit(
            phase, voltage_phase, order=1, error_x=phase_unc, error_y=voltage_unc
        )

        # K_D = dV/d(phi)
        K_D = p[0]
        K_D_stat_err = p_err[0]

        # Include component uncertainty (5%)
        K_D_component_err = abs(K_D) * component_fraction

        # Combined uncertainty
        K_D_err = np.sqrt(K_D_stat_err**2 + K_D_component_err**2)

        print("\nPhase detector gain:")
        print(f"K_D = ({K_D:.5g} +/- {K_D_err:.3g}) V/rad")

        # Plot
        matplot_styles()

        fig, ax = plt.subplots(figsize=(8, 6))

        ax.errorbar(
            phase,
            voltage_phase,
            xerr=phase_unc,
            yerr=voltage_unc,
            fmt="x",
            markersize=6,
            capsize=3,
            elinewidth=1,
            label="Locked data",
        )

        ax.plot(
            phase_fit, voltage_fit, label=(rf"$K_D = ({K_D:.3g} \pm " rf"{K_D_err:.2g})$ V/rad")
        )

        ax.set_xlabel("Phase difference (rad)")
        ax.set_ylabel("VCO input voltage (V)")
        ax.set_title(title)

        ax.legend()
        fig.tight_layout()

        if save_data:
            fig.savefig(
                os.path.join(save_location, save_name + "_KD.png"), dpi=300, bbox_inches="tight"
            )

        if show_plot:
            plt.show()

        plt.close(fig)

        # Store result for final summary
        kd_results.append(
            {
                "file": csv,
                "K_D": K_D,
                "error": K_D_err,
                "stat_error": K_D_stat_err,
                "locked_percentage": locked_fraction * 100,
            }
        )
    else:
        print("Not enough valid points to calculate K_D.")

# =====================================================
# FINAL K_O RESULTS
# =====================================================

# =====================================================
# SUM OF ALL K RESULTS
# =====================================================

print("\n" + "=" * 75)
print("TOTAL K RESULTS")
print("=" * 75)

# =====================================================
# FINAL WEIGHTED RESULTS
# =====================================================

print("\n" + "=" * 75)
print("FINAL WEIGHTED GAIN RESULTS")
print("=" * 75)

# Calculate K_O
KO_final = calculate_weighted_mean(
    ko_results,
    "K_O",
    systematic_fraction=component_fraction
)


# Calculate K_D
KD_final = calculate_weighted_mean(
    kd_results,
    "K_D",
    systematic_fraction=component_fraction
)

# =====================================================
# FIGURE: FINAL K_O AND K_D RESULTS
# =====================================================

matplot_styles()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

def plot_gain_results(ax, results, final_result, value_name, ylabel, title):

    if final_result is None:
        ax.set_title(title + " (no results)")
        return

    # Extract individual results
    values = np.array([
        result[value_name] for result in results
    ], dtype=float)

    errors = np.array([
        result["error"] for result in results
    ], dtype=float)

    # Remove invalid values
    valid = (
        np.isfinite(values)
        & np.isfinite(errors)
        & (errors >= 0)
    )

    values = values[valid]
    errors = errors[valid]

    x = np.arange(1, len(values) + 1)

    # Plot individual measurements
    ax.errorbar(
        x,
        values,
        yerr=errors,
        fmt="x",
        markersize=7,
        capsize=4,
        elinewidth=1.2,
        label="Individual measurements"
    )

    # Final weighted mean
    mean = final_result["mean"]
    mean_err = final_result["total_error"]

    ax.axhline(
        mean,
        linestyle="--",
        linewidth=1.5,
        label="Weighted mean"
    )

    # Uncertainty region around weighted mean
    ax.axhspan(
        mean - mean_err,
        mean + mean_err,
        alpha=0.2,
        label="Combined uncertainty"
    )

    ax.set_xlabel("Dataset number")
    ax.set_ylabel(ylabel)
    if value_name == "K_O":
        ax.set_title(
            f"{title}\n"
            rf"$K_{{O}}$={format_sci_err(mean,mean_err)}Hz/V"
        )
    else:
        ax.set_title(
            f"{title}\n"
            rf"$K_{{D}}$={format_sci_err(mean,mean_err)}Hz/V"
        )

    ax.set_xticks(x)
    ax.legend(fontsize=9)


# K_O plot
plot_gain_results(
    axes[0],
    ko_results,
    KO_final,
    "K_O",
    r"$K_O$ (Hz/V)",
    r"VCO gain ($K_O$)"
)

# K_D plot
plot_gain_results(
    axes[1],
    kd_results,
    KD_final,
    "K_D",
    r"$K_D$ (V/rad)",
    r"Phase detector gain ($K_D$)"
)

fig.suptitle("Final PLL Gain Measurements", fontsize=14)

fig.tight_layout()

# Save figure
if save_data:
    fig.savefig(
        os.path.join(
            save_location,
            f"final_KO_KD_results_PC{PC}.svg"
        ),
        dpi=300,
        bbox_inches="tight"
    )

if show_plot:
    plt.show()

plt.close(fig)


print("\nCompleted")
