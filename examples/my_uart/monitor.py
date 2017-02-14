import serial
import time

with serial.Serial('/dev/ttyUSB1', 115200, timeout=1) as ser:
    # print(ser.read(100))
    # for char in b"Hello World":
    #     ser.write([char])
    msg = b"e" * 20
    ser.write(msg)
    print(ser.read(len(msg)))
