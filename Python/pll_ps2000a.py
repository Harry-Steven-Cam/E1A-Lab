'''
-----------------
(c) A C Irvine (aci20@cam.ac.uk) 2025
Apologies for the author's obsessive dislike of non-essential white space.

This file is a library of functions which MOST users WILL NOT NEED TO EDIT!
If you choose to do so, beware!  And keep a (working) backup.
-----------------
'''

'''
First thing is to import standard modules which will be used.
Most should be present in any python installation, but "picosdk" will not usually,
	and must be downloaded and installed if not using the Teaching Lab laptops.
It is the only component needed to run your PicoScope; the picosdk-python-wrappers module
	at GitHub is NOT required here.
Find PicoSDK at https://www.picotech.com/downloads and be sure to choose the correct SDK
	for the PicoScope model used.

Imports below:
	"matplotlib.pyplot" is a widely-used plotting module which is used as a live monitor
		and to display captured data.
	"os" is a filing system utility which (here) helps correct unspecified file paths
		when saving data.
	"datetime" is used to create a timestamp which (optionally) is inserted into file names.
	"numpy" handles data and mathematics in a more efficient way.
	"ctypes" creates a link between python and C++ variables, again with efficiency as the intent.
	"picosdk" (see above) contains a library of commands for accessing the PicoScope
		and retrieving data - all of the ps2000a.ps200aXXXXX() calls require it.
'''

import matplotlib.pyplot as plt
import os
import datetime
import numpy as np

import ctypes
from ctypes import byref,c_byte,c_int16,c_int32,c_char

from picosdk.ps2000a import ps2000a
from picosdk.functions import assert_pico_ok

'''
The section below defines global variables by declaring them outside the functions
	(though placing them within this module to avoid clutter in the control script).
This python module has multiple functions to be called in turn, and frequently the
	subroutines need to work with the same version of a variable (using the command
	'global' within the function to specify that the global version is to be used).
	"handle", for example, identifies the hardware (PicoScope) in use, and so
	needs to be global.

Global variables:
	"handle" - the (PicoScope) hardware identifier.
	"samples_total" - number of samples per sweep.  
	"time_interval" - the interval between points calculated by PicoSDK for a given timebase
		setting.  This is hardware-dictated - it is the actual value for the sweep, and may
		differ from the value intended by the user.
	"trigger_samples_pre" - for the capture and readout phase, the user specifies a percentage
		of the trace to be captured before a trigger, and this variable is calculated
		using "samples_total".
	"trigger_samples_post" - similar to "trigger_samples_pre", but after the trigger.
	"timebase_number" - a 32-bit number used to calculate or produce time intervals between
		points via an algorithm.  Will dictate the maximum number of samples too.
		See manual for specifics.

	"status" - a dictionary containing the outcomes of all calls to the PicoSDK functions.
		Values will be zero if successful and an error thrown up if not.  Not utilised here.
	"overflow" - one 'False' returned per channel unless that channel goes outside its
		voltage limits, in which case that value is 'True'.  Used here to produce
		warning messages.

	"channel_name" - a list which gives channel numbers 0-3 an alphabetic equivalent,
		A-D respectively.
	"waveform_colours" - colours of traces for the four input channels.  Editable!

	"channel_range_id" - four-item list of numbers, one per input channel, corresponding to
		one of the available hardware voltage ranges, or 'False' if the channel is to be disabled.
	"channel_range_maxvolts" - the list of voltages corresponding to the range numbers
		in "channel_range_id".  Used to convert ADC numbers to volts.
	"channel_attenuation" - a list of integers which store the attenuation factor of probes used.

	"max_adc" - the ADC is signed 32-bit, and a voltage signal reaches this value at
		maximum voltage.  Used for calculating voltage from ADC numbers.

	"picoscope_variant" - the model of PicoScope in use, obtained from a PicoSDK query.
		Used only for open/closed status messages.

	"monitor_closed" - flags whether the continually-updating monitor window is closed.
	"continue_capture" - returns a value which indicates whether to keep the monitor updating.

	"now_time" - records datetime.datetime.now() when the data capture commences, for use
		in timestamps in file names.
'''

