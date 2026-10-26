import pll_ps2000a as picoscope
import Python.old.arduino as arduino

picoscope.picoscope_open()

arduino.arduino_open()

'''
Prepare the PicoScope for capturing the signals (see lab manual for
details of these, and other, parameters).  This set
of parameters is likely to be approximately correct for your needs,
but you may need to change "capture_time" and/or "samples".
'''
picoscope.scope_prepare(
	capture_time=0.005,	# Traces will be captured over this time period (in seconds).
	samples=5000,	# Number of samples to capture over the capture_time period.
	a_range=10,	# Voltage range for channel A (in volts).
	a_probe="x1",	# Probe attenuation for channel A (x1 is the default).
	b_range=10,
	c_range=10,
	d_range=10,
	a_name='SIG_IN',	# Useful channel names for exported data and/or plot legend.
	b_name='COMP',
	c_name='Trig',
	d_name='PC',
	trigger_channel='C',
	trigger_direction='f',
	trigger_level=2.5,
	trigger_pre_percent=10,
	verbose=False,
	)

'''
Here we provide the three parameters needed for a pair of square waveforms
with a constant phase difference between them.
In practice, you are likely to want to loop through a range of values,
and maybe perform "live" analysis on the data obtained.
'''
t=0.001	# period of pulses (NOT pulse width!) in seconds
p=0.25	# phase difference in fraction of a period (+0.25 => +90 degrees or +π/2 radians)
n=10	# number of cycles per pulse chain.

'''
Prepare the command string to send to the Arduino.
The syntax is very forgiving, and not all of the parameters need to be included.  The Arduino will ignore any parameters that it does not recognize.
'''
command=f"t={t} p={p} n={n}"
print(command, 'this is the command')

'''
Now tell the Arduino what to do:
First the "prepare" command breaks it out of "run mode" and gets it ready to
listen to the command.
(This is something of a workaround, as the Arduino will unpredictably "lose"
characters sent to it if it is still in "run mode" when the command is sent.
The "prepare" command is sent repeatedly until the Arduino responds
appropriately; the arduino_prepare() function then exits in the knowledge
that "run mode" has been exited - see Arduino code for how it is implemented.)
'''
arduino.arduino_prepare()
'''
Next, send the command to the Arduino, and read back the response to confirm.
This bit is necessary!  Skipping it will probably result in your capturing an
"old" waveform.
'''
arduino.arduino_write(command)
response=arduino.arduino_read()

print(response)

'''
At this point, the Arduino should be generating the requested waveform,
and the PicoScope is ready to capture it.
'''

'''
scope_monitor() will display a live plot of the signals on the PicoScope before capture
(you would click on that plot to continue).
It is optional - remove it or comment it out if it is annoying you,
and particularly if you are capturing a large number of traces.
'''
picoscope.scope_monitor()

'''
Capture the signals.  Consider whether you want to do any analysis on the data
now; you might even not need to save the full waveform data at all!
'''
(time,volts)=picoscope.scope_capture()

picoscope.quick_plot(	# Optional if you have no need of graphic output.
	time,	# Necessary - don't edit
	volts,	# Necessary - don't edit
	title=f"ϕ = {(p*2):+.3f} π, t = {t} s",	# Plot title (optional).
	display=True,	# Show a plot window (which you will need to close manually).
	legend=False,	# Show a legend on the plot.
	verbose=False,
	file_path=f"./images/phase PC2 {command}.png",	# Save plot image to this location (optional).
	)

picoscope.quick_save(	# Optional if you have no need of data output.
	time,	# Necessary - don't edit
	volts,	# Necessary - don't edit
	verbose=False,
	file_path=f"./data/phase PC2 {command}.csv",	# Save data to this location.
	)


#Cycle through phase diffrences, mean voltage against phase diffrenece


picoscope.picoscope_close()

arduino.arduino_close()


