from silica import fsm, Input, Output


@fsm
def baud_rx(out : Output):
    # 12 mhz / (115200 * 16) = 6.5
    i = Reg(8)
    while True:
        yield
        out = 0
        for i in range(0, 5):
            yield
        out = 1


@fsm
def baud_tx(out : Output):
    # 12 mhz / (115200 hz) = 104
    i = Reg(8)
    while True:
        yield
        out = 0
        for i in range(0, 102):
            yield
        out = 1



@fsm(clock_enable=True)
def uart_transmitter(data : Input[8], run : Input, tx : Output, done : Output):
    i = Reg(4)
    while True:
        yield
        tx = 1
        done = 0
        if run:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield
            done = 1

@fsm(clock_enable=True)
def uart_receiver(rx : Input, run : Input, data : Output[8], done : Output):
    i = Reg(4)
    j = Reg(4)
    k = Reg(4)
    l = Reg(4)
    while True:
        yield
        done = 0
        if run:
            while rx:  # wait for rx line low
                yield
            for i in range(0, 8):  # sample at middle of data
                yield
            for j in range(0, 8):
                for k in range(0, 15):
                    yield
                data[j] = rx
                yield
            for k in range(0, 15):
                yield
            done = rx  # end bit
            for k in range(0, 15):
                yield
            for k in range(0, 15):
                yield

@fsm(clock_enable=True)
def uart_control(rx_run : Output, rx_done : Input, tx_run : Output, tx_done : Input):
    while True:
        yield
        rx_run = 1
        tx_run = 0
        while rx_done:
            yield
        while not rx_done:
            yield
        rx_run = 0
        tx_run = 1
        while tx_done:
            yield
        while not tx_done:
            yield
        tx_run = 0
        while not tx_run:
            yield
