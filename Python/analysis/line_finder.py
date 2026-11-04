from scipy.optimize import curve_fit
from scipy import odr
import numpy as np
import pandas as pd


def linear_model(x, m, c):
    return m * x + c

def odr_linear_model(B, x):
    m, c = B
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


def get_poly_fit(x, y, order=1, error_data=None,error_x=None,error_y=None, steps=100):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if error_x is not None and error_y is not None:
        x_fit,y_fit,p,p_err = get_odr_fit(x, y, error_x, error_y, steps=steps) #xfit,yfit,m,m_err
        return x_fit, y_fit, p, p_err
    if error_data is None:
        p0 = np.polyfit(x, y, 1)
        popt, pcov = curve_fit(linear_model, x, y, p0=p0)
    else:
        err_data = error_data
        popt, pcov = curve_fit(linear_model, x, y, sigma=err_data, absolute_sigma=True)
    
    if order == 1:
        m = popt[0]
        c = popt[1]
        m_err = np.sqrt(pcov[0, 0])
        c_err = np.sqrt(pcov[1, 1])
        x_fit = np.linspace(min(x), max(x), steps)

        y_pred = linear_model(x, m, c)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return x_fit, linear_model(x_fit, m, c), [m, c], [m_err, c_err, r_squared]
    else:
        p = np.polyfit(x,y,order)
        x_fit = np.linspace(min(x), max(x), steps)
        y_fit = np.poly1d(p)
        return x_fit,y_fit(x_fit)


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


def finding_slope(
    x, y, lower_percentile=0.1, upper_percentile=0.95, error_x=None, error_y=None
):
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
        p = [0, 0]
        p_err = [0, 0]
        x_fit = x
        y_fit = y
    elif x[upper_index] - x[lower_index] == 0:
        print("infinite gradient")
    else:
        x_fit, y_fit, p, p_err = get_poly_fit(
            x_rising,
            y_rising,
            error_y=error_y[lower_index:upper_index],
            error_x=error_x[lower_index:upper_index],
            order=1,
        )

    return x_fit, y_fit, p[0], p_err[0]  # returns xfit,yfit,m,m_err


def get_odr_fit(x, y, x_err, y_err, steps=100):
    # Ensure inputs are numpy arrays
    x, y = np.array(x), np.array(y)
    x_err, y_err = np.array(x_err), np.array(y_err)

    # Prevent absolute zero errors from causing division-by-zero crashes
    x_err = np.where(x_err == 0, 1e-10, x_err)
    y_err = np.where(y_err == 0, 1e-10, y_err)

    # 2. Package the data with its dual errors
    data = odr.RealData(x, y, sx=x_err, sy=y_err)

    # 3. Instantiate the ODR model
    model = odr.Model(odr_linear_model)

    # 4. Provide a rough initial guess for the algorithm
    guess_m = (y[-1] - y[0]) / (x[-1] - x[0]) if (x[-1] - x[0]) != 0 else 1.0
    guess_c = y[0] - guess_m * x[0]

    # 5. Set up and run the Orthogonal Distance Regression
    odr_obj = odr.ODR(data, model, beta0=[guess_m, guess_c])
    output = odr_obj.run()

    # Extract optimized parameters and their standard errors
    p = output.beta  # [m, c]
    p_err = output.sd_beta  # [m_err, c_err]

    # Generate the smooth line array for plotting
    x_fit = np.linspace(min(x), max(x), steps)
    y_fit = odr_linear_model(p, x_fit)

    return x_fit, y_fit, p, p_err


def freqFinder(voltage, time):
    threshold = (np.max(voltage) + np.min(voltage)) / 2
    peaktopeak = np.max(voltage) - np.min(voltage)
    edges = np.where((voltage[:-1] < threshold) & (voltage[1:] >= threshold))[0]

    if len(edges) >= 2:  # and peaktopeak>.8:
        edge_times = time[edges]
        periods = np.diff(edge_times)
        # Ignore invalid periods
        periods = periods[periods > 0]
        if len(periods) > 0:
            period = np.mean(periods)
            freq = 1.0 / period
        else:
            freq = 0
            # print("Invalid periods")
    else:
        freq = 0
        # print("Not enough rising edges detected")
    return freq