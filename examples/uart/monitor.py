import serial
import time
import sys

# argument should be something like
# /dev/tty.usbserial-142B
# /dev/ttyUSB1
with serial.Serial(sys.argv[1], 28800, timeout=1) as ser:
    while True:
        msg = ""
        while True:
            result = ser.read(1)
            if not result:
                break
            msg += result.decode()
        if msg:
            print(msg)
