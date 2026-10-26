# Source - https://stackoverflow.com/q/44056846
# Posted by Neil Dey, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-01, License - CC BY-SA 4.0

import serial.tools.list_ports as port_list
ports = list(port_list.comports())
for p in ports:
    print (p)
