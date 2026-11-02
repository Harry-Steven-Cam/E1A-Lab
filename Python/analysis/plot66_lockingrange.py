
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

PC =1

folder = rf"./data/6.6/PC{PC}/RCvary"
save_location = rf"./analysis_images/6.6/PC{PC}/RCvary"

save_data=False
show_plot=True

os.makedirs(save_location, exist_ok=True)

# Filename frequency range to select
freq_start = 10.0
freq_end = 30.0

# Locking conditions
ratio_tolerance = 0.05       # Ratio must be within 1 of unity (%)
max_phase_span = 30          # Maximum phase variation in degrees
phase_window = 7             # Number of samples in rolling window
min_phase_samples = 5        # Minimum valid samples in window

min_locked_points = 3


# --------------------------------------------------
# FIND CSV FILES WITH THE CORRECT FREQUENCY RANGE
# --------------------------------------------------

file_names = []

for f in os.listdir(folder):

    if f.lower().endswith(".csv"):

        filename = f.lower()

        if "f10.0(khz) to 30.0(khz)" in filename:
            file_names.append(f)

file_names = sorted(file_names)

print(f"Found {len(file_names)} files with frequency range 10-30 kHz")

if len(file_names) == 0:
    raise ValueError("No CSV files found with the specified frequency range.")


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_fc_hz(filename):

    params = parse_filename(filename)
    fc = params["fc"]

    if fc is None:
        return np.nan

    fc = str(fc).lower().strip()

    if fc.endswith("khz"):
        return float(fc[:-3]) * 1000

    elif fc.endswith("hz"):
        return float(fc[:-2])

    elif fc.endswith("k"):
        return float(fc[:-1]) * 1000

    else:
        return float(fc)


def unwrap_phase(phase):

    """
    Unwrap phase separately for each continuous group of
    valid measurements, avoiding NaNs spreading through
    the entire phase array.
    """

    phase = np.asarray(phase, dtype=float)

    unwrapped = np.full(len(phase), np.nan)

    valid_indices = np.where(np.isfinite(phase))[0]

    if len(valid_indices) == 0:
        return unwrapped

    # Find separate continuous groups of valid measurements
    breaks = np.where(np.diff(valid_indices) > 1)[0] + 1

    groups = np.split(valid_indices, breaks)

    for group in groups:

        unwrapped[group] = np.rad2deg(
            np.unwrap(np.deg2rad(phase[group]))
        )

    return unwrapped


def find_longest_lock(locked, freq):

    """
    Finds the longest continuous region where both the
    frequency ratio and phase conditions are satisfied.
    """

    indices = np.where(locked)[0]

    if len(indices) == 0:
        return None

    # Split into continuous groups
    breaks = np.where(np.diff(indices) > 1)[0] + 1

    groups = np.split(indices, breaks)

    # Find group with largest frequency span
    longest = max(
        groups,
        key=lambda x: freq[x[-1]] - freq[x[0]]
    )

    if len(longest) < min_locked_points:
        return None

    return longest[0], longest[-1], len(longest)


# --------------------------------------------------
# ANALYSE EACH CSV FILE
# --------------------------------------------------

matplot_styles()

results = []