handle=ctypes.c_int16(0)
samples_total=ctypes.c_int32(0)
time_interval=ctypes.c_float(0)
trigger_samples_pre=ctypes.c_int32(0)
trigger_samples_post=ctypes.c_int32(0)
timebase_number=c_int16(0)

status={}
overflow=(False,False,False,False)

channel_name=['A','B','C','D']
waveform_colour=['#0060A8','#EB0028','#00953E','#C29A1F']

channel_range_id=[False]*4
channel_range_maxvolts=[False]*4
channel_attenuation=[1,1,1,1]

max_adc=c_int16(32767)

picoscope_variant=''

monitor_closed=False
continue_capture=True

now_time=0

'''
picoscope_open()
----------------
This is fairly self-explantory.  The PicoSDK function ps2000aOpenUnit opens the attached
PicoScope and assigns a "handle" (or identifier code) to it.  The "ctypes" construct enables
Python to access C-language variables such that the PicoScope hardware may be accessed and used.
The "byref" bit, a "pass-by-reference" allows functions to return variables when executed
("ctypes.byref(handle)" sets the variable "handle" to the unit's identifier; later on,
"byref(c_int16(0))" returns an integer (in C) for string length (which we don't use).
The function ps2000aGetUnitInfo then obtains a set of system information data, of which we only
use number 3, the variant info, for nothing more useful than an "Opening PicoScope XXXX" message
in the Python terminal.
The important thing is that we've opened the unit and found its handle so we can address it again;
we leave it open until everything is done, as the opening and closing of a PicoScope
is a bit ponderous.
'''
def picoscope_open():

	# Open the device

	status["OpenUnit"]=ps2000a.ps2000aOpenUnit(ctypes.byref(handle),None)
	assert_pico_ok(status["OpenUnit"])

	# Finding device information ("unit_info_types" is included for information only).  We need "picoscope_variant" when closing, so it's made global.

	unit_info_types={
		0:"Driver Version",
		1:"USB Version",
		2:"Hardware Version",
		3:"Variant Info",
		4:"Batch and Serial",
		5:"Calibration Date",
		6:"Kernel Driver Version",
		}

	unit_info_values={}
	for unit_info_id in unit_info_types.keys():
		buffer=(c_char*32)()
		status["UnitInfo"]=ps2000a.ps2000aGetUnitInfo(
			handle.value,
			buffer,
			len(buffer),
			byref(c_int16(0)),  # string length
			unit_info_id
			)
		assert_pico_ok(status["UnitInfo"])
		unit_info_values[unit_info_id]=str(bytes(buffer).decode('utf-8')).replace('\x00','')

	global picoscope_variant
	picoscope_variant=unit_info_values[3]
	print(f"Opening PicoScope {picoscope_variant}...")

	return False

