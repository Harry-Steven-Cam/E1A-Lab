'''
First thing if not using the class laptops - install Python from
    the Python website (not the Windows store)
Next thing - install the right SDK from the PicoScope site
-----------------
Module not found?  Try this from the Windows Command prompt...
python -m pip install -U matplotlib
python -m pip install -U picosdk
then probably restart your code editor (e.g. VS Code)
(the latter needs you to have installed the right SDK from the PicoScope site)
'''

import time

import matplotlib.pyplot as plt
import os
import datetime
import numpy as np

import ctypes
from ctypes import byref,c_byte,c_int16,c_int32,c_char

from picosdk.ps2000a import ps2000a

print("Hello modules!")

time.sleep(3)

