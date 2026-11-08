import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import scipy

from plot_style import *
from line_finder import *


PC = 1

folder = rf"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.6/PC{PC}"
save_location = (
    rf"C:/Users/harry/Desktop/university work/year 3/E1A-lab/analysis_images/6.6/PC{PC}/current_mirror"
)

save_data = True
show_plot = False

file_names = os.listdir(folder)
capacitance = file_names

time_data = []
dv_data = []
frequency = []

info_data = []

tmp_path = f"{folder}/capacitor_current"
subfolders = os.listdir(tmp_path)
for csv in subfolders:
    if csv.endswith(".csv"):
        tmp_path_2 = f"{folder}/capacitor_current/{csv}"
        df = pd.read_csv(tmp_path_2)
        time_data.append(df["time"].values)
        dv = df["dV data"].values
        frequency.append(parse_filename(csv)["f="][:-5]) 
        dv_data.append(dv)
        info_data.append(csv[17:-4])


def calculate_filtered_gradient(time, dV, C, ax, window_sections=50):
    time_sections = []
    voltage_sections = []

    final_time_data = []
    final_current_data = []
    final_current_errors = []

    # Split the data into sections
    for i in range(window_sections):
        start_index = len(time) * i // window_sections
        end_index = len(time) * (i + 1) // window_sections

        if end_index - start_index < 2:
            continue

        time_sections.append(time[start_index:end_index])
        voltage_sections.append(dV[start_index:end_index])

    # Calculate gradient and uncertainty for each section
    for t_section, v_section in zip(time_sections, voltage_sections):

        x_fit, y_fit, p, p_err = get_poly_fit(t_section, v_section)

        current = abs(p[0] * C)
        current_error = current * np.sqrt((p_err[0] / p[0]) ** 2 + 0.05**2)

        midpoint_time = (t_section[0] + t_section[-1]) / 2

        final_time_data.append(midpoint_time)
        final_current_data.append(current)
        final_current_errors.append(current_error)

    # Calculate mean current
    mean_current = scipy.stats.trim_mean(final_current_data, proportiontocut=0.1)

    # Filter out values greater than 1.5 times the mean
    filtered_data = [
        (t, current, error)
        for t, current, error in zip(final_time_data, final_current_data, final_current_errors)
        if current <= 1.5* mean_current and current >= 0.5 * mean_current
    ]

    # Separate filtered values
    final_time_data = [item[0] for item in filtered_data]
    final_current_data = [item[1] for item in filtered_data]
    final_current_errors = [item[2] for item in filtered_data]

    # Fit a flat line (mean current)
    flat_current = scipy.stats.trim_mean(final_current_data, proportiontocut=0.1)

    # Combined relative uncertainty from C and R
    relative_uncertainty = np.sqrt(0.10**2 + 0.05**2)

    # Uncertainty in the mean current
    flat_current_error = flat_current * relative_uncertainty

    # Plot current with error bars
    ax.errorbar(
        final_time_data,
        final_current_data,
        yerr=final_current_errors,
        color="blue",
        marker="x",
        linestyle="none",
        capsize=3,
    )

    # Plot flat line of best fit
    ax.axhline(
        y=flat_current,
        color="blue",
        linestyle="--",
        label=f"Mean current = {format_sci_err(flat_current,flat_current_error)} A",
    )

    return final_time_data, final_current_data, final_current_errors, flat_current, flat_current_error


plot_styles = {"marker": "x", "linestyle": "none"}
print("Plotting data...")

for i in range(len(info_data)):

    matplot_styles()

    info = info_data[i]
    p = parse_filename(info)

    R1 = p["r1"]
    R2 = p["r2"]
    C = p["c"]
    C_val = 1e-9

    # Create ONE figure with two subplots
    fig, ax1  = plt.subplots(1, 1, figsize=(8, 5))

    # LEFT: Voltage against time
    ax1.plot(time_data[i], dv_data[i], color="purple", label="Capacitor voltage")

    ax1.axhline(y=0, color="black", linewidth=1.5)
    ax1.set_ylabel("Voltage (V)")
    ax1.set_xlabel("Time (s)")
    ax1.set_xlim(left=0)
    ax1.set_ylim(-5, 5)
    ax1.legend()

    ax1.set_title(f"Voltage difference over capacitor (C={C}, R1={R1}, R2={R2})")

    fig.suptitle(f"Capacitor voltage and current against time"+"\n"+f"Using PC{PC} with an input frequency f={frequency[i]}kHz")

    fig.tight_layout()

    os.makedirs(save_location, exist_ok=True)

    if save_data:
        fig.savefig(f"{save_location}/Capacitor_current_R1={R1}_R2={R2}_C={p['c']}_f={frequency[i]}kHz.svg")
        plt.close()

    if show_plot:
        plt.show()
