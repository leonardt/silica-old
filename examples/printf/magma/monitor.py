import serial
import time
import sys
import pickle

BAUD_RATE  = 115200
START_BYTE  = 0x61
END_BYTE    = 0x62

if __name__ == "__main__":
    # sys.argv[1] should be something like
    # /dev/tty.usbserial-142B
    # /dev/ttyUSB1
    with open("messages.pkl", "rb") as messages_pickle:
        messages = pickle.load(messages_pickle)
    with serial.Serial(sys.argv[1], BAUD_RATE, timeout=1) as ser:
        while True:
            try:
                received = []
                in_message = False
                message = []
                message_count = 0
                for byte in ser.read(10):
                    if not in_message:
                        if byte == START_BYTE:
                            in_message = True
                            message_count = 0
                    else:
                        if message_count <= 1:
                            message.append(byte)
                            message_count += 1
                        else:
                            if byte == END_BYTE:
                                received.append(message)
                for message in received:
                    print(messages[message[0]].format(message[1]))

            except UnicodeDecodeError as e:
                print("Got UnicodeDecodeError, skipping message")
                print("> {}".format(str(e)))
