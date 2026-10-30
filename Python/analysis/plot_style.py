import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib as mpl

plot_styles = {"marker": "x", "linestyle": "none"}
colours = ["#EE7733", "#0077BB", "#33BBEE", "#EE3377", "#CC3311", "#009988", "#BBBBBB"]


def matplot_styles(
    x_min=None,
    x_max=None,
    y_min=None,
    y_max=None,
    unit_start=None,
    unit_end=None,
    unit_jump=None,
):
    mpl.rcParams.update(
        {
            # fonts
            "font.family": "serif",  # 'serif' | 'sans-serif' | 'monospace'
            "font.serif": [
                "Times New Roman",
                "DejaVu Serif",
            ],  # swap for 'Times New Roman' if installed
            "mathtext.fontset": "stix",  # maths font that matches Times
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            # axes
            "axes.grid": False,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "axes.spines.top": True,  # hide top/right box lines
            "axes.spines.right": True,
            "axes.linewidth": 0.8,
            "axes.titlepad": 12,  # gap between title and plot (points)
            "axes.labelpad": 6,
            # figures
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
    ax.set_xticks(np.arange(unit_start, unit_end, unit_jump))
    ax.set_box_aspect(9 / 16)
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)


def plot(
    x,
    y,
    names=None,
    title="no title",
    save_location=None,
    file_name=None,
    save=False,
    show_plot=True,
):
    plt.title(title)
    plt.plot(x, y, color=colours[1], **plot_styles)
    plt.xlabel(names[0])
    plt.ylabel(names[1])
    if save:
        os.makedirs(save_location, exist_ok=True)
        plt.savefig(f"{save_location}/{file_name}.png")
    if show_plot:
        plt.show()
