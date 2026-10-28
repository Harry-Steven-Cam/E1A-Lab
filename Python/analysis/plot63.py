import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.3"
save_location = (
    r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.3"
)

save_fig = False
plot_styles = {"marker": "x", "linestyle": "none"}

files = os.listdir(folder)

phase_data = []
mean_voltage_data = []
info_data = ["Phase /°", "Mean voltage /V"]


def matplot_styles():
    mpl.rcParams.update(
        {
            # fonts
            "font.family": "Times New Roman",  # 'serif' | 'sans-serif' | 'monospace'
            "font.serif": [
                "Times New Roman"
            ],  # swap for 'Times New Roman' if installed
            # axes
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "axes.spines.top": False,  # hide top/right box lines
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            #figures
            "figure.dpi": 150,  # on-screen resolution
            "savefig.dpi": 150,  # saved-file resolution
            "savefig.bbox": "tight",  # trim whitespace on save
            "figure.constrained_layout.use": False,  # auto-avoid overlapping labels
            # ticks
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "xtick.top": False,
            "ytick.right": False,
            # lines / markers
            "lines.linewidth": 1.5,
            "lines.markersize": 5,
            "errorbar.capsize": 3,
            # legend
            "legend.frameon": False,
            "legend.loc": "best",
        }
    )
    ax = plt.gca()
    ax.set_xticks(np.arange(0, 361, 30))
    ax.set_box_aspect(9/16)
    plt.xlim(left=0)
    plt.ylim(0,5)



def plot(x, y, names, save=False):
    matplot_styles()
    plt.title('PC1 Mean voltage output vs phase difference of signals')
    plt.plot(x, y, color="#0072B2", **plot_styles)
    plt.xlabel(names[0])
    plt.ylabel(names[1])
    plt.grid(True)
    if save:
        os.makedirs(save_location, exist_ok=True)
        plt.savefig(f"{save_location}/phase_V_avg_63.png")
    plt.show()
    plt.clf()


for csv in files:
    phase_data = []
    mean_voltage_data = []
    df = pd.read_csv(f"{folder}/{csv}")
    phase_data.append(df["Phase Data"].values * 360)
    mean_voltage_data.append(df["Mean voltage data"].values)
    plot(phase_data, mean_voltage_data, info_data, save=save_fig)
