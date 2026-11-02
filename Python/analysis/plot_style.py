import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib as mpl

plot_styles = {"marker": "x", "linestyle": "none"}
colours = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#42938C",
    "#000000",
    "#d019c4",
]


def matplot_styles(
    unit_start=None,
    unit_end=None,
    unit_jump=None,
):
    mpl.rcParams.update(
        {
            # fonts
            "font.family": "serif",  # 'serif' | 'sans-serif' | 'monospace'
            "font.serif": [
                "Helvetica",
                "DejaVu Serif",
            ],  # swap for 'Times New Roman' if installed
            "mathtext.fontset": "stix",  # maths font that matches Times
            "font.size": 11,
            "axes.titlesize": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 10,
            "axes.titlelocation": "left",
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
            "figure.dpi": 100,  # on-screen resolution
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
    if unit_start != unit_end:
        ax.set_xticks(np.arange(unit_start, unit_end, unit_jump))
    ax.set_box_aspect(9 / 16)


def format_sci(value, decimals=2):
    # Format the number to standard Python scientific notation (e.g., '1.23e+04')
    sci_str = f"{value:.{decimals}e}"
    # Split the string into the mantissa and the exponent
    mantissa, exponent = sci_str.split("e")
    # Convert exponent to integer to strip the '+' and leading zeros (e.g., '+04' -> 4)
    exp_int = int(exponent)
    if value == 0:
        return 0
    return rf"{mantissa} $\times$ $10^{{{exp_int}}}$"


def format_sci_err(value, error, decimals=2):
    # Handle the zero edge case
    if value == 0 and error == 0:
        return "0"
    # Determine the shared exponent based on the primary value
    # (If the value is exactly 0, base the order of magnitude on the error)
    base_val = value if value != 0 else error

    sci_str = f"{base_val:.{decimals}e}"
    exponent = int(sci_str.split("e")[1])

    # Scale both numbers by the shared exponent
    val_scaled = value / (10**exponent)
    err_scaled = error / (10**exponent)
    # Drop the scientific multiplier entirely if the exponent is 0
    if exponent == 0:
        return rf"{val_scaled:.{decimals}f} $\pm$ {err_scaled:.{decimals}f}"

    return rf"({val_scaled:.{decimals}f} $\pm$ {err_scaled:.{decimals}f}) $\times$ $10^{{{exponent}}}$"


# Format string for nice legends (e.g. converting '100k' to '100 k$\Omega$') and infinity
def format_val(val):
    value = val
    if not val:
        return ""
    if val in ["infinitek", "inf"]:
        return r"${\infty}$ $\Omega$"
    elif "pf" in val.lower():
        value = f"{int(value.lower().replace("pf", ""))*1e-3}nF"
    return value.replace("pf", " pF").replace("nf", " nF").replace("k", r" k$\Omega$")


def data_to_val(val):
    value = val.lower().strip()
    if value in ("infinite", "inf", "infinity","infinitek"):
        return np.inf

    if value.endswith("k"):
        return float(value[:-1]) * 1e3
    elif value.endswith("nf"):
        return float(value[:-2]) * 1e-9
    elif value.endswith("pf"):
        return float(value[:-2]) * 1e-12
    else:
        return float(value)

# Helper function to extract C, R1, R2 from the filename
def parse_filename(filename):
    params = {"c": None, "r1": None, "r2": None}
    parts = filename.lower().split("_")
    for p in parts:
        if p.startswith("c="):
            params["c"] = p[2:]
        elif p.startswith("r1="):
            params["r1"] = p[3:]
        elif p.startswith("r2="):
            params["r2"] = p[3:]
    return params


def plot_data(
    x,
    y,
    names=None,
    title="no title",
    save_location=None,
    file_name=None,
    save=False,
    show_plot=True,
    alpha=1,
    linestyle="none",
    marker="x",
):
    plt.title(title)
    if np.ndim(x[0]) > 0:
        for i, (x_data, y_data) in enumerate(zip(x, y)):
            c = colours[i % len(colours)]
            plt.plot(
                x_data, y_data, color=c, alpha=alpha, linestyle=linestyle, marker=marker
            )
    else:
        # Dimension is 0 (it's a scalar number)
        plt.plot(
            x, y, color=colours[0], alpha=alpha, linestyle=linestyle, marker=marker
        )

    if names:
        plt.xlabel(names[0])
        plt.ylabel(names[1])

    if save:
        os.makedirs(save_location, exist_ok=True)
        plt.savefig(f"{save_location}/{file_name}.svg")
    if show_plot:
        plt.show()


def plot_2x2(
    x,
    y,
    names=None,
    title="no title",
    save_location=None,
    file_name=None,
    save=False,
    show_plot=True,
):
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    # If title is a single string, use it as the main figure title
    if isinstance(title, str):
        fig.suptitle(title)
        subplot_titles = [None] * 4
    else:
        # Otherwise, assume it's a list of 4 subplot titles
        subplot_titles = title

    for i in range(min(4, len(x))):
        ax = axes[i]

        # If the first element of subplot i has a dimension > 0, it contains nested arrays
        if np.ndim(x[i][0]) > 0:
            for j, (x_data, y_data) in enumerate(zip(x[i], y[i])):
                c = colours[j % len(colours)]
                ax.plot(x_data, y_data, color=c, **plot_styles)
        else:
            # Single dataset for subplot i
            ax.plot(x[i], y[i], color=colours[1], **plot_styles)

        if subplot_titles[i] is not None:
            ax.set_title(subplot_titles[i])

        # Handle axis labels
        if names:
            if isinstance(names[0], str):
                # Same labels applied to all 4 graphs
                ax.set_xlabel(names[0])
                ax.set_ylabel(names[1])
            else:
                # Specific labels for each graph (list of 4 lists)
                ax.set_xlabel(names[i][0])
                ax.set_ylabel(names[i][1])

    # Automatically adjust layout so titles/labels don't overlap
    plt.tight_layout()

    if save:
        os.makedirs(save_location, exist_ok=True)
        plt.savefig(f"{save_location}/{file_name}.svg")
    if show_plot:
        plt.show()
