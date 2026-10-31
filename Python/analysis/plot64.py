import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib as mpl

from plot_style import *
from line_finder import *

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.4"
save_location = (
    r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.4"
)
file_name = "phase_V_avg_64"

save_fig = True

files = os.listdir(folder)
info_data = ["Phase (°)", "Mean voltage (V)"]
title = "PC2 mean voltage output vs\nphase difference between input signals"

x_min = 0
x_max = 360
y_min = 0
y_max = 5
unit_start = 0
unit_end = 361
unit_jump = 60

for csv in files:
    if csv[-3:] == "csv":
        # ---------------------- setting styles and axis -----------------------------
        matplot_styles(
            unit_start=unit_start,
            unit_end=unit_end,
            unit_jump=unit_jump,
        )
        # ---------------------- reading data -----------------------------
        df = pd.read_csv(f"{folder}/{csv}")
        phase_data = df["Phase Data"].values * 360
        mean_voltage_data = df["Mean voltage data"].values
        # ---------------------- plotting errors and best fits -----------------------------
        mean_voltage_error = get_voltage_errors(mean_voltage_data, voltage_window=10)
        x_fit, y_fit, m, c, error = get_poly_fit(
            phase_data[0 : len(phase_data) // 2],
            mean_voltage_data[0 : len(mean_voltage_data) // 2],
            1,
            error_data=mean_voltage_error[0 : len(phase_data) // 2],
        )
        x_fit2, y_fit2, m2, c2, error2 = get_poly_fit(
            phase_data[len(phase_data) // 2 :],
            mean_voltage_data[len(mean_voltage_data) // 2 :],
            1,
            error_data=mean_voltage_error[len(phase_data) // 2 :],
        )
        plt.errorbar(
            phase_data,
            mean_voltage_data,
            yerr=mean_voltage_error,
            linestyle="none",
            ecolor="black",
            capsize=3,
        )
        plt.plot(x_fit, y_fit, color=colours[3], alpha=0.6)
        plt.plot(x_fit2, y_fit2, color=colours[3], alpha=0.6)
        # ---------------------- text results -----------------------------
        plt.text(
            5,
            -1.5,
            rf"$m_{{1}}$ = ({m : .5g}±{format_sci(error[0],1)}) V/°",
            fontsize=8,
        )
        plt.text(
            5,
            -2,
            rf"$m_{{2}}$ = ({m2 : .4g}±{format_sci(error2[0],1)}) V/° ",
            fontsize=8,
        )
        plt.text(
            5,
            -2.5,
            rf"$K_{{D_ PC2}}$=({(m+m2)*180/(2*np.pi) : .6g}±{format_sci(error[0]/np.sqrt(2),0)}) V/rad",
            fontsize=8,
        )
        plt.text(
            5,
            -3,
            rf"$V_{{Start}}$={mean_voltage_data[0]: .3g}V, $V_{{End}}$={mean_voltage_data[-1]: .3g}V",
            fontsize=8,
        )
        # ---------------------- plotting data -----------------------------
        plot_data(
            x=phase_data,
            y=mean_voltage_data,
            names=info_data,
            title=title,
            file_name=file_name,
            save_location=save_location,
            save=save_fig,
            show_plot=False,
        )
        # ---------------------- Graph stuff -----------------------------
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        if save_fig:
            os.makedirs(save_location, exist_ok=True)
            plt.savefig(f"{save_location}/{file_name}.svg")
        plt.show()
