import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.5"
save_location = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.5/RCRcombos"
save_data = True
show_plots = False
# Ensure the save directory exists
os.makedirs(save_location, exist_ok=True)

file_names = os.listdir(folder)
capacitance = file_names

voltage_data = []
frequency_data = []
info_data = []
parsed_info = []


# Helper function to extract C, R1, R2 from the filename
def parse_filename(filename):
    params = {"c": None, "r1": None, "r2": None}
    parts = filename.lower().split("_")
    for p in parts:
        if p.startswith("c="):
            params["c"] = p[2:]
        elif p.startswith("r1="):
            params["r1"] = p[3:]
        elif p.startswith("r2="):
            params["r2"] = p[3:]
    return params


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
        error_voltage = get_voltage_errors(voltage_data[idx])
        x_fit, y_fit, gradient, m_err  = finding_slope(
            voltage_data[idx],
            frequency_data[idx],
            error_x=error_voltage,
            error_y=error_freq
        )
        k_o = np.absolute(2 * np.pi * gradient * 1e3)
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
        label+= rf", $K_{{O}}$ = {k_o :.4f}±{m_err :.4f} Hz/V, "

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
    if varying_param == "r1":
        plt.figure()
        matplot_styles()
        ax = plt.gca()
        plt.plot(x_data_values, k_o_values, marker="x", linestyle="none", color="black")
        x_fit, y_fit, p, p_err = get_poly_fit(x_data_values, k_o_values)
        plt.text(
            0.025,
            0.9,
            rf"$R^{{2}}$={p_err[2]:.4f}" + "\n" + f"m={format_sci_err(p[0], p_err[0])}",
            fontsize=8,
            transform=ax.transAxes,
        )
        plt.plot(x_fit, y_fit, color=colours[0], linestyle="--")
        plt.ylabel(rf"$K_{{O}}$ (Hz/V)")
        plt.xlabel(rf"$1/R_{{1}}$ ($\Omega^{-1}$)")
        plt.title(
            rf"$K_{{O}}$ vs 1/$R_{{1}}$ ($C=1$ nF, $R_2=${format_val(params['r2'])})"
        )
    if varying_param == "r2":
        plt.figure()
        matplot_styles()
        ax = plt.gca()
        plt.plot(
            x_data_values, f_min_values, marker="x", linestyle="none", color="black"
        )
        x_fit, y_fit, p, p_err = get_poly_fit(x_data_values, f_min_values)
        plt.text(
            0.025,
            0.9,
            rf"$R^{{2}}$={p_err[2]:.4f} "
            + "\n"
            + f"m={format_sci_err(p[0], p_err[0])}",
            fontsize=8,
            transform=ax.transAxes,
        )
        plt.plot(x_fit, y_fit, color=colours[0], linestyle="--")
        plt.ylabel(rf"$f_{{min}}$ (Hz)")
        plt.xlabel(rf"$1/R_{{2}}$ ($\Omega^{-1}$)")
        plt.title(
            rf"$f_{{min}}$ vs 1/$R_{{2}}$ ($C=1$ nF, $R_1=${format_val(params['r1'])})"
        )
    elif varying_param == "c":  # and np.inf not in :
        plt.figure()
        matplot_styles()
        ax = plt.gca()
        inverse_k_o_values = [1 / k if k != 0 else np.inf for k in k_o_values]
        plt.plot(
            x_data_values,
            inverse_k_o_values,
            marker="x",
            linestyle="none",
            color="black",
        )
        x_fit, y_fit, p, p_err = get_poly_fit(x_data_values, inverse_k_o_values)
        C_stray = p[1] / p[0]
        C_stray_err = np.sqrt((p_err[1] / p[1]) ** 2 + (p_err[0] / p[0]) ** 2) * abs(
            C_stray
        )
        plt.plot(x_fit, y_fit, color=colours[0], linestyle="--")
        plt.text(
            0.025,
            0.85,
            rf"$R^{{2}}$={p_err[2]:.4f} "
            + "\n"
            + f"m={format_sci_err(p[0], p_err[0])}"
            + "\n"
            + f"$C_{{stray}}$={C_stray*1e12:.0f} ± {C_stray_err*1e12:.0f}pF",
            fontsize=8,
            transform=ax.transAxes,
        )
        plt.ylabel(rf"$1/K_{{O}}$ (Hz/V)")
        plt.xlabel(rf"$C$ (F)")
        plt.title(
            rf"$K_{{O}}$ vs 1/$C$ ($R_1=${format_val(params['r1'])}, $R_2=${format_val(params['r2'])})"
        )
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.tight_layout()

    if save_data:
        plt.savefig(os.path.join(save_location, ("line_fits_" + filename_out)), dpi=150)
    if show_plots:
        plt.show()
    else:
        plt.clf()
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


print(f"All plots completed and saved to {save_location}")
