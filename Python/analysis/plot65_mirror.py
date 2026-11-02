import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from plot_style import *
from line_finder import *

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-lab/data/6.5"
save_location = r"C:/Users/harry/Desktop/university work/year 3/E1A-lab/analysis_images/6.5/current_mirror"

save_data = False
show_plot = True

file_names = os.listdir(folder)
capacitance = file_names

time_data = []
dv_data = []
vco_out_data = []

info_data = []


tmp_path = f"{folder}/current_mirror"
subfolders = os.listdir(tmp_path)
for csv in subfolders:
    tmp_path_2 = f"{folder}/current_mirror/{csv}"
    df = pd.read_csv(tmp_path_2)
    time_data.append(df["time"].values)
    dv_data.append(df["dV data"].values)
    vco_out_data.append(df["vco_out"].values)
    info_data.append(csv[17:-4])

import numpy as np

def calculate_filtered_gradient(time, dV,window_sections=20):
    # Calculate the differences for both axes: delta V and delta t
    time_window = window_sections * (max(time) - min(time))
    time_sections =[]
    voltage_sections=[]
    for i in range(window_sections-1):
        start_index=len(time)*i//window_sections
        end_index=len(time)*(i+1)//window_sections
        time_sections.append(time[start_index:end_index])
        voltage_sections.append(dV[start_index:end_index])
    #section into little segments and I will find their gradients and plot
    
    # Calculate the instantaneous gradient (m_i = delta_V / delta_t)
    gradient = delta_V / delta_t
    
    # The downward slopes are negative, while the "near infinity" resets are large positive values.
    # Filter the array to keep only the negative gradients to exclude the vertical jumps.
    valid_indices = gradient if abs(gradient) < 1e9 else None
    valid_gradients = gradient[valid_indices]
    
    # Optional: Calculate the single average gradient of the downward segments
    average_slope = np.mean(valid_gradients)
    
    return valid_gradients, average_slope

plot_styles = {"marker": "x", "linestyle": "none"}

for i in range(len(info_data)):
    matplot_styles()
    info = info_data[i]
    p=parse_filename(info)
    R1=p["r1"]
    R2=p["r2"]
    C=p["c"]
    #current=data_to_val(C)*gradient
    plt.plot(time_data[i], dv_data[i], color="purple")
    plt.plot(time_data[i], vco_out_data[i], color="black")
    plt.axhline(y=0, color='#000000', linestyle='-', linewidth=1.5, zorder=1)
    plt.ylabel("Voltage over C (V)")
    plt.xlabel("Time (s)")
    plt.xlim(left=0)
    #plt.legend(["dV", "pin7", "pin6", "Vco"])
    os.makedirs(save_location, exist_ok=True)
    if save_data:
        plt.savefig(f"{save_location}/Capacitor_current_R1={R1}_R2={R2}_C={C}.svg")
    if show_plot:
        plt.show()
    else:
        plt.close()