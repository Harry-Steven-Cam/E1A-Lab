import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-lab/data/6.5"
save_location = r"C:/Users/harry/Desktop/university work/year 3/E1A-lab/analysis_images/6.5/current_mirror"

save_data = True
show_plot = False

file_names = os.listdir(folder)
capacitance = file_names

time_data = []
dv_data = []
vco_out_data = []
r1_voltage_data = []
r2_voltage_data = []

info_data = []

tmp_path = f"{folder}/current_mirror"
subfolders = os.listdir(tmp_path)
for csv in subfolders:
    tmp_path_2 = f"{folder}/current_mirror/{csv}"
    df = pd.read_csv(tmp_path_2)
    time_data.append(df["time"].values)
    dv_data.append(df["capacitor_voltage"].values)
    vco_out_data.append(df["vco_out"].values)
    r1_voltage_data.append(df["r1_voltage"].values)
    r2_voltage_data.append(df["r2_voltage"].values)
    info_data.append(csv[17:-4])


def calculate_filtered_gradient(time, dV, C, ax, window_sections=50):
    time_sections = []
    voltage_sections = []
    for i in range(window_sections - 1):
        start_index = len(time) * i // window_sections
        end_index = len(time) * (i + 1) // window_sections
        time_sections.append(time[start_index:end_index])
        voltage_sections.append(dV[start_index:end_index])
    current_values = []
    time_values_iplot = []
    for x in range(len(voltage_sections)):
        x_fit, y_fit, p, p_err = get_poly_fit(time_sections[x], voltage_sections[x])
        # goes through each little section
        current_values.append(p[0] * C)
        time_values_iplot.append(x_fit)
    abs_current_values = [abs(val) for val in current_values]
    mean_current = np.mean(abs_current_values)
    for i in range(len(current_values)):
        x_fit, y_fit, p, p_err = get_poly_fit(time, dV)
        ax.plot(
            time_values_iplot[i],
            np.full_like(
                time_values_iplot[i],
                (
                    current_values[i]
                    if abs(current_values[i]) < 1.25 * mean_current
                    else 0
                ),
            ),
            color="red",
            label="measured current" if i == 0 else "",
        )


plot_styles = {"marker": "x", "linestyle": "none"}
print("Plotting data...")

for i in range(len(info_data)):

    matplot_styles()

    info = info_data[i]
    p = parse_filename(info)

    R1 = p["r1"]
    R2 = p["r2"]
    C = p["c"]
    C_val = data_to_val(C)

    # Create ONE figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # LEFT: Voltage against time
    ax1.plot(time_data[i], dv_data[i], color="purple", label="Capacitor voltage")
    ax1.plot(time_data[i], vco_out_data[i], color="black", label="VCO output")
    ax1.plot(time_data[i], r1_voltage_data[i], color="blue", label="R1 voltage")
    ax1.plot(time_data[i], r2_voltage_data[i], color="red", label="R2 voltage")

    ax1.axhline(y=0, color="black", linewidth=1.5)
    ax1.set_ylabel("Voltage (V)")
    ax1.set_xlabel("Time (s)")
    ax1.set_xlim(left=0)
    ax1.set_ylim(-5, 5)
    ax1.legend()

    # RIGHT: Current against time
    calculate_filtered_gradient(time_data[i], dv_data[i], C_val, ax2)

    ax2.set_ylabel("Current (A)")
    ax2.set_xlabel("Time (s)")
    ax2.set_xlim(left=0)
    freq = freqFinder(vco_out_data[i], time_data[i])
    dVpp = 3.7
    theory_current = 2 * C_val * dVpp * freq
    I_in = np.mean(r1_voltage_data[i]) / data_to_val(R1) + np.mean(
        r2_voltage_data[i]
    ) / data_to_val(R2)
    ax2.axhline(y=0, color="black", linewidth=1.5)
    ax2.axhline(y=I_in, color="blue", label=r"$I_{in}$", linestyle="--")
    ax2.axhline(y=-I_in, color="blue", linestyle="--")
    ax2.axhline(
        y=theory_current, color="blue", label="Theoretical current", linestyle="--"
    )
    ax2.axhline(y=-theory_current, color="blue", linestyle="--")
    ax2.legend()
    ax1.set_title(f"Voltage difference over capacitor (C={C}, R1={R1}, R2={R2})")
    ax2.set_title(f"Current over capacitor (C={C}, R1={R1}, R2={R2})")

    fig.tight_layout()

    os.makedirs(save_location, exist_ok=True)

    if save_data:
        fig.savefig(f"{save_location}/Capacitor_current_R1={R1}_R2={R2}_C={p['c']}.svg")

    if show_plot:
        plt.show()
