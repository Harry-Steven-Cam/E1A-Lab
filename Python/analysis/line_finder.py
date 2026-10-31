from scipy.optimize import curve_fit
import numpy as np
import pandas as pd

def get_poly_fit(x, y, order,error_data=None,steps=100):
    # p: array of coefficients
    # V: covariance matrix
    p, V = np.polyfit(x, y, deg=order,w=1/error_data, cov=True)
    # Calculate the standard error for each coefficient
    errors = np.sqrt(np.diag(V))
    if order == 1:
        x_fit = np.linspace(min(x),max(x),steps)
        return x_fit, (p[0]*x_fit+p[1]),p[0],p[1], errors
    return p, errors

def get_voltage_errors(voltage_data, voltage_window=10.0, resolution_bits=8):
    #Calculate the Least Significant Bit (LSB), 2x voltage window as picoscope def
    lsb = voltage_window*2 / (2 ** resolution_bits)
    '''
    delta V = Vrange/2^8bits, so max res is 1/2 deltaV
    P(x)=1/dV or any point in the bin--> so variance = int +1/2dv to -1/2dV x^2p(x) dx etc 
    to give sigma V below
    '''
    sigma_v = lsb / np.sqrt(12)
    #create an array of constant errors matching the dimensions of your input data
    voltage_errors = np.full_like(voltage_data, fill_value=sigma_v, dtype=float)
    return voltage_errors