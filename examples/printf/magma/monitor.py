import serial
import time
import sys

BAUD_RATE  = 115200

if __name__ == "__main__":
    # sys.argv[1] should be something like
    # /dev/tty.usbserial-142B
    # /dev/ttyUSB1
    with serial.Serial(sys.argv[1], BAUD_RATE, timeout=1) as ser:
        while True:
            try:
                print(int.from_bytes(ser.read(1), byteorder='big'))
            except UnicodeDecodeError as e:
                print("Got UnicodeDecodeError, skipping message")
                print("> {}".format(str(e)))
