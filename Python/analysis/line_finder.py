from scipy.optimize import curve_fit
import numpy as np
import pandas as pd


def linear_model(x, m, c):
    return m * x + c


"""    
# p: array of coefficients
# V: covariance matrix
if len(error_data) == len(x):
p, V = np.polyfit(x, y, deg=order, w=1 / error_data, cov=True)
else:
p, V = np.polyfit(x, y, deg=order, cov=True)
# Calculate the standard error for each coefficient
errors = np.sqrt(np.diag(V)) #not great for data
    """


def get_poly_fit(x, y, order=1, error_data=None, steps=100):
    if error_data is None:
        err_data = np.full_like(x, 0)
        popt, pcov = curve_fit(linear_model, x, y)
    else:
        err_data = error_data
        popt, pcov = curve_fit(linear_model, x, y, sigma=err_data, absolute_sigma=True)
    x_fit = np.linspace(min(x), max(x), steps)
    if order == 1:
        m = popt[0]
        c = popt[1]
        m_err = np.sqrt(pcov[0, 0])
        c_err = np.sqrt(pcov[1, 1])
        return x_fit, linear_model(x_fit, m, c), [m, c], [m_err, c_err]


def get_voltage_errors(voltage_data, voltage_window=10.0, resolution_bits=8):
    # Calculate the Least Significant Bit (LSB), 2x voltage window as picoscope def
    lsb = voltage_window * 2 / (2**resolution_bits)
    """
    delta V = Vrange/2^8bits, so max res is 1/2 deltaV
    P(x)=1/dV or any point in the bin--> so variance = int +1/2dv to -1/2dV x^2p(x) dx etc 
    to give sigma V below
    """
    sigma_v = lsb / np.sqrt(12)
    # create an array of constant errors matching the dimensions of your input data
    voltage_errors = np.full_like(voltage_data, fill_value=sigma_v, dtype=float)
    return voltage_errors


def finding_slope(x, y, lower_percentile=0.1, upper_percentile=0.9, error_data=None):
    val_max = max(y)
    val_min = min(y)
    val_range = val_max - val_min
    # looks at small sections of gradient to check if the are above low cut
    low_cut = val_min + lower_percentile * val_range  # goes .2 up slop
    high_cut = val_min + upper_percentile * val_range  # goes .8 up slope

    def find_closest_index(data, target):
        diff = np.absolute(target - data[0])
        data_point = data[0]  # for flat line cases
        for val in data:
            if np.absolute(target - val) < diff:
                diff = np.absolute(target - val)
                data_point = val

        return data.tolist().index(data_point)

    upper_index = find_closest_index(y, high_cut)
    lower_index = find_closest_index(y, low_cut)
    x_rising = x[lower_index:upper_index]
    y_rising = y[lower_index:upper_index]
    if y[upper_index] - y[lower_index] < 1e-8:  # flat line case
        gradient = 0
        error = [0, 0]
        x_fit = x
        y_fit = y
    elif x[upper_index] - x[lower_index] == 0:
        print("infinite gradient")
    else:
        x_fit, y_fit, gradient, c, error = get_poly_fit(
            x_rising, y_rising, error_data=error_data[lower_index:upper_index], order=1
        )

    return gradient, error[0], x_fit, y_fit
