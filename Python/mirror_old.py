import pll_ps2000a as picoscope
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import time as t

# winsound.Beep(2500, 1000)

R1 = "100K"  # str(input('R1 (k): ')+'K')
R2 = "100K"  # str(input('R2 (k): ')+'K')
C = str(input('C (in nf, no nF): ')+'nF')


def data_save(name, x, xname, y, yname, z, zname,l,lname,p,pname):
    file_path = f"./data/{name}.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname, zname, lname, pname])
        writer.writerows(zip(x, y, z, l, p))

    print(f"Data saved to: {os.path.abspath(file_path)}")


picoscope.picoscope_open()
time = 0.02
samplerate = 1e7
picoscope.scope_prepare(
    capture_time=0.02,  # Traces will be captured over this time period (in seconds).
    samples=50_000,  # Number of samples to capture over the capture_time period.
    a_range=10,  # Voltage range for channel A (in volts).
    b_range=10,  # Voltage range for channel A (in volts).
    c_range=10,  # Voltage range for channel A (in volts).
    d_range=10,  # Voltage range for channel A (in volts).
    a_probe="x10",  # Probe attenuation for channel A (x1 is the default).
    b_probe="x10",  # Probe attenuation for channel A (x1 is the default).
    c_probe="x10",  # Probe attenuation for channel A (x1 is the default).
    d_probe="x10",  # Probe attenuation for channel A (x1 is the default).
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
    # print("awg set")


def save_scope(voltage, time, volts):
    plt.plot(time, volts)
    plt.xlabel("time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    os.makedirs("./images", exist_ok=True)
    plt.savefig(f"./images/{voltage}.png")
    plt.clf()


# picoscope.scope_monitor()
print("running")

#frequency = 18_000
#FIXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
voltage = (1.8 / 5) * 3  # should be around 18kHz

set_awg(voltage)
time, volts = picoscope.scope_capture()
voltage_data_capacitor = volts[0] #pin 7
voltage_data_vco_out = volts[1] #pin 6

voltage_data_r1 = volts[2]
voltage_data_r2 = volts[3]
time = np.asarray(time)

plot_styles = {"marker": "x", "linestyle": "none"}

plt.plot(time, voltage_data_capacitor, color="purple")
plt.plot(time, voltage_data_vco_out, color="blue")
plt.plot(time, voltage_data_r1, color="red")
plt.plot(time, voltage_data_r2, color="black")
plt.ylabel("dV (V) over C")
plt.xlabel("time")
plt.xlim(left=0)
# plt.ylim(bottom=0)
plt.legend(["Capacitor Voltage", "VCO Output", "R1 Voltage", "R2 Voltage"])
plt.grid(True)
os.makedirs("./images", exist_ok=True)
plt.savefig(f"./images/Capacitor_current_R1={R1}_R2={R2}_C={C}.png")
plt.show()
data_save(
    f"Capacitor_current_R1={R1}_R2={R2}_C={C}",
    time,
    "time",
    voltage_data_capacitor,
    "capacitor_voltage",
    voltage_data_vco_out,
    "vco_out",
    voltage_data_r1,
    "r1_voltage",
    voltage_data_r2,
    "r2_voltage"
)


picoscope.picoscope_close()
print(R1)
print(R2)
print(C)