from scipy.optimize import curve_fit
import numpy as np

def get_poly_fit(x, y, order,steps=100):
    # p: array of coefficients
    # V: covariance matrix
    p, V = np.polyfit(x, y, deg=order, cov=True)
    # Calculate the standard error for each coefficient
    errors = np.sqrt(np.diag(V))
    if order == 1:
        x_fit = np.linspace(min(x),max(x),steps)
        return x_fit, (p[0]*x_fit+p[1]), errors
    return p, errors