'''
scope_prepare()
---------------
There are so many things we need to tell the PicoScope before acquiring a trace; which channels
	we're using, what voltage range, triggering conditions and more.  However, when calling
	"scope_prepare", it is really handy to have default values, such that we often call it with
	very few parameters.  "def scope_prepare()" is a long function, but is pretty simple -
	it just needs to tidy up rather a lot of input parameters.  For the sake of sanity, we call
	the function using named variables.  If a variable is omitted, its default (below) is taken.
	For user-friendliness, there is often a set of possible string values which do the same thing -
	'C', 'c', '2' and 2 all refer to the same input channel/terminal, for instance.
'''
def scope_prepare(					# Default values shown.
	capture_time=0.1,				# Requested total sweep time in seconds.
	samples=1000,					# Total number of samples per channel.
	a_range=None,					# Range of channel A in volts.  Unless non-zero, the channel is disabled.  May adjust to the nearest higher hardware range.
	b_range=None,
	c_range=None,
	d_range=None,
	a_probe='x1',					# Attenuation of Channel A probe.
	b_probe='x1',
	c_probe='x1',
	d_probe='x1',
	a_coupling='dc',				# coupling of channel A (AC or DC)
	b_coupling='dc',
	c_coupling='dc',
	d_coupling='dc',
	a_name="A",						# Name of channel A, used in file names and plot legends.
	b_name="B",
	c_name="C",
	d_name="D",
	trigger_channel=None,			# Channel to use for triggering.  If None, trigger is disabled.
	trigger_level=0,				# Trigger level in volts.
	trigger_direction='rising',		# Direction of trigger edge; rising or falling.
	trigger_delay_samples=0,		# Delay (in number of samples) after the trigger is received before starting the capture.
	trigger_pre_percent=0,			# Percentage of samples recorded before the trigger.
	trigger_timeout=0,				# Timeout in milliseconds before automatic trigger.  If zero, device will wait indefinitely.
	verbose=True,					# If True, print information about the process.
	):

	global nsamples,channel_range_id,channel_print_name,channel_range_maxvolts,channel_attenuation,handle,samples_total,timebase_number,max_adc

# Number of samples must be a positive integer.

	samples_total.value=int(samples)
	if(samples_total.value<1):
		samples_total.value=1

# Get appropriate values for channel parameters (ID, attenuation, coupling)

	channel_number={'A':0,'B':1,'C':2,'D':3,'a':0,'b':1,'c':2,'d':3,'0':0,'1':1,'2':2,'3':3,0:0,1:1,2:2,3:3}
	channel_range=[a_range,b_range,c_range,d_range]
	channel_print_name=[a_name,b_name,c_name,d_name]
	channel_count=0
	for element in channel_range:
		if element is not None:
			channel_count+=1
	channel_probe=[a_probe,b_probe,c_probe,d_probe]
	channel_attenuation=channel_probe.copy()
	for channel in range(0,4):
		if channel_attenuation[channel]=='' or channel_attenuation[channel] is None:
			channel_attenuation[channel]='x1'
		channel_attenuation[channel]=channel_attenuation[channel].strip("xX ")
		try:
			channel_attenuation[channel]=float(channel_attenuation[channel])
		except:
			channel_attenuation[channel]=1
			print(f"Channel {channel_name[channel]} probe setting ('{channel_probe[channel]}') invalid. Setting to x1.")
	channel_coupling={'':True,'dc':True,'d.c.':True,'DC':True,'D.C.':True,
						'ac':False,'a.c.':False,'AC':False,'A.C.':False}
	channel_dc=[channel_coupling[a_coupling],channel_coupling[b_coupling],channel_coupling[c_coupling],channel_coupling[d_coupling]]

# Calculate channel ranges from driver dictionary

	range_v={}
	for v_range in ps2000a.PS2000A_RANGE.keys():
		x=v_range.split('_')
		if x[1][-2:] == 'MV':
			if int(x[1][:len(x[1])-2])>10:		# PicoScope 2406B has a 20 mV range, but not 10 mV.
				range_v[int(x[1][:len(x[1])-2])]=ps2000a.PS2000A_RANGE[v_range]
		elif x[1][-1:] == 'V':
			range_v[int(x[1][:len(x[1])-1])*1000]=ps2000a.PS2000A_RANGE[v_range]

	ranges_available=list(range_v.keys())
	ranges_available.sort(reverse=True)

	channel_range_id=[False]*4
	channel_range_maxvolts=[False]*4
	for channel in range(0,4):
		if channel_range[channel]:
			for comparison_range in ranges_available:
				if comparison_range>=channel_range[channel]*1000/channel_attenuation[channel]:
					channel_range_maxvolts[channel]=comparison_range/1000
					channel_range_id[channel]=range_v[comparison_range]
				else:
					break

