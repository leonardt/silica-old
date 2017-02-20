from silica import fsm, Input, Output


@fsm
def baud_rx(out : Output):
    # 12 mhz / (28800 * 16) = 26
    i = Reg(16)
    while True:
        yield
        out = 0
        for i in range(0, 24):
            yield
        out = 1


@fsm
def baud_tx(out : Output):
    # 12 mhz / (28800 hz) = 416
    i = Reg(16)
    while True:
        yield
        out = 0
        for i in range(0, 414):
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
    j = Reg(4)
    data = Reg(8)
    while True:
        yield
        valid = 0
        if ready:
            if not rx:
                for i in range(0, 8):  # sample at middle of data
                    yield
                if not rx:  # Check if still low
                    for j in range(0, 8):
                        for i in range(0, 15):
                            yield
                        data[j] = rx
                        yield
                    for i in range(0, 15):
                        yield
                    valid = 1  # end bit
                    yield
                    valid = 0
                    for i in range(0, 14):
                        yield
