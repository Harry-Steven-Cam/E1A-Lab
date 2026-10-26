import time

import pll_ps2000a as picoscope

picoscope.picoscope_open()

print("Hello PicoScope!")

picoscope.picoscope_close()

time.sleep(3)

