import serial
import time

with serial.Serial('/dev/ttyUSB1', 115200, timeout=1) as ser:
    while True:
        x = ser.read(24)
        print("Received Bytes: {}".format(x))


