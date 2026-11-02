import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

# Folder containing CSV files
PC=1
save_data=False
show_plot=True
folder = rf"./data/6.6/PC{PC}/RCvary"
file_names = sorted([f for f in os.listdir(folder) if f.lower().endswith(".csv")])
save_location=rf"./analysis_images/6.6/PC{PC}/RCvary"

for csv in file_names:

    # Read CSV
    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    # Extract data
    awg_freq = df["awg_freq"].values
    vco_freq = df["vco_freq"].values
    phase_diff = df["phase_diff"].values
    vco_in_val = df["vco_in_val"].values

    # Calculate or extract ratio
    if "ratio" in df.columns:
        ratio = df["ratio"].values
    else:
        ratio = awg_freq / vco_freq
    params = parse_filename(csv)
    r1 = params["r1"] or "N/A"
    r2 = params["r2"] or "N/A"
    c = params["c"] or "N/A"
    fc = params["fc"] or "N/A"
    title = (
        rf"$R_{{1}}$={format_val(r1)}, $R_{{2}}$={format_val(r2) }, "
        rf"C={format_val(c)}, $f_{{c}}$={format_sci(data_to_val(fc))}Hz"
    )
    # Create 2x2 figure
    x = [awg_freq, awg_freq, awg_freq, awg_freq]

    y = [ratio, phase_diff, vco_in_val, vco_freq]

    # Individual axis labels
    names = [
        ["AWG frequency (kHz)", "Ratio"],
        ["AWG frequency (kHz)", "Phase difference (°)"],
        ["AWG frequency (kHz)", "VCO input voltage (V)"],
        ["AWG frequency (kHz)", "VCO frequency (kHz)"],
    ]
    save_name=f"fc={fc},{min(awg_freq)}to{max(awg_freq)}"
    # Generate 2x2 figure using your existing function
    plot_2x2(x, y, names=names, title=title, file_name=save_name,save_location=save_location, save=save_data, show_plot=show_plot)
