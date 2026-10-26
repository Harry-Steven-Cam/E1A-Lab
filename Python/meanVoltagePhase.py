import pll_ps2000a as picoscope
import Python.old.arduino as arduino
import numpy as np
import matplotlib.pyplot as plt
import csv
import os

def data_save(name,x,xname,y,yname):
    file_path = f"../data/{name}.csv"

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xname, yname])
        writer.writerows(zip(x, y))

    print(f"Data saved to: {os.path.abspath(file_path)}")

picoscope.picoscope_open()
arduino.arduino_open()
picoscope.scope_prepare(
    capture_time=0.005,  # Traces will be captured over this time period (in seconds).
    samples=5000,  # Number of samples to capture over the capture_time period.
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
    trigger_direction="f",
    trigger_level=2.5,
    trigger_pre_percent=0,
    verbose=False,
)

t = 0.001  # period of pulses (NOT pulse width!) in seconds
p = 0.25  # phase difference in fraction of a period (+0.25 => +90 degrees or +π/2 radians)
n = 10  # number of cycles per pulse chain.

command = f"t={t} p={p} n={n}"

picoscope.scope_monitor()
mean_voltage_data = []
phase_data = []
steps =50
for i in range(0, steps+1):
    phase = i/steps
    print(phase)
    command = f"t={t} p={phase} n={n}"
    arduino.arduino_prepare()
    arduino.arduino_write(command)
    response = arduino.arduino_read()
    time, volts = picoscope.scope_capture()
    mean_voltage_data.append(np.mean(volts[3])) #selects data from channel 3 / the probe
    phase_data.append(phase)
plt.plot(phase_data,mean_voltage_data, 'x',linestyle='none')
os.makedirs('../images', exist_ok=True)
plt.savefig('../images/PC2.png')
plt.show()
data_save(f'PC2_scan{command},{steps}data',phase_data,'Phase Data',mean_voltage_data,'Mean voltage data')
picoscope.quick_save(  # Optional if you have no need of data output.
    time,  # Necessary - don't edit
    volts,  # Necessary - don't edit
    verbose=False,
    file_path=f"./data/ScanPC2 {command}.csv",  # Save data to this location.
)
'''
picoscope.quick_plot(  # Optional if you have no need of graphic output.
    time,  # Necessary - don't edit
    volts,  # Necessary - don't edit
    title=f"ϕ = {(p*2):+.3f} π, t = {t} s",  # Plot title (optional).
    display=True,  # Show a plot window (which you will need to close manually).
    legend=False,  # Show a legend on the plot.
    verbose=False,
    file_path=f"./images/phase PC2 {command}.png",  # Save plot image to this location (optional).
)
picoscope.quick_save(  # Optional if you have no need of data output.
    time,  # Necessary - don't edit
    volts,  # Necessary - don't edit
    verbose=False,
    file_path=f"./data/phase PC2 {command}.csv",  # Save data to this location.
)

'''
# Cycle through phase diffrences, mean voltage against phase diffrenece


picoscope.picoscope_close()

arduino.arduino_close()
