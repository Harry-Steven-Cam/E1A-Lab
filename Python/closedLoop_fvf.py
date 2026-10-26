import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import scipy
import winsound
import time as t

winsound.Beep(1500, 1000)
t.sleep(0.01)
winsound.Beep(1500, 1000)
t.sleep(0.01)
winsound.Beep(1500, 1250)

R1 = '100K'#str(input('R1 (k): ')+'K')
R2 = '100K'#str(input('R2 (k): ')+'K')
C = '100pF'#str(input('C: '))

def data_save(name, x, xname, y, yname):
    file_path = f"./data/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname])
        writer.writerows(zip(x, y))

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
    trigger_channel="D",
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
        peak_to_peak=1,
        offset=-1,
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

def freqFinder(voltage,time):
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

steps = 100
top_limit=152_000
bottom_limit=145_000
frequencies = np.linspace(bottom_limit, top_limit, steps)
awg_freq=[]
vco_freq=[]

for freq in frequencies:
    set_awg(freq)
    time, volts = picoscope.scope_capture()
    time = np.asarray(time)
    awg_out = np.asarray(volts[0])
    vco_out = np.asarray(volts[1])
    print(f'{np.round(((freq-bottom_limit)/(top_limit-bottom_limit))*100,0)}% complete')

    #awg_freq.append(freqFinder(awg_out,time))
    awg_freq.append(freq/1000)
    vco_freq.append(freqFinder(vco_out,time))



#print("Final frequencies:", frequency)
winsound.Beep(2500, 500)
#t.sleep(0.001)
winsound.Beep(2500, 500)

plot_styles = {'marker':'x','linestyle':'none'}

plt.plot(time, awg_freq,**plot_styles)
plt.plot(time, vco_freq,**plot_styles)
plt.ylabel("awg_freq/vco_freq)")
plt.xlabel("awg_freq (KHz)")
#plt.xlim(left=0)
#plt.ylim(bottom=0)
plt.grid(True)
os.makedirs("./images", exist_ok=True)
plt.savefig(f"./images/Closed_loop_PC1_ff_R1={R1}_R2={R2}_C={C}_f{bottom_limit/1000}(kHz) to {top_limit/1000}(kHz).png")
plt.show()
data_save(f"Closed_loop_PC1_ff_R1={R1}_R2={R2}_C={C}_f{bottom_limit/1000}(kHz) to {top_limit/1000}(kHz)", awg_freq, "awg_freq", vco_freq, "vco_freq")


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)