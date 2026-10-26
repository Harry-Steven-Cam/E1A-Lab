import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import scipy
import time as t

R1 = "100K"  # str(input('R1 (k): ')+'K')
R2 = "100K"  # str(input('R2 (k): ')+'K')
C = "1000pF"  # str(input('C: '))

PC = 2
R3 = 15_000
C2 = 0.01e-6
fc = f"{(1 / (np.pi * 2 * R3 * C2)):.3g}"
noise=0


def data_save(name, data, data_name):
    file_path = f"./data/6.6/PC{PC}/Noise/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data_name)
        writer.writerows(zip(data))

    print(f"Data saved to: {os.path.abspath(file_path)}")


picoscope.picoscope_open()

picoscope.scope_prepare(
    capture_time=0.05,  # Traces will be captured over this time period (in seconds).
    samples=50_000,  # Number of samples to capture over the capture_time period.
    a_range=10,  # Voltage range for channel A (in volts).
    a_probe="x1",  # Probe attenuation for channel A (x1 is the default).
    b_range=10,
    c_range=10,
    d_range=10,
    a_name="SIG_IN",  # Useful channel names for exported data and/or plot legend.
    b_name="COMP",
    c_name="Trig",
    d_name="PC",
    trigger_channel="B",
    trigger_direction="f",
    trigger_level=2.5,
    trigger_pre_percent=0,
    verbose=False,
    trigger_timeout=1000,
)


def set_awg(freq):
    picoscope.awg(
        waveform="square",
        frequency=freq,
        peak_to_peak=0.6,
        offset=-0.6,#TMPPPPP
    )
    # print("awg set")


def plot(x, y, name, xname, yname, save, show=True):
    plot_styles = {"marker": "x", "linestyle": "none"}
    plt.plot(x, y, **plot_styles)
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.grid(True)
    os.makedirs("./images", exist_ok=True)
    if save == True:
        plt.savefig(f"./images/6.6/PC{PC}/Noise/{name}.png")
    if show == True:
        plt.show()
    plt.clf()

def plot_all(x, ys, names, xname, ynames, saves):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    os.makedirs("./images", exist_ok=True)

    for ax, y, name, yname, save in zip(axes, ys, names, ynames, saves):
        ax.plot(x, y, marker="x", linestyle="none")
        ax.set_xlabel(xname)
        ax.set_ylabel(yname)
        ax.grid(True)

        if save:
            fig_tmp = ax.get_figure()
            # Save the individual plot if requested

    plt.savefig(f"./images/6.6/PC{PC}/Noise/{name}.png")
    plt.tight_layout()
    plt.show()
    plt.close()




def phaseFinder(awg_out, vco_out, time, freq):
    def rising_edges(signal):
        threshold = (np.max(signal) + np.min(signal)) / 2
        edges = np.where((signal[:-1] < threshold) & (signal[1:] >= threshold))[0]

        # Interpolate the threshold crossing time
        t_edges = time[edges] + (
            (threshold - signal[edges]) / (signal[edges + 1] - signal[edges])
        ) * (time[edges + 1] - time[edges])

        return t_edges

    awg_edges = rising_edges(awg_out)
    vco_edges = rising_edges(vco_out)

    n = min(len(awg_edges), len(vco_edges))

    if n == 0 or freq <= 0:
        return np.nan

    # Calculate time differences between corresponding rising edges
    delays = vco_edges[:n] - awg_edges[:n]

    # Wrap delays into [-T/2, T/2), where T is the signal period
    period = 1 / freq
    delays = (delays + period / 2) % period - period / 2

    # Average the delays
    delay = np.mean(delays)

    # Convert delay to phase in degrees and wrap into [-180, 180)
    phase = (delay * freq * 360 + 180) % 360 - 180

    return phase


def freqFinder(voltage, time):
    threshold = (np.max(voltage) + np.min(voltage)) / 2
    peaktopeak = np.max(voltage) - np.min(voltage)
    edges = np.where((voltage[:-1] < threshold) & (voltage[1:] >= threshold))[0]

    if len(edges) >= 2:  # and peaktopeak>.8:
        edge_times = time[edges]
        periods = np.diff(edge_times)
        # Ignore invalid periods
        periods = periods[periods > 0]
        if len(periods) > 0:
            period = scipy.stats.trim_mean(periods, proportiontocut=0.1)
            freq = 1.0 / period
        else:
            freq = 0
            # print("Invalid periods")
    else:
        freq = 0
        # print("Not enough rising edges detected")
    return freq / 1000


# picoscope.scope_monitor()
print("running")

steps = 200
top_limit = 60_000
bottom_limit = 0  # 10_000
frequencies = np.linspace(bottom_limit, top_limit, steps)
awg_freq = []
vco_freq = []
phase_diff = []
vco_in_val = []

for freq in frequencies:
    set_awg(freq)
    time, volts = picoscope.scope_capture()
    time = np.asarray(time)
    awg_out = -np.asarray(volts[0])
    vco_out = np.asarray(volts[1])
    vco_in = np.asarray(volts[3])
    print(f"{np.round(((freq-bottom_limit)/(top_limit-bottom_limit))*100,0)}% complete")

    awg_freq.append(freq / 1000)
    vco_freq.append(freqFinder(vco_out, time))
    phase_diff.append(phaseFinder(awg_out, vco_out, time, freq))
    vco_in_val.append(np.mean(vco_in))


ratio = [awg_freq[i] / vco_freq[i] for i in range(len(awg_freq))]

PC = 2
R3 = 15_000
C2 = 0.01e-6
fc = f"{(1 / (np.pi * 2 * R3 * C2)):.3g}"
noise=000


def namer(data_type):
    return f"Closed_loop_noise={noise}mV_PC{PC}_{data_type}_R1={R1}_R2={R2}_C={C}_R3={R3/1000}K_C2={C2*1e9}nF_fc={fc}Hz_f{bottom_limit/1000}(kHz) to {top_limit/1000}(kHz)"



plot_all(
    awg_freq,
    [phase_diff, ratio, vco_freq, vco_in_val],
    [
        namer("phase_diff"),
        namer("ratio"),
        namer("fvf"),
        namer("vco_in"),
    ],
    "awg_freq",
    ["phase_diff", "ratio", "vco_freq", "vco_in_val"],
    [True, True, True, True],
)


save_data = True
if save_data:
    data_save(
        namer(f"all_data"),
        [time, awg_freq, vco_freq, ratio, phase_diff,vco_in_val],
        ["time", "awg_freq", "vco_freq", "ratio", "phase_diff","vco_in_val"],
    )


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)
print(fc)
