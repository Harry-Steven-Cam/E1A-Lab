import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

# Settings
PC = 2
save_data = True
show_plot = True
threshold = 0.02
folder = rf"./data/6.6/PC{PC}/RCvary"
save_location = rf"./analysis_images/6.6/PC{PC}/RCvary"

file_names = sorted([f for f in os.listdir(folder) if f.lower().endswith(".csv")])

os.makedirs(save_location, exist_ok=True)

print("Running ratio analysis...")

# Store results
fc_values = []
percentage_values = []
frequency_ranges = []

# Ratio limits
ratio_base = 1
ratio_min = ratio_base - threshold
ratio_max = ratio_base + threshold

# AWG frequency limits (kHz)
freq_min, freq_max = 10, 30
ignore_range = ["60.0(kHz)", "120.0(kHz)", "240.0(kHz)"]

# for 7th harmonic
#freq_min,freq_max = 40,60
#ignore_range = ["30.0(kHz)"]

for csv in file_names:

    # Read CSV
    if any(file in csv for file in ignore_range):
        continue
    # Read CSV
    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    # Extract data
    awg_freq = df["awg_freq"].values
    vco_freq = df["vco_freq"].values

    if "ratio" in df.columns:
        ratio = df["ratio"].values
    else:
        ratio = awg_freq / vco_freq

    # Extract fc from filename
    params = parse_filename(csv)
    fc = params["fc"]

    if fc is None:
        print(f"Skipping {csv}: no fc found")
        continue

    fc_value = data_to_val(fc)

    # --------------------------------
    # Filter data to 10-30 kHz only
    # --------------------------------
    freq_mask = (awg_freq >= freq_min) & (awg_freq <= freq_max)

    filtered_freq = awg_freq[freq_mask]
    filtered_ratio = ratio[freq_mask]

    # Total number of datapoints in 10-30 kHz
    total_points = len(filtered_ratio)

    if total_points == 0:
        print(f"Skipping {csv}: no data between 10 and 30 kHz")
        continue

    # --------------------------------
    # Find points where ratio is 1 +/- 5%
    # --------------------------------
    in_band = (filtered_ratio >= ratio_min) & (filtered_ratio <= ratio_max)

    number_in_band = np.count_nonzero(in_band)

    # Calculate percentage
    percentage = (number_in_band / total_points) * 100

    # --------------------------------
    # Calculate frequency range
    # --------------------------------
    if number_in_band > 0:
        frequency_range = np.max(filtered_freq[in_band]) - np.min(filtered_freq[in_band])
    else:
        frequency_range = np.nan

    # Store results
    fc_values.append(fc_value)
    percentage_values.append(percentage)
    frequency_ranges.append(frequency_range)


# Convert to numpy arrays
fc_values = np.array(fc_values, dtype=float)
percentage_values = np.array(percentage_values, dtype=float)
frequency_ranges = np.array(frequency_ranges, dtype=float)

# Sort results by fc
sort_indices = np.argsort(fc_values)

fc_values = fc_values[sort_indices]
percentage_values = percentage_values[sort_indices]
frequency_ranges = frequency_ranges[sort_indices]


# --------------------------------
# Plot results side by side
# --------------------------------

matplot_styles()

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Graph 1: Percentage of points within ratio band
axes[0].plot(fc_values, percentage_values, marker="x", linestyle="none")

axes[0].set_xlabel(r"$f_c$ (Hz)")
axes[0].set_ylabel(rf"Datapoints with ${ratio_min} \leq R \leq {ratio_max}$ (%)")
axes[0].set_title("Percentage of points within ratio band")
axes[0].set_ylim(0, 100)


# Graph 2: Frequency range of points within ratio band
axes[1].plot(fc_values, frequency_ranges, marker="x", linestyle="none")

axes[1].set_xlabel(r"$f_c$ (Hz)")
axes[1].set_ylabel("AWG frequency lock range (kHz)")
axes[1].set_title("Frequency range within ratio band")


# Overall title
fig.suptitle(rf"PC{PC}: Analysing locking, " rf"$f_{{AWG}}$ = {freq_min} to {freq_max} kHz")

plt.tight_layout()

# Save figure
if False:
    file_path = os.path.join(save_location, f"ratio_band_summary_PC{PC}.svg")
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    print(f"Saved figure to {file_path}")

# Show figure
if show_plot:
    plt.show()
else:
    plt.close()

# --------------------------------
# Second figure: ln(fc) on x-axis
# --------------------------------

ln_fc = np.log(fc_values)

matplot_styles()

fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))

# Graph 1: Percentage within ratio band
axes2[0].plot(ln_fc, percentage_values, marker="x", linestyle="none")

axes2[0].set_xlabel(r"$\ln(f_c / \mathrm{Hz})$")
axes2[0].set_ylabel(rf"Datapoints with ${ratio_min} \leq R \leq {ratio_max}$ (%)")
axes2[0].set_title("Percentage of points within ratio band")
axes2[0].set_ylim(0, 100)


# Graph 2: Frequency range within ratio band
axes2[1].plot(ln_fc, frequency_ranges, marker="x", linestyle="none")

axes2[1].set_xlabel(r"$\ln(f_c / \mathrm{Hz})$")
axes2[1].set_ylabel("AWG frequency lock range (kHz)")
axes2[1].set_title("Frequency range within ratio band")
axes2[1].set_ylim(0,12)


# Overall title
fig2.suptitle(
    rf"PC{PC}: Analysing locking with various RC filters "
    + "\n"
    + rf"$f_{{AWG}}$ = {freq_min} to {freq_max} kHz"
    + "\n"
    + f" Analysis of the {'1st harmonic' if ratio_base == 1 else f"{ratio_base}th harmonic"}"
)

plt.tight_layout()

# Save figure separately
if save_data:
    file_path = os.path.join(save_location, f"ratio_band_vs_noise_PC{PC}_ratio={ratio_base}.svg")
    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    print(f"Saved figure to {file_path}")

# Show figure
if show_plot:
    plt.show()
else:
    plt.close()

print("Completed ln(fc) plots")

print("Completed")
