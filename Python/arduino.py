import serial as ser  # Serial read/write library for Arduino communication
import time as timer  # Time library for delays and timing functions

arduino = None  # Global variable to hold the Arduino serial connection


"""
Below scans and finds the com port
"""
import serial.tools.list_ports as port_list


def findPort():
    try:
        ports = list(port_list.comports())
        for port in ports:
            print(port, "Is connected")
            return str(port)[0:4]
    except:
        print("The device was not found")


"""
arduino_open()
-----------	
Straightforwardly, this opens the Arduino for serial communication.
	9600 baud (bits per second) is the default as it is the most convenient,
	and is very likely to be suitable.  Make sure that the port is correct
	(displayed in the Arduino IDE when successfully connected).
	Use close_arduino() at the end.  The port may also be found in the available_ports() function.
"""


def arduino_open(
    port=findPort(),
    baud_rate=9600,
    timeout=10,
):

    global arduino
    arduino = ser.Serial(port=port, baudrate=baud_rate, timeout=timeout)
    timer.sleep(2)  # Wait for the connection to be established
    print(f"Connected to Arduino on port {arduino.port} at {arduino.baudrate} baud.")


"""
arduino_write()
-----------	
Writes a command to the Arduino.  The command is sent as a string,
	and is encoded to bytes before being sent.
"""


def arduino_write(
    command="",
):

    command_out = command.encode("utf-8")
    arduino.write(command_out)


"""
arduino_prepare()
-----------	
This function sends a command to the Arduino (if necessary multiple times)
	and waits for a specific response.
	The default behavior is to send the string "ready" (repeatedly)
	until the Arduino to responds with "ready".  This may be used to ensure
	that the Arduino is in the correct state to receive commands.
"""


def arduino_prepare(
    receive="ready",
    send="",
):

    print("preparing")
    if send == "":
        send = receive
    listening = False
    while not listening:
        arduino.write(send.encode("utf-8"))
        timer.sleep(0.1)
        if arduino.readline().decode().strip() == receive:
            listening = True


"""
arduino_read()
-----------	
This function reads a line from the Arduino and returns it as a string.
"""


def arduino_read():

    return arduino.readline().decode("utf-8").strip()


"""
arduino_close()
-----------	
This closes the Arduino serial connection.
"""


def arduino_close(
    verbose=True,
):

    arduino.close()
    if verbose:
        print(f"Disconnected from Arduino on port {arduino.port}.")