for csv in file_names:

    print(f"\nAnalysing: {csv}")

    # Read CSV
    tmp_path = os.path.join(folder, csv)
    df = pd.read_csv(tmp_path)

    # Extract data (all frequencies in kHz)
    time = df["time"].values
    awg_freq = df["awg_freq"].values
    vco_freq = df["vco_freq"].values
    phase_diff = df["phase_diff"].values

    # Calculate or extract ratio
    if "ratio" in df.columns:
        ratio = df["ratio"].values
    else:
        ratio = awg_freq / vco_freq

    # Extract cutoff frequency
    fc = get_fc_hz(csv)
    # Remove invalid frequency and ratio values
    valid = (
        np.isfinite(awg_freq) &
        np.isfinite(ratio)
    )

    time = time[valid]
    awg_freq = awg_freq[valid]
    ratio = ratio[valid]
    phase_diff = phase_diff[valid]

    # Sort by time (sweep order)
    order = np.argsort(time)

    time = time[order]
    awg_freq = awg_freq[order]
    ratio = ratio[order]
    phase_diff = phase_diff[order]

    # --------------------------------------------------
    # CONDITION 1: FREQUENCY RATIO CLOSE TO UNITY
    # --------------------------------------------------

    ratio_locked = (
        np.abs(ratio - 1.0) <= ratio_tolerance
    )

    # --------------------------------------------------
    # CONDITION 2: PHASE DIFFERENCE REMAINS BOUNDED
    # --------------------------------------------------

    phase_unwrapped = unwrap_phase(phase_diff)

    # Calculate rolling phase range
    phase_series = pd.Series(phase_unwrapped)

    phase_max = phase_series.rolling(
        window=phase_window,
        center=True,
        min_periods=min_phase_samples
    ).max()

    phase_min = phase_series.rolling(
        window=phase_window,
        center=True,
        min_periods=min_phase_samples
    ).min()

    phase_span = (phase_max - phase_min).to_numpy()

    phase_locked = (
        np.isfinite(phase_span) &
        (phase_span <= max_phase_span)
    )

    # Both conditions must be satisfied
    locked = ratio_locked & phase_locked

    # Percentage of ratio-unity points that pass phase test
    n_ratio = np.sum(ratio_locked)

    if n_ratio > 0:
        lock_percentage = 100 * np.sum(locked) / n_ratio
    else:
        lock_percentage = 0

    # --------------------------------------------------
    # FIND CONTINUOUS LOCKING REGION
    # --------------------------------------------------

    run = find_longest_lock(locked, awg_freq)

    if run is None:

        lock_start = np.nan
        lock_end = np.nan
        locking_range = 0
        n_locked = 0

        print(
            "No continuous locking region found. "
            f"Ratio-unity points: {n_ratio}, "
            f"phase-stable percentage: {lock_percentage:.1f}%"
        )

    else:

        start, end, n_locked = run

        lock_start = awg_freq[start]
        lock_end = awg_freq[end]

        locking_range = lock_end - lock_start

        print(f"fc = {fc:.3f} kHz")
        print(f"Locking start = {lock_start:.3f} kHz")
        print(f"Locking end = {lock_end:.3f} kHz")
        print(f"Locking range = {locking_range:.3f} kHz")
        print(f"Locked points = {n_locked}")

    print(f"Percentage passing phase test = {lock_percentage:.1f}%")

    # Store results
    results.append({

        "filename": csv,
        "fc (Hz)": fc,
        "locking_start (kHz)": lock_start,
        "locking_end (kHz)": lock_end,
        "locking_range (kHz)": locking_range,
        "locked_points": n_locked,
        "ratio_unity_points": n_ratio,
        "phase_locked_percentage": lock_percentage

    })


# --------------------------------------------------
# SAVE RESULTS TO CSV
# --------------------------------------------------

results_df = pd.DataFrame(results)
# Display results in the console instead of saving a CSV


# --------------------------------------------------
# PLOT LOCKING RANGE AGAINST FC
# --------------------------------------------------

plot_df = results_df.dropna(
    subset=["fc (Hz)"]
).copy()

# Remove zero or negative fc values (ln is undefined)
plot_df = plot_df[plot_df["fc (Hz)"] > 0]

plot_df = plot_df.sort_values("fc (Hz)")

if len(plot_df) > 0:

    plot_data(
        np.log(plot_df["fc (Hz)"].values),
        plot_df["locking_range (kHz)"].values,
        names=[
            r"$\ln(f_c/\mathrm{Hz})$",
            "Locking range (kHz)"
        ],
        title="Locking range against ln(fc)",
        save_location=save_location,
        file_name="locking_range_vs_ln_fc",
        save=save_data,
        show_plot=show_plot,
        marker="x",
        linestyle="none"
    )

else:
    print("No valid fc values found for plotting.")
