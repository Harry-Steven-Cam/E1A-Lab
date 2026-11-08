import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.ticker import FuncFormatter, MaxNLocator

from scipy import odr

from plot_style import *
from line_finder import *

# ============================================================
# SETTINGS
# ============================================================

folder = r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/data/6.5"

save_location = (
    r"C:/Users/harry/Desktop/university work/year 3/E1A-Lab/analysis_images/6.5/RCRcombos"
)

save_data = False
show_plots = False

os.makedirs(save_location, exist_ok=True)


# Component tolerances
COMPONENT_TOLERANCE = 0.05

# True: treat ±5% as a 1-sigma uncertainty.
# False: treat ±5% as a maximum tolerance with a
# rectangular probability distribution (divide by sqrt(3)).
TOLERANCE_IS_1SIGMA = True


# ============================================================
# COMPONENT UNCERTAINTY CALCULATIONS
# ============================================================


def get_component_x_error(param, nominal_value):
    """
    Calculates the x-axis value and uncertainty for a component.

    For resistors:
        x = 1/R

    The uncertainty is calculated using the exact transformed
    limits corresponding to R +/- 5%.

    For capacitors:
        x = C

    Returns:
        x       : nominal x-axis value
        x_err   : symmetric standard uncertainty for ODR
        x_lower : lower error bar magnitude
        x_upper : upper error bar magnitude
    """

    tolerance = COMPONENT_TOLERANCE

    if param in ("r1", "r2"):

        resistance = data_to_val(nominal_value)

        if resistance <= 0:
            raise ValueError("Resistance must be positive")

        x = 1 / resistance

        # Exact limits after transforming R +/- 5% into 1/R
        x_min = 1 / (resistance * (1 + tolerance))
        x_max = 1 / (resistance * (1 - tolerance))

        x_lower = x - x_min
        x_upper = x_max - x

    elif param == "c":

        capacitance = data_to_val(nominal_value)
        tolerance=0.1
        if capacitance <= 0:
            raise ValueError("Capacitance must be positive")

        x = capacitance

        # Capacitance is plotted directly, so uncertainty is symmetric
        x_lower = tolerance * x
        x_upper = tolerance * x

    else:
        raise ValueError(f"Unknown parameter: {param}")

    # Convert tolerance into standard uncertainty for ODR
    tolerance_factor = 1.0 if TOLERANCE_IS_1SIGMA else 1 / np.sqrt(3)

    x_err = ((x_lower + x_upper) / 2) * tolerance_factor

    return x, x_err, x_lower, x_upper


# ============================================================
# ORTHOGONAL DISTANCE REGRESSION
# ============================================================


