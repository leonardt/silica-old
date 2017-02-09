from silica import fsm, Input, Output
import binascii

# message = "hello world"
# byte_arr = [ord(char) for char in message]
# body = ""
# for byte in byte_arr:
#     body += "        data = {};\n        yield\n".format(byte)
# 
# print(body)
# exit()

@fsm(clock_enable=True)
def data_controller(data : Output[8], done : Input):
    while True:
        yield
        data = 104;
        yield
        data = 101;
        yield
        data = 108;
        yield
        data = 108;
        yield
        data = 111;
        yield
        data = 32;
        yield
        data = 119;
        yield
        data = 111;
        yield
        data = 114;
        yield
        data = 108;
        yield
        data = 100;


@fsm(clock_enable=True)
def uart_transmitter(data : Input[8], run : Input, tx : Output, done : Output):
    i = Reg(4)
    while True:
        yield
        if run:
            done = 0
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield
            done = 1
