import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import time as t

#winsound.Beep(2500, 1000)

R1 = '100K' #str(input('R1 (k): ')+'K')
R2 = '100K' #str(input('R2 (k): ')+'K')
C = '100nF' #str(input('C: '))

def data_save(name, x, xname, y, yname,z,zname):
    file_path = f"./data/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname,zname])
        writer.writerows(zip(x, y,z))

    print(f"Data saved to: {os.path.abspath(file_path)}")


picoscope.picoscope_open()
time =0.02
samplerate = 1e7
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
    trigger_channel="A",
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

voltage = (1.88/5)*3 #should be around 18kHz

set_awg(voltage)
time, volts = picoscope.scope_capture()
voltage_data_pin_7=volts[0]
voltage_data_pin_6 =volts[1]
vco_out = volts[3]
#print(voltage_data_pin_7[0])
dV = [voltage_data_pin_7[x]-voltage_data_pin_6[x] for x in range(len(voltage_data_pin_7))]
time = np.asarray(time)

plot_styles = {'marker':'x','linestyle':'none'}

plt.plot(time, dV,color='purple')
plt.plot(time, voltage_data_pin_7,color='blue')
plt.plot(time, voltage_data_pin_6,color='red')
plt.plot(time, vco_out,color='black')
plt.ylabel("dV (V) over C")
plt.xlabel("time")
plt.xlim(left=0)
#plt.ylim(bottom=0)
plt.legend(['dV','pin7','pin6','Vco'])
plt.grid(True)
os.makedirs("./images", exist_ok=True)
plt.savefig(f"./images/Capacitor_current_R1={R1}_R2={R2}_C={C}.png")
plt.show()
data_save(f"Capacitor_current_R1={R1}_R2={R2}_C={C}", time, "time", dV, "dV data",vco_out,"vco_out")


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)