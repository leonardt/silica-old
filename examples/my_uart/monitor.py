import serial
import time

with serial.Serial('/dev/ttyUSB1', 115200, timeout=1) as ser:
    # print(ser.read(100))
    # for char in b"Hello World":
    #     ser.write([char])
    for i in range(10):
        msg = b"HH"
        ser.write(msg)
        time.sleep(.1)
        print(ser.read(len(msg)))
