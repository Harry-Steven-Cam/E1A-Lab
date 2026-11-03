import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.5"
save_location = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.5/RCRcombos"
save_data = False
show_plots = True
# Ensure the save directory exists
os.makedirs(save_location, exist_ok=True)

file_names = os.listdir(folder)
capacitance = file_names

voltage_data = []
frequency_data = []
info_data = []
parsed_info = []

# Load all data
for c in capacitance:
    if c != "current_mirror":
        tmp_path = f"{folder}/{c}"
        if not os.path.isdir(tmp_path):
            continue
        subfolders = os.listdir(tmp_path)
        for csv in subfolders:
            if not csv.endswith(".csv"):
                continue
            tmp_path_2 = f"{folder}/{c}/{csv}"
            df = pd.read_csv(tmp_path_2)

            freq_vals = df["Frequency"].values
            volt_vals = df["Voltage data"].values
            filename_no_ext = csv[0:-4]

            frequency_data.append(freq_vals)
            voltage_data.append(volt_vals)
            info_data.append(filename_no_ext)
            parsed_info.append(
                parse_filename(filename_no_ext)
            )  # R12 C values for corresponding data

combined_plot_data = {"r1": [], "r2": [], "c": [], "r1_err": []}


# Main plotting function
def create_and_save_plot(indices, title, varying_param, filename_out, fixed_param=None):
    if not indices:
        return
    # ---------------------- setting styles and axis -----------------------------
    plt.figure()
    matplot_styles()
    ax = plt.gca()
    max_freq = 0
    # ---------------------- gathering values for 1/R1 and 1/R2 plots -----------------------------
    k_o_values = []
    k_err_values = []
    f_min_values = []
    x_data_values = []
    # ---------------------- plot each line -----------------------------
    for count, idx in enumerate(indices):
        # ---------------------- cleaning labels -----------------------------
        params = parsed_info[idx]  # gets relevant data names for the varying variable
        if varying_param == "r1":
            label = f"$R_1$ = {format_val(params['r1'])}"
            x_data_values.append(1 / data_to_val(params["r1"]))
        elif varying_param == "r2":
            label = f"$R_2$ = {format_val(params['r2'])}"
            x_data_values.append(1 / data_to_val(params["r2"]))
        elif varying_param == "c":
            label = f"$C$ = {format_val(params['c'])}"
            x_data_values.append(data_to_val(params["c"]))
        else:
            label = info_data[idx]  # if it has no name
        # ---------------------- find slope :) (and fit over region)-----------------------------
        t_min = 10e-7
        error_freq = t_min * (frequency_data[idx]) ** 2  # err propagation formula :)
        error_voltage = get_voltage_errors(voltage_data[idx], resolution_bits=6)
        x_fit, y_fit, gradient, m_err = finding_slope(
            voltage_data[idx],
            frequency_data[idx],
            error_x=error_voltage,
            error_y=error_freq,
        )
        k_o = np.absolute(2 * np.pi * gradient * 1e3)
        k_err = np.absolute(2 * np.pi * m_err * 1e3)
        f_min = frequency_data[idx][0] * 1e3
        f_centre = (frequency_data[idx][-1] + frequency_data[idx][0]) * 1e3 / 2
        f_ratio = (
            np.absolute(
                (frequency_data[idx][-1] - frequency_data[idx][0])
                / frequency_data[idx][0]
            )
            if frequency_data[idx][0] != 0
            else r"${\infty}$"
        )
        k_o_values.append(k_o)
        k_err_values.append(k_err)
        f_min_values.append(f_min)
        """text = (
            label
            + rf", $K_{{O}}$ = {format_sci_err(k_o,m_err,decimals=4)} Hz/V, "
            + rf"$f_{{min}}$ = {format_sci(f_min)}Hz, "
            + rf"$f_{{centre}}$ = {format_sci(f_centre)}Hz, "
            + (
                rf"$f_{{ratio}}$ = {f_ratio : .1f} "
                if isinstance(f_ratio, (int, float))
                else rf"$f_{{ratio}}$ = {f_ratio}"
            )
        )"""
        # plt.text(0, -0.2 - 0.1 * count, text, fontsize=8, transform=ax.transAxes)
        # here for displaying all the interesting info
        # ---------------------- plot -----------------------------
        label += rf", $K_{{O}}$ = {k_o :.4f}±{m_err :.4f} Hz/V"

        plt.plot(
            voltage_data[idx],
            frequency_data[idx],
            color=colours[count % len(colours)],
            label=label,
            alpha=0.6,
        )
        plt.plot(
            x_fit, y_fit, color=colours[count % len(colours)], linestyle="--", alpha=1
        )
        # ---------------------- for ticks -----------------------------
        if max_freq < max(frequency_data[idx]):
            max_freq = max(frequency_data[idx])

    # ---------------------- setting styles and axis -----------------------------
    ax.set_xticks(np.arange(0, 6, 1))
    if max_freq < 200:
        ax.set_yticks(np.arange(0, max_freq + 20, 20))
    else:
        ax.set_yticks(np.arange(0, max_freq + 20, 100))
    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Voltage (V)")
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.title(title)
    plt.legend(fontsize=8)
    plt.tight_layout()
    if save_data:
        plt.savefig(os.path.join(save_location, ("curves_" + filename_out)), dpi=300)
    if show_plots:
        plt.show()
    else:
        plt.clf()
        plt.close()
    fixed_params = parsed_info[indices[0]]
    if varying_param == "r1":
        combined_plot_data["r1"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "y": np.asarray(k_o_values, dtype=float),
                "y_err": np.asarray(k_err_values, dtype=float),
                "label": (
                    f"R2={format_val(fixed_params['r2'])}, "
                    f"C={format_val(fixed_params['c'])}"
                ),
            }
        )
    elif varying_param == "r2":
        combined_plot_data["r2"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "y": np.asarray(f_min_values, dtype=float),
                "label": (
                    f"R1={format_val(fixed_params['r1'])}, "
                    f"C={format_val(fixed_params['c'])}"
                ),
            }
        )
    elif varying_param == "c":
        inverse_k_o_values = np.array([1 / k if k != 0 else np.inf for k in k_o_values])
        combined_plot_data["c"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "y": inverse_k_o_values,
                "label": (
                    f"R1={format_val(fixed_params['r1'])}, "
                    f"R2={format_val(fixed_params['r2'])}"
                ),
            }
        )