# Trigger setup - many ways to define rising and falling edge.

	direction_id={0:0,1:1,
			'rising':0,'falling':1,'RISING':0,'FALLING':1,'Rising':0,'Falling':1,'R':0,'F':1,'r':0,'f':1,
			'up':0,'down':1,'UP':0,'DOWN':1,'Up':0,'Down':1,'U':0,'D':1,'u':0,'d':1}

# Setting up the trigger channel and direction, and ensuring sane values for the trigger timings.

	trigger_adc=0
	try:
		trigger_channel=channel_number[trigger_channel]
		if channel_range_maxvolts[trigger_channel]:
			trigger_adc=int(trigger_level/channel_attenuation[trigger_channel]/channel_range_maxvolts[trigger_channel]*max_adc.value)
	except:
		trigger_channel=''
	try:
		trigger_direction_id=direction_id[trigger_direction]
	except:
		trigger_direction_id=0 
	if trigger_pre_percent<0:
		trigger_pre_percent=0
		if verbose:
			print(f"Warning: trigger_pre_percent ({trigger_pre_percent}) must be >= 0. Setting to 0.")
	if trigger_pre_percent>100:
		trigger_pre_percent=100
		if verbose:
			print(f"Warning: trigger_pre_percent ({trigger_pre_percent}) must be <= 100. Setting to 100.")
	if trigger_delay_samples<0:
		if verbose:
			print(f"Warning: trigger_delay_samples ({trigger_delay_samples}) must be >= 0. Setting to 0.")
		trigger_delay_samples=0

# Setting the channel ranges

	for channel in range(0,4):
		if channel_range[channel]:		# Setting only enabled channels
			outval=f"SetChannel{channel_name[channel]}"
			status[outval]=ps2000a.ps2000aSetChannel(
				handle.value,
				channel,
				1,							# enabled
				channel_dc[channel],
				channel_range_id[channel],
				0,							# Analogue offset - not implemented here.
			)
			assert_pico_ok(status[f"SetChannel{channel_name[channel]}"])
			if verbose:
				print(f"Channel {channel_name[channel]}: range {channel_range_maxvolts[channel]*channel_attenuation[channel]} V, probe attenuation {channel_attenuation[channel]}x, coupling {'DC' if channel_dc[channel] else 'AC'}.")
		else:		# Non-enabled channels now - must be set anyway
			outval=f"SetChannel{channel_name[channel]}"
			status[outval]=ps2000a.ps2000aSetChannel(
				handle.value,
				channel,
				0,				# disabled
				False,
				0,
				0
			)
			if verbose:
				print(f"Channel {channel_name[channel]}: disabled.")
			assert_pico_ok(status[f"SetChannel{channel_name[channel]}"])

# Setting the trigger

	if trigger_channel!='': # If trigger is enabled
		status["SetTrigger"]=ps2000a.ps2000aSetSimpleTrigger(
			handle.value,
			True,					# enabled
			trigger_channel,		# source (A=0, B=1)
			trigger_adc,			# threshold in adc numbers
			trigger_direction_id,	# direction (0=rising, 1=falling)
			trigger_delay_samples,	# delay (samples, >=0)
			trigger_timeout,		# auto trigger time_ms
		)
		if verbose:
			print(f"Trigger: channel {channel_name[trigger_channel]}, level {trigger_level} V ({'rising' if trigger_direction_id==0 else 'falling'} edge),{f' delay {trigger_delay_samples} samples, ' if trigger_delay_samples>0 else ''} {f'timeout {trigger_timeout} ms' if trigger_timeout>0 else 'timeout disabled'}.")
		assert_pico_ok(status["SetTrigger"])
	else:		# If trigger is disabled
		status["SetTrigger"]=ps2000a.ps2000aSetSimpleTrigger(
			handle.value,
			False,					# disabled
			0,
			0,
			0,
			0,
			0,
		)
		if verbose:
			print("Trigger: disabled.")

