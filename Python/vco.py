import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import scipy
import winsound
import time as t

#winsound.Beep(2500, 1000)

R1 = '100K' #str(input('R1 (k): ')+'K')
R2 = '100K' #str(input('R2 (k): ')+'K')
C = '1000pF' #str(input('C: '))

def data_save(name, x, xname, y, yname):
    file_path = f"./data/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname])
        writer.writerows(zip(x, y))

    print(f"Data saved to: {os.path.abspath(file_path)}")


picoscope.picoscope_open()
time =0.05
samplerate = 1e9
picoscope.scope_prepare(
    capture_time=0.5,  # Traces will be captured over this time period (in seconds).
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


def set_awg(voltage: float):
    picoscope.awg(
        waveform="dc",
        peak_to_peak=0,
        offset=-voltage,
    )
    #print("awg set")

def save_scope(voltage,time,volts):
    plt.plot(time, volts)
    plt.xlabel("time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    os.makedirs("./images", exist_ok=True)
    plt.savefig(f"./images/{voltage}.png")
    plt.clf()

#picoscope.scope_monitor()
print("running")

frequency = []
steps = 50
voltagesAWG = np.linspace(0, 1.88, steps)
voltage_data=[]

for voltage in voltagesAWG:
    set_awg(voltage)
    time, volts = picoscope.scope_capture()
    voltage_data.append(np.mean(volts[0]))
    time = np.asarray(time)
    signal = np.asarray(volts[1])
    print(f'{np.round((voltage/1.88)*100,0)}% complete')
    '''
    print("Voltage:", voltage)
    print("Signal min/max:", np.min(signal), np.max(signal))
    print("Time range:", time[0], time[-1])
    print("Sample interval:", np.mean(np.diff(time)))
    '''
    # Find rising edges
    threshold = (np.max(signal) + np.min(signal)) / 2
    peaktopeak = (np.max(signal) - np.min(signal))
    edges = np.where((signal[:-1] < threshold) & (signal[1:] >= threshold))[0]

    if len(edges) >= 2  and peaktopeak>.8:
        edge_times = time[edges]
        periods = np.diff(edge_times)
        # Ignore invalid periods
        periods = periods[periods > 0]
        if len(periods) > 0:
            period = scipy.stats.trim_mean(periods, proportiontocut=0.2)
            freq = 1.0 / period
            '''
            print("Edges:", len(edges))
            print("Period:", period, "s")
            print("Frequency:", freq, "Hz")
            '''
        else:
            freq = 0
            #print("Invalid periods")
    else:
        freq = 0
        #print("Not enough rising edges detected")
    frequency.append(freq/1000)
    #print(peaktopeak)

#print("Final frequencies:", frequency)
winsound.Beep(2500, 500)
t.sleep(0.005)
winsound.Beep(2500, 500)

plt.plot(voltage_data, frequency, "x", linestyle="none")
plt.ylabel("Frequency (KHz)")
plt.xlabel("Voltage (V)")
plt.xlim(left=0)
#plt.ylim(bottom=0)
plt.grid(True)
os.makedirs("./images", exist_ok=True)
plt.savefig(f"./images/R1={R1}_R2={R2}_C={C}.png")
plt.show()
data_save(f"R1={R1}_R2={R2}_C={C}", frequency, "Frequency", voltage_data, "Voltage data")


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)