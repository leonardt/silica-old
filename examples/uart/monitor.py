import serial
import time

with serial.Serial('/dev/ttyUSB1', 28800, timeout=1) as ser:
    # print(ser.read(100))
    # for char in b"Hello World":
    #     ser.write([char])
    for i in range(10):
        msg = b"Hello World"
        ser.write(msg)
        time.sleep(.1)
        print(ser.read(len(msg)))
