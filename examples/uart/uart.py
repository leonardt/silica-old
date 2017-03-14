from silica import fsm, Input, Output

BAUD_RATE  = 28800
CLOCK_RATE = int(12e6)  # 12 mhz

@fsm
def baud_rx(out : Output):
    while True:
        yield
        out = 0
        for i in range(0, CLOCK_RATE // (BAUD_RATE * 16) - 2):
            yield
        out = 1


@fsm
def baud_tx(out : Output):
    while True:
        yield
        out = 0
        for i in range(0, (CLOCK_RATE // BAUD_RATE) - 2):
            yield
        out = 1



@fsm(clock_enable=True)
def uart_transmitter(data : Input[8], valid : Input, tx : Output, ready : Output):
    while True:
        if valid:
            # Signal the FIFO to load into data
            ready = 1
            yield
            ready = 0

            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield
        else:
            tx = 1
            yield

@fsm(clock_enable=True)
def uart_receiver(rx    : Input, 
                  ready : Input, 
                  data  : Output[8], 
                  valid : Output):
    """
    yield from range(8) -> yield for 8 cycles
    """
    # data = Reg(8)  # TODO: Can we just specify the output to be registered?
    while True:
        yield
        valid = 0
        if ready & ~rx:
            yield from range(8)  # Wait half a baud period
            if ~rx:              # Check if still low
                for i in range(8):
                    yield from range(15)
                    data[i] = rx
                    yield
                yield from range(15)
                valid = rx  # end bit
                yield
                valid = 0
                yield from range(14)
