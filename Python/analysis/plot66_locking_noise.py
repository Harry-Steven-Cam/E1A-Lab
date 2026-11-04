import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

# Settings
PC = 1
save_data = True
show_plot = True
threshold = 0.02
ratio_base = 7 # 7 for pc1 harmonic
square_wave_voltage_amplitude = 600
linear_snr=False
folder = rf"./data/6.6/PC{PC}/Noise"
save_location = rf"./analysis_images/6.6/PC{PC}/Noise"

file_names = sorted([f for f in os.listdir(folder) if f.lower().endswith(".csv")])

os.makedirs(save_location, exist_ok=True)

print("Running noise analysis...")

# Store results
noise_values = []
fc_values = []
percentage_values = []
frequency_ranges = []

# Ratio limits

#7 for high harmonic on pc1
# Ratio limits
ratio_min = ratio_base - threshold
ratio_max = ratio_base + threshold

# AWG frequency limits (kHz)
#freq_min,freq_max = 10,30
#ignore_range = ["60.0(kHz)","120.0(kHz)","240.0(kHz)"]

#for 7th harmonic
freq_min,freq_max = 100,120
ignore_range = ["f0.0(kHz)","30.0(kHz)","60.0(kHz)","240.0(kHz)"]

for csv in file_names:

    # Read CSV
    if any(file in csv for file in ignore_range):
        continue
    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    # --------------------------------
    # Extract noise and fc from filename
    # --------------------------------

    try:
        noise_str = csv.split("noise=")[1].split("_")[0]
        noise_value = float(noise_str.replace("mV", ""))

        fc_str = csv.split("fc=")[1].split("Hz")[0]
        fc_value = float(fc_str)

    except (IndexError, ValueError):
        print(f"Skipping {csv}: could not extract noise or fc")
        continue

    # --------------------------------
    # Extract data
    # --------------------------------

    awg_freq = df["awg_freq"].values
    vco_freq = df["vco_freq"].values

    if "ratio" in df.columns:
        ratio = df["ratio"].values
    else:
        ratio = awg_freq / vco_freq

    # --------------------------------
    # Filter to 10-30 kHz
    # --------------------------------

    freq_mask = (
        (awg_freq >= freq_min) & (awg_freq <= freq_max) & np.isfinite(awg_freq) & np.isfinite(ratio)
    )

    filtered_freq = awg_freq[freq_mask]
    filtered_ratio = ratio[freq_mask]

    total_points = len(filtered_ratio)

    if total_points == 0:
        print(f"Skipping {csv}: no valid data between 10 and 30 kHz")
        continue

    # --------------------------------
    # Find points where ratio = 1 +/- 5%
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

    # --------------------------------
    # Store results
    # --------------------------------

    noise_values.append(noise_value)
    fc_values.append(fc_value)
    percentage_values.append(percentage)
    frequency_ranges.append(frequency_range)


# Convert to numpy arrays
noise_values = np.array(noise_values, dtype=float)
fc_values = np.array(fc_values, dtype=float)
percentage_values = np.array(percentage_values, dtype=float)
frequency_ranges = np.array(frequency_ranges, dtype=float)


# --------------------------------
# Get unique fc values
# --------------------------------

unique_fc = np.unique(fc_values)

fc_title = ", ".join([f"{format_sci(fc)} Hz" for fc in unique_fc])


# --------------------------------
# Plot results against noise
# --------------------------------

matplot_styles()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

for fc in unique_fc:

    # Select data for this fc
    fc_mask = fc_values == fc

    noise = noise_values[fc_mask]
    percentage = percentage_values[fc_mask]
    freq_range = frequency_ranges[fc_mask]

    # Sort by noise
    sort_indices = np.argsort(noise)
    if linear_snr:
        noise = square_wave_voltage_amplitude/noise[sort_indices]
    else:
        noise = 20*np.log10(square_wave_voltage_amplitude/noise[sort_indices])
    percentage = percentage[sort_indices]
    freq_range = freq_range[sort_indices]

    # Graph 1: Percentage within ratio band
    axes[0].plot(noise, percentage, marker="x", linestyle="none")

    # Graph 2: Frequency range within ratio band
    axes[1].plot(noise, freq_range, marker="x", linestyle="none")


# --------------------------------
# Format first graph
# --------------------------------

if linear_snr:
    axes[0].set_xlabel("Linear SNR")
else:
    axes[0].set_xlabel(rf"$SNR_{{dB}}$")
axes[0].set_ylabel(rf"Datapoints with ${ratio_min} \leq R \leq {ratio_max}$ (%)")
axes[0].set_title("Percentage within ratio band")
axes[0].set_ylim(0, 60)
axes[0].grid(True)
axes[0].legend()


# --------------------------------
# Format second graph
# --------------------------------
if linear_snr:
    axes[1].set_xlabel("Linear SNR")
else:
    axes[1].set_xlabel(rf"$SNR_{{dB}}$")

axes[1].set_ylabel("AWG frequency range (kHz)")
axes[1].set_title("Frequency range within ratio band")
axes[1].set_ylim(0)
axes[1].grid(True)
axes[1].legend()


# --------------------------------
# Overall title
# --------------------------------

fig.suptitle(rf"PC{PC}: $f_c$ = {fc_title}" + "\n" + rf"$f_{{AWG}}$ = {freq_min} to {freq_max} kHz" + "\n"+ f" Analysis of the {'1st harmonic' if ratio_base == 1 else f"{ratio_base}th harmonic"}")

plt.tight_layout()

# Save figure
if save_data:
    file_path = os.path.join(save_location, f"ratio_band_vs_noise_PC{PC}_ratio={ratio_base}_{'linear' if linear_snr else '20logsnr'}.svg")

    plt.savefig(file_path, dpi=300, bbox_inches="tight")
    print(f"Saved figure to {file_path}")

# Show figure
if show_plot:
    plt.show()
else:
    plt.close()


print("Completed noise analysis")
