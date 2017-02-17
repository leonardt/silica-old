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
def uart_transmitter(data : Input[8], valid : Input, tx : Output, ready : Output):
    i = Reg(4)
    while True:
        yield
        tx = 1
        if valid:
            ready = 1
            yield
            ready = 0
            yield
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield

@fsm(clock_enable=True)
def uart_receiver(rx : Input, ready : Input, data : Output[8], valid : Output):
    i = Reg(4)
    j = Reg(6)
    k = Reg(6)
    l = Reg(6)
    data = Reg(8)
    while True:
        yield
        valid = 0
        if ready:
            if not rx:
                for i in range(0, 8):  # sample at middle of data
                    yield
                if not rx:
                    for j in range(0, 8):
                        for k in range(0, 15):
                            yield
                        data[j] = rx
                        yield
                    for k in range(0, 15):
                        yield
                    valid = rx  # end bit
                    yield
                    valid = 0
                    for k in range(0, 15):
                        yield
                    for k in range(0, 15):
                        yield
