import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import scipy
import time as t


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

picoscope.scope_prepare(
    capture_time=0.5,  # Traces will be captured over this time period (in seconds).
    samples=5_000,  # Number of samples to capture over the capture_time period.
    a_range=10,  # Voltage range for channel A (in volts).
    a_probe="x1",  # Probe attenuation for channel A (x1 is the default).
    b_range=10,
    c_range=10,
    d_range=10,
    a_name="SIG_IN",  # Useful channel names for exported data and/or plot legend.
    b_name="COMP",
    c_name="Trig",
    d_name="PC",
    trigger_channel="C",
    trigger_direction="r",
    trigger_level=2, 
    trigger_pre_percent=25,
    verbose=False,
    trigger_timeout=0,
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
    picoscope.awg(
        waveform="dc",
        offset=0,
    )


def plot(x, y, name, xname, yname, save=False, show=True,label=None):
    plot_styles = {"marker": "x", "linestyle": "none"}
    plt.plot(x, y,label=label)
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.legend()
    plt.grid(True)
    os.makedirs("./images", exist_ok=True)
    if save == True:
        plt.savefig(f"./images/{name}.png")
    if show == True:
        plt.show()

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

freq = 18_000 

awg_idle()
t.sleep(0.5)
print('setting freq')
set_awg(freq)
time, volts = picoscope.scope_capture()
time = np.asarray(time)
awg_out = np.asarray(volts[2])
pll_out = np.asarray(volts[3]) #pll output

awg_idle()



name = f"Turn_on_PC1_R1={R1}_R2={R2}_C={C}_f{freq/1000}(kHz)_R3={R3}_C2={C2}_fc={fc}(Hz)"
plot(time,awg_out,name,'time','voltage',label='awg_out',show=False)  # voltage vs time for A and B
plot(time,pll_out,name,'time','voltage',label='pll_out',show=False)  # voltage vs time for A and B
plt.show()
#data_save(name+"_A", time, "time", awg_out, "A_SIG_IN", pll_out, "B_COMP")


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)