def create_combined_plot(param, ylabel, xlabel, title, filename):
    datasets = combined_plot_data[param]
    if not datasets:
        return

    plt.figure()
    matplot_styles()
    ax = plt.gca()

    for i, data in enumerate(datasets):
        x = data["x"]
        y = data["y"]

        # Get uncertainty in y (only for R1 plot)
        y_err = data.get("y_err", np.zeros_like(y))

        # Remove invalid values
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(y_err) & (y_err > 0)

        x = x[valid]
        y = y[valid]
        y_err = y_err[valid]

        if len(x) == 0:
            continue

        colour = colours[i % len(colours)]

        # Plot experimental data with error bars
        plt.errorbar(
            x,
            y,
            yerr=y_err,
            marker="x",
            linestyle="none",
            color=colour,
            alpha=0.8,
            capsize=3,
        )

        # Fit and calculate R squared
        r_squared = np.nan
        gradient = np.nan
        gradient_err = np.nan

        if len(x) >= 2 and len(np.unique(x)) >= 2:
            try:
                if param == "r1":

                    # Weighted linear fit using KO uncertainties
                    weights = 1 / y_err

                    # Check that uncertainties and weights are valid
                    if (
                        np.all(np.isfinite(weights))
                        and np.all(weights > 0)
                        and len(x) >= 2
                        and len(np.unique(x)) >= 2
                    ):

                        p, cov = np.polyfit(
                            x,
                            y,
                            deg=1,
                            w=weights,
                            cov="unscaled",
                        )
                    gradient = p[0]
                    intercept = p[1]

                    gradient_err = np.sqrt(cov[0, 0])
                    intercept_err = np.sqrt(cov[1, 1])

                    # Generate fitted line
                    x_fit = np.linspace(min(x), max(x), 200)
                    y_fit = np.polyval(p, x_fit)

                    # Calculate R squared
                    y_pred = np.polyval(p, x)
                    ss_res = np.sum((y - y_pred) ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)

                    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

                else:
                    # Retain your original fitting method
                    x_fit, y_fit, p, p_err = get_poly_fit(x, y)

                    gradient = p[0]
                    gradient_err = p_err[0]
                    intercept = p[1]
                    intercept_err = p_err[1]
                    r_squared = p_err[2]

                plt.plot(
                    x_fit,
                    y_fit,
                    linestyle="--",
                    color=colour,
                    alpha=0.8,
                )

            except (RuntimeError, ValueError, np.linalg.LinAlgError) as e:
                print(f"Fit failed for {data['label']}: {e}")

        # Legend entry
        m_unit = (
            r"Hz/V$\Omega$"
            if param == "r1"
            else r"Hz/V$\Omega$" if param == "r2" else "HzF/V"
        )

        if np.isfinite(gradient) and np.isfinite(gradient_err):
            gradient_text = f"{gradient:.3e} ± {gradient_err:.3e}"
        else:
            gradient_text = "Fit unavailable"

        legend_label = (
            data["label"]
            + f", m = {gradient_text} {m_unit}"
            + f", R² = {r_squared:.4f}"
        )

        plt.plot(
            [],
            [],
            color=colour,
            marker="x",
            linestyle="--",
            label=legend_label,
        )

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)

    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.legend(fontsize=7)
    plt.tight_layout()

    if save_data:
        plt.savefig(os.path.join(save_location, filename), dpi=300)

    if show_plots:
        plt.show()
    else:
        plt.close()


