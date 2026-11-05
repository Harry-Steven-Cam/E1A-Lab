import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

PC = 1
save_data = False
show_plot = True
folder = rf"./data/7/PC{PC}"
save_location = rf"./analysis_images/7/display/PC{PC}"

file_names = sorted([f for f in os.listdir(folder) if f.lower().endswith(".csv")])

os.makedirs(save_location, exist_ok=True)

#ignore_data = ["f0.0(kHz)", "30.0(kHz)", "60.0(kHz)", "240.0(kHz)"]
ignore_data = []


print("running")
for csv in file_names:
    # Read CSV
    if any(file in csv for file in ignore_data):
        continue
    # Read CSV
    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    # Extract data
    time = df["time"].values
    awg_out = df["awg_out"].values
    pll_out = df["pll_out"].values
    x_fit=np.linspace(min(time),max(time),200)
    plt.plot(x_fit,np.sin(x_fit))
    title = None
    x=time
    y=pll_out

    save_name = f"transient_response.svg"
    # Generate 2x2 figure using your existing function
    plot_data(
        x,
        y,
        names=["Time (s)", "Voltage (V)"],
        title=title,
        save_location=save_location,
        file_name=save_name,
        save=save_data,
        show_plot=show_plot,
        alpha=1,
        linestyle="--",
        marker="none",
        ylim=(0,5)
    )