# Setting the timebase; the picoscope has many possible timebases (intervals between data samples), but these are not arbitrary.
# This particular picoscope has a readily-calculated timebase number except for the three quickest - see manual.

	max_samples=ctypes.c_int32(0)

	time_interval_specified=capture_time/samples_total.value
	if verbose:
		print(f"Requested capture time: {(capture_time):.6g} s, samples: {samples_total.value}, time interval: {(time_interval_specified):.6g} s/sample.")
	global timebase_number
	if time_interval_specified*125000000==int(time_interval_specified*125000000):
		timebase_number=int(time_interval_specified*125000000)+2
	else:
		timebase_number=int(time_interval_specified*125000000)+3
	if time_interval_specified<=4e-9:
		timebase_number=2
	if time_interval_specified<=2e-9 and channel_count<=2:
		timebase_number=1
	if time_interval_specified<=1e-9 and channel_count==1:
		timebase_number=0

# Now we query the timebase number we've calculated, and get back its time interval and maximum samples.

	status["GetTimebase"]=ps2000a.ps2000aGetTimebase2(
		handle.value,
		timebase_number,		# timebase
		0,						# no_of_samples - zero here to avoid error if > max.
		byref(time_interval),	# time_interval
		0,						# oversample, not available
		byref(max_samples),		# max_samples
		0,						# segment index, not implemented
	)
	assert_pico_ok(status["GetTimebase"])

# If we've specified more samples than the timebase can manage, we have to cut back.

	if samples_total.value>max_samples.value:
		if verbose:
			print(f"Warning: requested samples ({samples_total.value}) exceeds the maximum ({max_samples.value}) for this timebase.  The number of samples will be set to {max_samples.value}, new duration of the capture {(max_samples.value*time_interval.value*1e-9):.6g} s.")
		samples_total.value=max_samples.value
		if verbose:
			print(f"Samples set to {samples_total.value}.")

# Setting the number of samples before and after the trigger from the percentacge specified,

	trigger_samples_pre.value=int(samples_total.value*trigger_pre_percent/100)
	trigger_samples_post.value=samples_total.value-trigger_samples_pre.value

	if verbose:
		print(f"Sweep: Timebase {timebase_number}, {samples_total.value} samples (max: {max_samples.value}), interval: {(time_interval.value*1e-9):.6g} s, total time: {(time_interval.value*samples_total.value*1e-9):.6g} s.")

'''
scope_capture()
---------------
This function executes the trace capture and retrieves the data.
'''
def scope_capture(
	):
	global channel_range_id
	global overflow
	global now_time

	now_time=datetime.datetime.now()	# useful for timestamps on files.

	capture_time_ms=c_int32(0)			# not so useful.  Value returned by the next call.

# Run the block

	status["RunBlock"]=ps2000a.ps2000aRunBlock(
		handle.value,
		trigger_samples_pre.value,		# no_of_pre_trigger_samples
		trigger_samples_post.value,		# no_of_post_trigger_samples
		timebase_number,
		0,								# not used
		byref(capture_time_ms),
		0,								# not implemented
		None,							# not implemented
		None,							# not implemented
		)
	assert_pico_ok(status["RunBlock"])

# Wait until the unit is ready to continue.

	check=ctypes.c_int16(0)
	ready=ctypes.c_int16(0)

	while ready.value==check.value:
		status["IsReady"]=ps2000a.ps2000aIsReady(
			handle.value,
			ctypes.byref(ready),
			)

# Create buffers to put the data into, of the appropriate size.

	buffer_a=(ctypes.c_int16*samples_total.value)()
	buffer_b=(ctypes.c_int16*samples_total.value)()
	buffer_c=(ctypes.c_int16*samples_total.value)()
	buffer_d=(ctypes.c_int16*samples_total.value)()
	buffers=[buffer_a,buffer_b,buffer_c,buffer_d]

	overflow_raw=c_byte(0)

	for channel in range(0,4):
		if channel_range_id[channel]:
			status[f"SetDataBuffer{channel_name[channel]}"]=ps2000a.ps2000aSetDataBuffer(
				handle.value,						# handle
				channel,							# source (A=0, B=1, C=2, D=3)
				ctypes.byref(buffers[channel]),		# pointer to buffer
				samples_total.value,				# buffer length
				0,									# segment index, not implemented
				0,									# ratio mode (downsampling) - not implemented yet, but interesting
				)
			assert_pico_ok(status[f"SetDataBuffer{channel_name[channel]}"])