print("Generating plots...")

# 1. Cycle through Fixed R1 values for C=1000pF (varying R2)
# ---------------------- sets a container for all R1R2C combos we use  -----------------------------

r1_values = set(
    p["r1"] for p in parsed_info if p["c"] == "1000pf" and p["r1"] is not None
)
# R1_values is just all the possible value names
for r1 in r1_values:
    # gets all the indexs of the data that match the current R1 value and C=1000pF
    idx_list = [
        i for i, p in enumerate(parsed_info) if p["c"] == "1000pf" and p["r1"] == r1
    ]
    if idx_list:
        create_and_save_plot(
            idx_list,
            f"VCO Response ($C=1$ nF, $R_1=${format_val(r1)})",  # title
            "r2",  # varying param
            f"Fixed_R1_{r1}_C_1000pF.svg",  # save name
        )


# 2. Cycle through Fixed R2 values for C=1000pF (varying R1)
r2_values = set(
    p["r2"] for p in parsed_info if p["c"] == "1000pf" and p["r2"] is not None
)
for r2 in r2_values:
    idx_list = [
        i for i, p in enumerate(parsed_info) if p["c"] == "1000pf" and p["r2"] == r2
    ]
    if idx_list:
        create_and_save_plot(
            idx_list,
            f"VCO Response ($C=1$ nF, $R_2=${format_val(r2)})",
            "r1",
            f"Fixed_R2_{r2}_C_1000pF.svg",
        )


# 3. Cycle through all unique (R1, R2) combinations (varying C)
r1_r2_pairs = set(
    (p["r1"], p["r2"])
    for p in parsed_info
    if p["r1"] is not None and p["r2"] is not None
)
for r1, r2 in r1_r2_pairs:
    idx_list = [i for i, p in enumerate(parsed_info) if p["r1"] == r1 and p["r2"] == r2]
    # Only plot if there's more than one capacitance to compare
    if len(idx_list) > 1:
        create_and_save_plot(
            idx_list,
            f"VCO Response ($R_1=${format_val(r1)}, $R_2=${format_val(r2)})",
            "c",
            f"Fixed_R1_{r1}_R2_{r2}_Varying_C.svg",
            fixed_param=[data_to_val(r1), data_to_val(r2)],
        )

# ------------------------------------------------------------
# 1. KO against 1/R1
# ------------------------------------------------------------

create_combined_plot(
    param="r1",
    ylabel=r"$K_O$ (Hz/V)",
    xlabel=r"$1/R_1$ ($\Omega^{-1}$)",
    title=r"$K_O$ vs $1/R_1$",
    filename="Combined_KO_vs_invR1.svg",
)


# ------------------------------------------------------------
# 2. Minimum frequency against 1/R2
# ------------------------------------------------------------

create_combined_plot(
    param="r2",
    ylabel=r"$f_{\min}$ (Hz)",
    xlabel=r"$1/R_2$ ($\Omega^{-1}$)",
    title=r"$f_{\min}$ vs $1/R_2$",
    filename="Combined_fmin_vs_invR2.svg",
)


# ------------------------------------------------------------
# 3. Inverse KO against capacitance
# ------------------------------------------------------------

create_combined_plot(
    param="c",
    ylabel=r"$1/K_O$ (V/Hz)",
    xlabel=r"$C$ (F)",
    title=r"$1/K_O$ vs $C$",
    filename="Combined_invKO_vs_C.svg",
)
print(f"All plots completed and saved to {save_location}")
