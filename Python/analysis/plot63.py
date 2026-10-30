import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

from plot_style import plot, matplot_styles
from line_finder import get_poly_fit

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.3"
save_location = (
    r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.3"
)
file_name = "phase_V_avg_63"
save_fig = False

files = os.listdir(folder)

info_data = ["Phase (°)", "Mean voltage (V)"]
title = "PC1 Mean voltage output vs phase difference between two signals"

x_min = 0
x_max = 360
y_min = 0
y_max = 5
unit_start = 0
unit_end = 361
unit_jump = 30

for csv in files:
    if csv[-3:] == "csv":
        matplot_styles(
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            unit_start=unit_start,
            unit_end=unit_end,
            unit_jump=unit_jump,
        )
        df = pd.read_csv(f"{folder}/{csv}")
        phase_data = df["Phase Data"].values * 360
        mean_voltage_data = df["Mean voltage data"].values
        plot(
            x=phase_data,
            y=mean_voltage_data,
            names=info_data,
            title=title,
            file_name=file_name,
            save_location=save_location,
            save=save_fig,
        )