# Retrieve the data from the unit

	samples_found=c_int32(samples_total.value)
	status["GetValues"]=ps2000a.ps2000aGetValues(
		handle.value,			# handle
		0,						# start index
		byref(samples_found),	# no_of_samples
		0,						# downsample ratio - not implemented
		0,						# downsample ratio mode - not implemented
		0,						# segment index, not implemented
		byref(overflow_raw),	# voltage overflow flags
		)
	assert_pico_ok(status["GetValues"])

# Bitwise extraction of overflow flags

	overflow=(
		(overflow_raw.value & 0b0000_0001)!=0,
		(overflow_raw.value & 0b0000_0010)!=0,
		(overflow_raw.value & 0b0000_0100)!=0,
		(overflow_raw.value & 0b0000_1000)!=0,
		)

# Set up some Python arrays to accept the data

	time=[]
	volts_a=[]
	volts_b=[]
	volts_c=[]
	volts_d=[]
	volts=[volts_a,volts_b,volts_c,volts_d]

# Calculate times and convert buffer data to voltage

	time_offset=trigger_samples_pre.value*time_interval.value*1e-9
	for i in range(0,samples_total.value):
		time.append(1e-9*time_interval.value*i-time_offset)
	for channel in range (0,4):
		if channel_range_id[channel]>0:
			for i in range(0,samples_total.value):
				volts[channel].append(buffers[channel][i]/(max_adc.value)*channel_range_maxvolts[channel]*channel_attenuation[channel])
		else:
			volts[channel]=[""]*samples_total.value

	return time,volts

'''
quick_plot()
-----------
A straightforward plotting routine for captured traces.  It can easily be omitted (particularly
	when taking multiple data sets), and the graphics may be automatically saved by specifying
	a valid "image_path" parameter.  The various plot attributes are not hard to mess about with.
'''
def quick_plot(
	time,				# "time" and "volts" are very necessary!
	volts,
	title=None,			# appears at the top - maybe something like f"{frequency} Hz"
	legend=True,		# if "True", a legend is displayed, otherwise not
	file_path=None,		# Specify a valid path and the image will be saved - "#" is replaced by a timestamp, and file type is determined by the extension
	display=True,		# Useful to set to False if taking multiple data sets - graphics may still be saved
	verbose=True,		# Outputs information if "True"
	):
	fig,ax=plt.subplots()
	ax.set_xlabel('Time/s')
	ax.set_ylabel('Volts/V')
	if overflow!=(False,False,False,False):
		plt.text(0,0,"!!!OUT OF RANGE!!!",fontsize=14,color='red',ha='left',va='bottom',transform=fig.transFigure)
	ax.grid(visible=True,which='major',axis='both')
	for channel in range(0,4):
		if volts[channel][0] != '':
			ax.plot(time,volts[channel],label=f'{channel_print_name[channel]}',color=waveform_colour[channel])
	if legend:
		ax.legend()
	ax.set_title(title)
	ax.ticklabel_format(axis='both',style='sci',scilimits=(0,0))
	if file_path!=None:
		file_path=file_format(file_path)
		fig.savefig(file_path)
		if verbose:
			print(f"Saved image: {file_path}")
	if display:
		plt.show()
	else:
		plt.close()

