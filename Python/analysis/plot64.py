import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.4"
save_location=r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.4"

save_fig=False
plot_styles = {'marker':'x','linestyle':'none'}

files = os.listdir(folder)

phase_data = []
mean_voltage_data=[]
info_data=['Phase (°)','Mean voltage (V)']

def matplot_styles():
    ax = plt.gca()  
    ax.set_facecolor("yellow")

def plot(x,y,names,save=False):
    matplot_styles()
    plt.plot(x, y,color='blue',**plot_styles)
    plt.xlabel(names[0])
    plt.ylabel(names[1])
    plt.xlim(left=0)
    plt.grid(True)
    if save:
        os.makedirs(save_location, exist_ok=True)
        plt.savefig(f"{save_location}/phase_V_avg_63.png")
    plt.show()
    plt.clf()

for csv in files:
    if csv[-3:]=='csv':
        phase_data = []
        mean_voltage_data=[]
        df = pd.read_csv(f'{folder}/{csv}')
        phase_data.append(df["Phase Data"].values*360)
        mean_voltage_data.append(df["Mean voltage data"].values)
        plot(phase_data,mean_voltage_data,info_data,save=save_fig)