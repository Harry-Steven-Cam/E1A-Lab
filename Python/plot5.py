import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

folder = r"C:/Users/hs916/Desktop/PLL hs916/data/6.5"

file_names = os.listdir(folder)

capacitance = file_names

voltage_data = []
frequency_data = []
info_data = []

for c in capacitance:
    if c != "current_mirror":
        tmp_path = f"{folder}/{c}"
        subfolders = os.listdir(tmp_path)
        for csv in subfolders:
            tmp_path_2 = f"{folder}/{c}/{csv}"
            df = pd.read_csv(tmp_path_2)
            frequency_data.append(df["Frequency"].values)
            voltage_data.append(df["Voltage data"].values)
            info_data.append(csv[0:-4])

colours = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#42938C",
    "#000000",
    "#d019c4",
]
"""
for x in range(7):
    for i in range(4):  # range(len(voltage_data)):
        plt.plot(voltage_data[i+x*4], frequency_data[i+x*4], color=colours[i])
    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Voltage (V)")
    plt.xlim(left=0)
    #plt.ylim(bottom=0)
    plt.legend(info_data[x*4:x*4+4])
    plt.show()
"""

print("Choose a plotting option:")
print("1: Fixed R1 when C = 1000pF")
print("2: Fixed R2 when C = 1000pF")
print("3: Fixed R1 and fixed R2 across all capacitances")
print("4: All resistor combinations for a fixed capacitance")
print("5: Diagonals where R1 = R2 for C = 1000pF")
choice = input("Enter choice (1/2/3/4/5): ")

plot_indices = []

if choice == "1":
    r1_val = input("Enter R1 value (e.g., 9.9k, 100k, 1000k, infinite): ").lower()
    for i, info in enumerate(info_data):
        info_lower = info.lower()
        if f"r1={r1_val}" in info_lower and "1000pf" in info_lower:
            plot_indices.append(i)

elif choice == "2":
    r2_val = input("Enter R2 value (e.g., 9.9k, 100k, 1000k, infinite): ").lower()
    for i, info in enumerate(info_data):
        info_lower = info.lower()
        if f"r2={r2_val}" in info_lower and "1000pf" in info_lower:
            plot_indices.append(i)

elif choice == "3":
    print("R_1=100K is the only value available")
    r1_val = "100k"
    r2_val = input("Enter R2 value (e.g., 9.9k, 100k, infinite): ").lower()
    for i, info in enumerate(info_data):
        info_lower = info.lower()
        if f"r1={r1_val}" in info_lower and f"r2={r2_val}" in info_lower:
            plot_indices.append(i)

elif choice == "4":
    c_val = input(
        "Enter capacitance value (e.g., 10nf, 100nf, 100pf, 1000pf): "
    ).lower()
    for i, info in enumerate(info_data):
        info_lower = info.lower()
        if f"c={c_val}" in info_lower:
            plot_indices.append(i)

elif choice == "5":
    for i, info in enumerate(info_data):
        info_lower = info.lower()
        if "1000pf" in info_lower:
            parts = info_lower.split("_")
            r1_str = next((p.split("=")[1] for p in parts if p.startswith("r1=")), None)
            r2_str = next((p.split("=")[1] for p in parts if p.startswith("r2=")), None)
            if r1_str is not None and r2_str is not None and r1_str == r2_str:
                plot_indices.append(i)
else:
    print("Invalid choice.")

if plot_indices:
    plt.figure()
    for count, idx in enumerate(plot_indices):
        plt.plot(
            voltage_data[idx],
            frequency_data[idx],
            color=colours[count % len(colours)],
            label=info_data[idx],
        )

    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Voltage (V)")
    plt.xlim(left=0)
    plt.legend()
    plt.show()
else:
    print("No data found matching those parameters.")