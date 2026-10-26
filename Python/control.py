"""
Control program for taking data using the 4-channel PicoScope 2406B
-------------------------------
NOTE!  Connect the AWG to Channel A - the program needs a trigger!
-------------------------------
This program is just an example, using the functions in "pll_ps2000a.py"
        to interface with the PicoScope.
You'll need the "import" statement and you'll need to open and close the PicoScope
        but otherwise the programming is up to you.
Take a look in "pll_ps2000a.py" and/or the class manual to see what parameters you
         may/must pass to those functions.
You won't have to edit "pll_ps2000a.py" at all for this project, but you are welcome
        to do so - at your own risk.
Keep backups of Python scripts and data as you go!
"""

import pll_ps2000a as picoscope  # Import the other file so you can use its functions

# If you've put it in a sub-folder "example_folder",
# 	change this to "import example_folder.pll_ps2000a"

picoscope.picoscope_open()  # First thing - open the unit, last thing - close it!

picoscope.scope_prepare(  # Sets up the measurement - see class manual for options
    capture_time=0.005,
    samples=1000,
    a_range=10,
    a_probe="x1",
    trigger_channel="A",
    trigger_direction="rising",
    trigger_level=1,
    trigger_pre_percent=20,
)

picoscope.awg(  # An example of an AWG signal generator - see class manual
    waveform="square",
    peak_to_peak=2,
    offset=1,
    frequency=1e3,
)

continue_capture = (
    picoscope.scope_monitor()
)  # Optional - watch the waveform first before starting
if not continue_capture:  # If you closed the window (by hitting the 'x'), abandon now
    picoscope.picoscope_close()
    quit()

time, volts = picoscope.scope_capture()  # Reads the data into arrays

make_plot = True  # Making it easy to select options
save_data = False

if save_data:
    picoscope.quick_save(  # Saves data to file
        time=time,
        volts=volts,
        file_path=f"./data/#.csv",
    )

if make_plot:  # Plots the trace and (optionally) saves the pic
    picoscope.quick_plot(
        time=time,
        volts=volts,
        file_path=f"./data/#.png",  # file_path=f'./data/#.png', for example (or 'bmp', 'jpg' etc)
    )

picoscope.picoscope_close()  # Finish by closing the unit