'''
quick_save()
-----------
Saves data to file.  A correct path (including filename) is necessary, or the file will be
	saved to the default_data folder.  Pick a delimiter or it will default to ",".
'''
def quick_save(
	time=None,							# "time" and "volts" are very necessary!
	volts=None,
	file_path='./default_data/#.csv',	# *full* path and file name - there is a good chance you'll mess this up, but "./data_folder/filename.csv" might be a good start.  A '#' included in the path will be replaced by a timestamp.
	delimiter=',',						# you might prefer a different symbol between data values
	verbose=True,						# Outputs information if "True"
	):
	global overflow
	if overflow!=(False,False,False,False):
			print(f'WARNING: Out of range!')
	if delimiter=='':
		delimiter=','
	file_path=file_format(file_path)
	if verbose:
		print(f"Saved data: {file_path}")
	with open(file_path,"w") as f:
		f.write(f"n{delimiter}t/s{delimiter}{channel_print_name[0]}/V{delimiter}{channel_print_name[1]}/V{delimiter}{channel_print_name[2]}/V{delimiter}{channel_print_name[3]}/V\n")
		for i in range(0,len(time),1):
			f.write(f"{i}{delimiter}{time[i]}{delimiter}{volts[0][i]}{delimiter}{volts[1][i]}{delimiter}{volts[2][i]}{delimiter}{volts[3][i]}\n")
	f.close()

'''
file_format()
-----------
A short routine for replacing instances of "#" in file paths with a timestamp
and for creating all necessary folders and sub-folders.  "File path" here includes the
file name, e.g. ./my_topfolder/my_subfolder/file_name.txt
'''
def file_format(
	file_path=None,
	):
	global now_time
	file_timestamp=now_time.strftime("%Y-%m-%d_%H-%M-%S_%f")
	if file_path is None or file_path=='':
		file_path=os.getcwd()+f'./default_data/#.csv'
		print(f"WARNING: No file path provided.  Using default.")
	file_path=file_path.replace("#",file_timestamp)
	file_parts=file_path.split('/')
	if len(file_parts)>1:
		file_folders='/'.join(file_parts[0:len(file_parts)-1])
	if not os.path.isdir(file_folders):
		os.makedirs(file_folders)
	return file_path

'''
awg()
-----------
Arbitrary Wave Generator - this can do plenty, but for now it's a simple signal generator.
	Can sweep frequency (by setting "finish_frequency" etc), but doesn't have to.
'''
def awg(
	waveform='square',		# Waveform type: 'sine', 'square', 'triangle', 'ramp_up', 'ramp_down', 'dc'
	peak_to_peak=2,			# Peak-to-peak in volts
	offset=0,				# d.c. offset in volts
	frequency=1000,			# (Start) frequency in Hz
	finish_frequency=None,	# Sweep finish frequency in Hz
	increment=1,			# Frequency increment in Hz
	dwell_time=1,			# Time per frequency step in seconds
	sweep_type='up',		# 'up', 'down', 'updown', 'downup'
	operation='normal',		# 'normal', 'whitenoise', 'random' - 'whitenoise' ignores most inputs, and 'random' jumbles the order of the standard sweep
	):

# Avoid sweeping if no finish frequency

	if finish_frequency is None:
		finish_frequency=frequency
		increment=0
		dwell_time=1e10

# tidy up waveform, type of sweep and operation mode

	waveform=str(waveform)
	waveform=waveform.strip().lower()
	waveform_id={
		'0':0,'sine':0,
		'1':1,'square':1,'':1,
		'2':2,'triangle':2,
		'3':3,'ramp_up':3,'ramp up':3,
		'4':4,'ramp_down':4,'ramp down':4,
		'5':5,'sinc':5,
		'6':6,'gaussian':6,
		'7':7,'half_sine':7,'half sine':7,
		'8':8,'dc':8,
		}
	sweep_type=str(sweep_type)
	sweep_type=sweep_type.strip().lower()
	sweep_type_id={
		'0':0,'up':0,
		'1':1,'down':1,
		'2':2,'updown':2,'up_down':2,'up-down':2,'up down':2,
		'3':3,'downup':3,'down_up':3,'down_up':3,'down up':3,
		}
	operation=str(operation)
	operation=operation.strip().lower()
	operation_id={
		'0':0,'normal':0,'off':0,'none':0,
		'1':1,'noise':1,'whitenoise':1,'white_noise':1,'white-noise':1,'white noise':1,
		'2':2,'random':2,'pseudorandom':2,'pseudo-random':2,'pseudo_random':2,'pseudo random':2,
		}

	offset_microvolts=int(offset*1000000)				# microvolts!
	peak_to_peak_microvolts=int(peak_to_peak*1000000)	# microvolts!