def fit_line_odr(x, y, x_err, y_err=None, steps=200):
    """
    Performs linear orthogonal distance regression.

    Accounts for:
        - Horizontal uncertainties (x_err)
        - Vertical uncertainties (y_err)

    If y_err is None, the vertical data are treated as
    unweighted.

    Returns:
        x_fit
        y_fit
        gradient
        intercept
        gradient_err
        intercept_err
        r_squared
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_err = np.asarray(x_err, dtype=float)

    if y_err is not None:
        y_err = np.asarray(y_err, dtype=float)

    def linear_model(beta, x):
        return beta[0] * x + beta[1]

    model = odr.Model(linear_model)

    data = odr.RealData(x, y, sx=x_err, sy=y_err)

    # Initial estimate from ordinary linear regression
    initial_guess = np.polyfit(x, y, 1)

    regression = odr.ODR(data, model, beta0=initial_guess)

    output = regression.run()

    gradient = output.beta[0]
    intercept = output.beta[1]

    # Use unscaled covariance because the supplied uncertainties
    # are being treated as absolute standard uncertainties.
    gradient_err = np.sqrt(output.cov_beta[0, 0])
    intercept_err = np.sqrt(output.cov_beta[1, 1])

    # Generate fitted line
    x_fit = np.linspace(min(x), max(x), steps)
    y_fit = linear_model(output.beta, x_fit)

    # Calculate conventional R squared
    y_pred = linear_model(output.beta, x)

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

    return (x_fit, y_fit, gradient, intercept, gradient_err, intercept_err, r_squared)


# ============================================================
# LOAD DATA
# ============================================================

file_names = os.listdir(folder)
capacitance = file_names

voltage_data = []
frequency_data = []
info_data = []
parsed_info = []


# Load all data
for c in capacitance:

    if c == "current_mirror":
        continue

    tmp_path = f"{folder}/{c}"

    if not os.path.isdir(tmp_path):
        continue

    subfolders = os.listdir(tmp_path)

    for csv in subfolders:

        if not csv.endswith(".csv"):
            continue

        tmp_path_2 = f"{folder}/{c}/{csv}"

        df = pd.read_csv(tmp_path_2)

        freq_vals = df["Frequency"].values
        volt_vals = df["Voltage data"].values

        filename_no_ext = csv[0:-4]

        frequency_data.append(freq_vals * 1e3)
        voltage_data.append(volt_vals)
        info_data.append(filename_no_ext)

        parsed_info.append(parse_filename(filename_no_ext))


# ============================================================
# STORAGE FOR COMBINED PLOTS
# ============================================================

combined_plot_data = {
    "r1": [],
    "r2": [],
    "c": [],
    "fmin_inv_c": [],
}

# ============================================================
# MAIN PLOTTING FUNCTION
# ============================================================


def create_and_save_plot(indices, title, varying_param, filename_out, fixed_param=None):

    if not indices:
        return

    # --------------------------------------------------------
    # Plot setup
    # --------------------------------------------------------

    plt.figure()
    matplot_styles()

    ax = plt.gca()

    max_freq = 0

    # --------------------------------------------------------
    # Storage for combined plots
    # --------------------------------------------------------

    k_o_values = []
    k_err_values = []

    f_min_values = []
    f_min_err_values = []

    x_data_values = []
    x_err_values = []

    x_err_lower_values = []
    x_err_upper_values = []

    inverse_fmin_vs_c_data= []

    # --------------------------------------------------------
    # Plot each line
    # --------------------------------------------------------

    for count, idx in enumerate(indices):

        params = parsed_info[idx]

        # ----------------------------------------------------
        # Determine varying parameter and uncertainty
        # ----------------------------------------------------

        if varying_param == "r1":

            label = f"$R_1$ = {format_val(params['r1'])} "

            x, x_err, x_lower, x_upper = get_component_x_error("r1", params["r1"])

        elif varying_param == "r2":

            label = f"$R_2$ = {format_val(params['r2'])} "

            x, x_err, x_lower, x_upper = get_component_x_error("r2", params["r2"])

        elif varying_param == "c":

            label = f"$C$ = {format_val(params['c'])} "

            x, x_err, x_lower, x_upper = get_component_x_error("c", params["c"])

        else:

            label = info_data[idx]

            x = np.nan
            x_err = np.nan
            x_lower = np.nan
            x_upper = np.nan

        x_data_values.append(x)
        x_err_values.append(x_err)

        x_err_lower_values.append(x_lower)
        x_err_upper_values.append(x_upper)

        # ----------------------------------------------------
        # Find slope and fit over region
        # ----------------------------------------------------

        t_min = 10e-7

        error_freq = t_min * frequency_data[idx]  ** 2#convert to Hz, standard error prop, 1/t => 1/t^2 dt

        error_voltage = get_voltage_errors(voltage_data[idx], resolution_bits=6)

        x_fit, y_fit, gradient, m_err = finding_slope(
            voltage_data[idx], frequency_data[idx], error_x=error_voltage, error_y=error_freq
        )

        # Calculate KO and its uncertainty
        k_o = np.absolute(2 * np.pi * gradient)

        k_err = np.absolute(2 * np.pi * m_err)

        # Minimum frequency and its uncertainty
        f_min = frequency_data[idx][0] 

        f_min_err = error_freq[0]

        k_o_values.append(k_o)
        k_err_values.append(k_err)

        f_min_values.append(f_min)
        f_min_err_values.append(f_min_err)
        if varying_param == "c":

            C = data_to_val(params["c"])


        # ----------------------------------------------------
        # Update legend
        # ----------------------------------------------------

        label += rf", $K_{{O}}$ = {format_sci_err(k_o,k_err,decimals=4)} Hz/V"

        # ----------------------------------------------------
        # Plot original VCO response
        # ----------------------------------------------------

        plt.plot(
            voltage_data[idx],
            frequency_data[idx],
            color=colours[count % len(colours)],
            label=label,
            alpha=0.6,
        )

        plt.plot(x_fit, y_fit, color=colours[count % len(colours)], linestyle="--", alpha=1)

        # ----------------------------------------------------
        # Update maximum frequency
        # ----------------------------------------------------

        if max_freq < max(frequency_data[idx]):
            max_freq = max(frequency_data[idx])

    # --------------------------------------------------------
    # Set styles and axes
    # --------------------------------------------------------

    ax.set_xticks(np.arange(0, 6, 1))

    if max_freq < 200_000:
        ax.set_yticks(np.arange(0, max_freq + 20_000, 20_000))
    else:
        ax.set_yticks(np.arange(0, max_freq + 20_000, 100_000))
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, _: f"{y / 1000:g}")
    )

    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Voltage (V)")

    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.title(title)

    plt.legend(fontsize=8)

    plt.tight_layout()

    # --------------------------------------------------------
    # Save / show plot
    # --------------------------------------------------------

    if save_data:

        plt.savefig(os.path.join(save_location, "curves_" + filename_out), dpi=300)

    if show_plots:
        plt.show()
    else:
        plt.close()

    # ========================================================
    # STORE DATA FOR COMBINED PLOTS
    # ========================================================

    fixed_params = parsed_info[indices[0]]

    # Asymmetric error bars, stored as a 2 x N array
    x_errors_plot = np.vstack(
        (np.asarray(x_err_lower_values, dtype=float), np.asarray(x_err_upper_values, dtype=float))
    )

    # Symmetric uncertainty for ODR
    x_errors_fit = np.asarray(x_err_values, dtype=float)

    # --------------------------------------------------------
    # KO against 1/R1
    # --------------------------------------------------------

    if varying_param == "r1":

        combined_plot_data["r1"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "x_err": x_errors_fit,
                "x_err_plot": x_errors_plot,
                "y": np.asarray(k_o_values, dtype=float),
                "y_err": np.asarray(k_err_values, dtype=float),
                "label": (
                    f"R2={format_val(fixed_params['r2'])} , " f"C={format_val(fixed_params['c'])} "
                ),
            }
        )

    # --------------------------------------------------------
    # Minimum frequency against 1/R2
    # --------------------------------------------------------

    elif varying_param == "r2":

        combined_plot_data["r2"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "x_err": x_errors_fit,
                "x_err_plot": x_errors_plot,
                "y": np.asarray(f_min_values, dtype=float),
                "y_err": np.asarray(f_min_err_values, dtype=float),
                "label": (
                    f"R1={format_val(fixed_params['r1'])}, " f"C={format_val(fixed_params['c'])}"
                ),
            }
        )

    # --------------------------------------------------------
    # Inverse KO against capacitance
    # --------------------------------------------------------

    elif varying_param == "c":

        k_values = np.asarray(k_o_values, dtype=float)

        k_errors = np.asarray(k_err_values, dtype=float)

        # Propagate uncertainty through 1/KO:
        #
        # y = 1/KO
        #
        # Δy = ΔKO / KO²

        inverse_k_values = np.divide(
            1, k_values, out=np.full_like(k_values, np.inf), where=k_values != 0
        )

        inverse_k_errors = np.divide(
            k_errors, k_values**2, out=np.full_like(k_errors, np.inf), where=k_values != 0
        )

        combined_plot_data["c"].append(
            {
                "x": np.asarray(x_data_values, dtype=float),
                "x_err": x_errors_fit,
                "x_err_plot": x_errors_plot,
                "y": inverse_k_values,
                "y_err": inverse_k_errors,
                "label": (
                    f"R1={format_val(fixed_params['r1'])} , "
                    f"R2={format_val(fixed_params['r2'])} "
                ),
            }
        )
        # ----------------------------------------------------
        # f_min against 1/C
        # ----------------------------------------------------

        C = np.asarray(x_data_values, dtype=float)

        f_min_array = np.asarray(f_min_values, dtype=float)
        f_min_err_array = np.asarray(f_min_err_values, dtype=float)

        # Convert capacitance to inverse capacitance
        inverse_C = 1 / C

        # Calculate asymmetric uncertainties
        inverse_C_lower = inverse_C - 1 / (
            C * (1 + COMPONENT_TOLERANCE)
        )

        inverse_C_upper = (
            1 / (C * (1 - COMPONENT_TOLERANCE)) - inverse_C
        )

        # Symmetric uncertainty for ODR
        tolerance_factor = (
            1.0 if TOLERANCE_IS_1SIGMA else 1 / np.sqrt(3)
        )

        inverse_C_err = (
            (inverse_C_lower + inverse_C_upper) / 2
        ) * tolerance_factor

        combined_plot_data["fmin_inv_c"].append({
            "x": inverse_C,
            "x_err": inverse_C_err,
            "x_err_plot": np.vstack((
                inverse_C_lower,
                inverse_C_upper
            )),
            "y": f_min_array,
            "y_err": f_min_err_array,
            "label": (
                f"R1={format_val(fixed_params['r1'])}, "
                f"R2={format_val(fixed_params['r2'])}"
            ),
        })


# ============================================================
# COMBINED PLOTTING FUNCTION
# ============================================================


def create_combined_plot(param, ylabel, xlabel, title, filename):

    datasets = combined_plot_data[param]

    if not datasets:
        return

    plt.figure()

    matplot_styles()

    ax = plt.gca()

    # --------------------------------------------------------
    # Plot each dataset
    # --------------------------------------------------------

    for i, data in enumerate(datasets):

        x = data["x"]
        y = data["y"]

        # Horizontal uncertainties
        x_err = data["x_err"]
        x_err_plot = data["x_err_plot"]

        # Vertical uncertainties
        y_err = data.get("y_err", None)

        # ----------------------------------------------------
        # Remove invalid values
        # ----------------------------------------------------

        valid = (
            np.isfinite(x)
            & np.isfinite(y)
            & np.isfinite(x_err)
            & (x_err >= 0)
            & np.all(np.isfinite(x_err_plot), axis=0)
        )

        if y_err is not None:

            valid &= np.isfinite(y_err) & (y_err >= 0)

        x = x[valid]
        y = y[valid]

        x_err = x_err[valid]

        x_err_plot = x_err_plot[:, valid]

        if y_err is not None:
            y_err = y_err[valid]

        if len(x) == 0:
            continue

        colour = colours[i % len(colours)]

        # ----------------------------------------------------
        # Plot experimental data with error bars
        # ----------------------------------------------------

        plt.errorbar(
            x,
            y,
            xerr=x_err_plot,
            yerr=y_err,
            marker="x",
            linestyle="none",
            color=colour,
            alpha=0.8,
            capsize=3,
        )

        # ----------------------------------------------------
        # Orthogonal distance regression
        # ----------------------------------------------------

        r_squared = np.nan
        gradient = np.nan
        gradient_err = np.nan

        # Only use points with positive uncertainties for ODR
        fit_valid = x_err > 0

        if y_err is not None:
            fit_valid &= y_err > 0

        # Extract points suitable for fitting
        fit_x = x[fit_valid]
        fit_y = y[fit_valid]
        fit_x_err = x_err[fit_valid]

        if y_err is not None:
            fit_y_err = y_err[fit_valid]
        else:
            fit_y_err = None

        # Perform fit if at least two valid points exist
        if len(fit_x) >= 2 and len(np.unique(fit_x)) >= 2:

            try:

                (
                    x_fit,
                    y_fit,
                    gradient,
                    intercept,
                    gradient_err,
                    intercept_err,
                    r_squared,
                ) = fit_line_odr(
                    fit_x,
                    fit_y,
                    fit_x_err,
                    fit_y_err
                )

                plt.plot(
                    x_fit,
                    y_fit,
                    linestyle="--",
                    color=colour,
                    alpha=0.8
                )

            except (RuntimeError, ValueError, np.linalg.LinAlgError, TypeError) as e:

                print(f"Fit failed for {data['label']}: {e}")

        # ----------------------------------------------------
        # Determine gradient units
        # ----------------------------------------------------

        if param == "r1":
            m_unit = r"Hz $\Omega$/V"

        elif param == "r2":
            m_unit = r"Hz $\Omega$"

        elif param == "fmin_inv_c":
            m_unit = r"Hz F"

        else:
            m_unit = r"V/(Hz F)"

        # ----------------------------------------------------
        # Create legend
        # ----------------------------------------------------

        if np.isfinite(gradient) and np.isfinite(gradient_err):

            gradient_text = f"{format_sci_err(gradient,gradient_err, decimals=3)}"

        else:

            gradient_text = "Fit unavailable"

        legend_label = data["label"] + f", m = {gradient_text} {m_unit}" + f", R² = {r_squared:.4f}"

        plt.plot([], [], color=colour, marker="x", linestyle="--", label=legend_label)

    # --------------------------------------------------------
    # Axis formatting
    # --------------------------------------------------------
    # Format frequency axes from Hz to kHz (visual only)
        if param == "r2":
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda y, _: f"{y / 1000:g}")
            )
            ylabel = r"$f_{\min}$ (kHz)"

    plt.ylabel(ylabel)
    plt.xlabel(xlabel)

    plt.title(title)

    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.legend(fontsize=7)

    plt.tight_layout()

    # --------------------------------------------------------
    # Save / show
    # --------------------------------------------------------

    if save_data:

        plt.savefig(os.path.join(save_location, filename), dpi=300)

    if show_plots:
        plt.show()
    else:
        plt.close()


# ============================================================
# GENERATE PLOTS
# ============================================================

print("Generating plots...")


# ------------------------------------------------------------
# 1. Fixed R1 values for C = 1000pF (varying R2)
# ------------------------------------------------------------

r1_values = set(p["r1"] for p in parsed_info if p["c"] == "1000pf" and p["r1"] is not None)

for r1 in r1_values:

    idx_list = [i for i, p in enumerate(parsed_info) if p["c"] == "1000pf" and p["r1"] == r1]

    if idx_list:

        create_and_save_plot(
            idx_list,
            f"VCO Response ($C=1$ nF, $R_1=${format_val(r1)})",
            "r2",
            f"Fixed_R1_{r1}_C_1000pF.svg",
        )


# ------------------------------------------------------------
# 2. Fixed R2 values for C = 1000pF (varying R1)
# ------------------------------------------------------------

r2_values = set(p["r2"] for p in parsed_info if p["c"] == "1000pf" and p["r2"] is not None)

for r2 in r2_values:

    idx_list = [i for i, p in enumerate(parsed_info) if p["c"] == "1000pf" and p["r2"] == r2]

    if idx_list:

        create_and_save_plot(
            idx_list,
            f"VCO Response ($C=1$ nF, $R_2=${format_val(r2)})",
            "r1",
            f"Fixed_R2_{r2}_C_1000pF.svg",
        )


# ------------------------------------------------------------
# 3. All unique R1, R2 combinations (varying C)
# ------------------------------------------------------------

r1_r2_pairs = set(
    (p["r1"], p["r2"]) for p in parsed_info if p["r1"] is not None and p["r2"] is not None
)

for r1, r2 in r1_r2_pairs:

    idx_list = [i for i, p in enumerate(parsed_info) if p["r1"] == r1 and p["r2"] == r2]

    # Only plot if there is more than one capacitance
    if len(idx_list) > 1:

        create_and_save_plot(
            idx_list,
            f"VCO Response ($R_1=${format_val(r1)}, $R_2=${format_val(r2)})",
            "c",
            f"Fixed_R1_{r1}_R2_{r2}_Varying_C.svg",
            fixed_param=[data_to_val(r1), data_to_val(r2)],
        )


# ============================================================
# COMBINED PLOTS
# ============================================================


# ------------------------------------------------------------
# 1. KO against 1/R1
# ------------------------------------------------------------

create_combined_plot(
    param="r1",
    ylabel=r"$K_O$ (Hz/V)",
    xlabel=r"$1/R_1$ ($\Omega^{-1}$)",
    title=r"$K_O$ vs $1/R_1$",
    filename="Combined_KO_vs_invR1.svg",
)


# ------------------------------------------------------------
# 2. Minimum frequency against 1/R2
# ------------------------------------------------------------

create_combined_plot(
    param="r2",
    ylabel=r"$f_{\min}$ (Hz)",
    xlabel=r"$1/R_2$ ($\Omega^{-1}$)",
    title=r"$f_{\min}$ vs $1/R_2$",
    filename="Combined_fmin_vs_invR2.svg",
)


# ------------------------------------------------------------
# 3. Inverse KO against capacitance
# ------------------------------------------------------------

create_combined_plot(
    param="c",
    ylabel=r"$1/K_O$ (V/Hz)",
    xlabel=r"$C$ (F)",
    title=r"$1/K_O$ vs $C$",
    filename="Combined_invKO_vs_C.svg",
)

# ------------------------------------------------------------
# 4. Inverse minimum frequency against capacitance
# ------------------------------------------------------------
show_plots = True
save_data=True
create_combined_plot(
    param="fmin_inv_c",
    ylabel=r"$f_{\min}$ (Hz)",
    xlabel=r"$1/C$ (F$^{-1}$)",
    title=r"$f_{\min}$ vs $1/C$",
    filename="Combined_fmin_vs_invC.svg",
)
# ============================================================
# FINISHED
# ============================================================

print("All plots completed.")

if save_data:
    print(f"Plots saved to: {save_location}")
else:
    print("save_data is False, so plots were not saved.")
