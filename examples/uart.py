from dsl import fsm, Input, Output, Module

@fsm
def uart_transmitter(data : Input, signal : Input, tx : Output):
    while True:
        yield
        if signal:
            tx = 0  # start bit
            yield
            bit = 0x80
            while (bit):
                tx = data & bit  # send next bit
                yield
                bit >>= 1
            tx = 1  # end bit
            yield

module = Module()
module.init_fsm(uart_transmitter)

