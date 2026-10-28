import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

folder = r"C:/Users/harry/Desktop/university work/year 3/E1a/data/6.5"

file_names = os.listdir(folder)

capacitance = file_names

time_data = []
dv_data=[]
vco_out_data = []

info_data=[]


tmp_path = f"{folder}/current_mirror"
subfolders = os.listdir(tmp_path)
for csv in subfolders:
    tmp_path_2 = f"{folder}/current_mirror/{csv}"
    df = pd.read_csv(tmp_path_2)
    time_data.append(df["time"].values)
    dv_data.append(df["dV data"].values)
    vco_out_data.append(df["vco_out"].values)
    info_data.append(csv[17:-4])

colours = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#42938C",
    "#000000",
    "#d019c4",
]

plot_styles = {'marker':'x','linestyle':'none'}
i=1
plt.plot(time_data[i], dv_data[i],color='purple')
plt.plot(time_data[i], vco_out_data[i],color='black')

plt.ylabel("dV (V) over C")
plt.xlabel("time")
plt.xlim(left=0)
plt.legend(['dV','pin7','pin6','Vco'])
plt.grid(True)
os.makedirs("./images", exist_ok=True)
#plt.savefig(f"./images/Capacitor_current_R1={R1}_R2={R2}_C={C}.png")
plt.show()
#data_save(f"Capacitor_current_R1={R1}_R2={R2}_C={C}", time, "time", dV, "dV data",vco_out,"vco_out")