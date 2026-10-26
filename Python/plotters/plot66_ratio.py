import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

folder = r"C:/Users/harry/Desktop/university work/year 3/E1a/data/6.6"

file_names = os.listdir(folder)

data = file_names

awg_freq_data = []
vco_freq_data = []
info_data = []

for csv in data:
    tmp_path = f"{folder}/{csv}"
    df = pd.read_csv(tmp_path)
    awg_freq_data.append(df["awg_freq"].values)
    vco_freq_data.append(df["vco_freq"].values)
    info_data.append(csv[0:-4])

ratio = []
for i in range(len(awg_freq_data)):
    ratio.append(
        [
            awg_freq_data[i][x] / vco_freq_data[i][x]
            for x in range(len(awg_freq_data[i]))
        ]
    )

colours = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
    "#393b79",
    "#637939",
]

for i in range(len(info_data)):
    plt.plot(awg_freq_data[i], ratio[i], "x", color=colours[i], linestyle="none")
plt.ylabel("ratio")
plt.xlabel("awg_freq_data")
plt.xlim(left=0)
# plt.ylim(bottom=0)
plt.legend(info_data)
plt.show()