# Nothing returned by this function - we simply instruct the AWG.

	status["AWG"]=ps2000a.ps2000aSetSigGenBuiltIn(
		handle.value,
		offset_microvolts,
		peak_to_peak_microvolts,
		waveform_id[waveform],
		frequency,
		finish_frequency,
		increment,
		dwell_time,
		sweep_type_id[sweep_type],
		operation_id[operation],
		0,							# others not implemented
		0,
		0,
		0,
		0,
		)

	return False

'''
scope_monitor()
-----------
Opens a window which displays the voltage traces and continually refreshes.  Would be used
	to observe that things are looking good.  Clicking on the plot area closes it.
	Usually closing returns "True", but clicking the 'x' button at top right returns "False",
	and can be used to abort the capture.
'''
def scope_monitor():

# Opens a repeatedly-refreshing plot window - see "pyplot" documentation at Matplotlib for details

	mon,ax=plt.subplots()
	monitor=plt.plot([],[])[0]
	plt.title("Click to start data capture")
	plt.xlabel("Time/s")
	plt.ylabel("Volts/V")
	plt.grid(visible=True,which='major',axis='both')
	ax.ticklabel_format(axis='both',style='sci',scilimits=(0,0))

# Now check for clicks on the plot (returns "True" for close-and-continue
# or "False" for close-and-exit if forced close via the "x" )

	global monitor_closed
	global continue_capture
	monitor_closed=False
	continue_capture=True

	def close_continue(event):
		global monitor_closed
		global continue_capture
		monitor_closed=True
		continue_capture=True

	def close_exit(event):
		global monitor_closed
		global continue_capture
		if monitor_closed==True:
			monitor_closed=True
		else:
			monitor_closed=True
			continue_capture=False

	mon.canvas.mpl_connect('button_press_event',close_continue)
	mon.canvas.mpl_connect('close_event',close_exit)

# Read data from the PicoScope and send it to the plot

	(time,volts)=scope_capture()
	for channel in range(0,4):
		if volts[channel][0]!='':
			plt.plot(time,volts[channel],label=f'{channel_print_name[channel]}',color=waveform_colour[channel])
	plt.legend()

# If one or more channels is out of its voltage range, warn

	overflow_text=plt.text(0,0,f"!!!OUT OF RANGE!!!",fontsize=14,color='red',ha='left',va='bottom',transform=mon.transFigure)
	while(monitor_closed==False):
		for artist in plt.gca().lines:
			artist.remove()
		(time,volts)=scope_capture()
		for channel in range(0,4):
			if volts[channel][0]!='':
				plt.plot(time,volts[channel],label=f'{channel_print_name[channel]}',color=waveform_colour[channel])
		plt.legend()
		if overflow!=(False,False,False,False):
			overflow_text.set_visible(True)
		else:
			overflow_text.set_visible(False)
		plt.pause(0.01)

	plt.close()

	return continue_capture

'''
picoscope_close()
-----------
Good practice, but practical too.  If taking multiple traces during an experiment, there is
	usually no need to close the PicoScope (saving time with the laborious open/close process),
	but do remember to close on completion.
'''
def picoscope_close(
	verbose=True,
	):

	status["CloseUnit"]=ps2000a.ps2000aCloseUnit(handle.value)
	if verbose:
		print(f"Closing PicoScope {picoscope_variant}.")
	return False

