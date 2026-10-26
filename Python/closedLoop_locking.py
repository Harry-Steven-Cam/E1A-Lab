import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import scipy
import winsound
import threading
import time as t

winsound.Beep(1500, 1000)
t.sleep(0.01)
winsound.Beep(1500, 1000)
t.sleep(0.01)
winsound.Beep(1500, 1250)

R1 = '100K'#str(input('R1 (k): ')+'K')
R2 = '100K'#str(input('R2 (k): ')+'K')
C = '100pF'#str(input('C: '))

R3='15K'#RC filter
C2='100nF'#RC filter
R3_ = 15e3
C2_ = 100e-9
fc=1/(np.pi*2*R3_*C2_)


def data_save(name, x, xname, y, yname, z, zname):
    # Writes two columns (x, y) with a header row to ./data/<name>.csv
    file_path = f"./data/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname, zname])
        writer.writerows(zip(x, y, z))

    print(f"Data saved to: {os.path.abspath(file_path)}")


picoscope.picoscope_open()
time =0.005
samplerate = 1e8
picoscope.scope_prepare(
    capture_time=time,  # Traces will be captured over this time period (in seconds).
    samples=time*samplerate,  # Number of samples to capture over the capture_time period.
    a_range=10,  # Voltage range for channel A (in volts).
    a_probe="x1",  # Probe attenuation for channel A (x1 is the default).
    b_range=10,
    c_range=10,
    d_range=10,
    a_name="SIG_IN",  # Useful channel names for exported data and/or plot legend.
    b_name="COMP",
    c_name="Trig",
    d_name="PC",
    trigger_channel="A",  # CHANGED: trigger on the AWG signal itself so the window starts at turn-on
    trigger_direction="r",  # CHANGED: rising edge (idle -1 V -> upper square level -0.5 V)
    trigger_level=-0.75,  # CHANGED: midway between the idle level and the upper square level
    trigger_pre_percent=25,  # CHANGED: keep 10% pre-trigger so the turn-on edge is inside the window
    verbose=False,
    trigger_timeout=1000,
)


def set_awg(freq):
    # Turns the AWG on as a 1 Vpp square wave at freq (Hz), offset -1 V
    picoscope.awg(
        waveform="square",
        frequency=freq,
        peak_to_peak=1,
        offset=-1,
    )
    #print("awg set")

def awg_idle():
    #turns off the awg (CHANGE OFFSET???????)
    picoscope.awg(
        waveform="square",
        frequency=1000,
        peak_to_peak=0,
        offset=-1,
    )


def save_scope(name,time,a,b):

    plt.plot(time, a, label="A (SIG_IN)")
    plt.plot(time, b, label="B (COMP)")
    plt.xlabel("time (s)")
    plt.ylabel("Voltage (V)")
    plt.legend()
    plt.grid(True)
    os.makedirs("./images", exist_ok=True)
    plt.savefig(f"./images/{name}.png")

def freqFinder(voltage,time):
    # Estimates frequency (kHz) from the mean spacing of mid-level rising edges (trimmed mean)
    threshold = (np.max(voltage) + np.min(voltage)) / 2
    peaktopeak = (np.max(voltage) - np.min(voltage))
    edges = np.where((voltage[:-1] < threshold) & (voltage[1:] >= threshold))[0]

    if len(edges) >= 2:# and peaktopeak>.8:
        edge_times = time[edges]
        periods = np.diff(edge_times)
        # Ignore invalid periods
        periods = periods[periods > 0]
        if len(periods) > 0:
            period = scipy.stats.trim_mean(periods, proportiontocut=0.1)
            freq = 1.0 / period
        else:
            freq = 0
            #print("Invalid periods")
    else:
        freq = 0
        #print("Not enough rising edges detected")
    return freq/1000

#picoscope.scope_monitor()
print("running")

freq = 148_000 

awg_idle()
t.sleep(0.1)
set_awg(freq)
time, volts = picoscope.scope_capture()
time = np.asarray(time)
awg_out = np.asarray(volts[0])
vco_out = np.asarray(volts[1]) #pll output

awg_idle()

winsound.Beep(2500, 500)
#t.sleep(0.001)
winsound.Beep(2500, 500)

name = f"Turn_on_PC1_R1={R1}_R2={R2}_C={C}_f{freq/1000}(kHz)_R3={R3}_C2={C2}_fc={fc}(Hz)"
save_scope(name, time, awg_out, vco_out)  # voltage vs time for A and B
plt.show()
data_save(name+"_A", time, "time", awg_out, "A_SIG_IN", vco_out, "B_COMP")


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)