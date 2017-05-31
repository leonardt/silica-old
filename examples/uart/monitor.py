import serial
import time
import sys

# argument should be something like
# /dev/tty.usbserial-142B
# /dev/ttyUSB1
with serial.Serial(sys.argv[1], 115200, timeout=1) as ser:
    while True:
        print(ser.read(10))
