from silica import fsm, Input, Output

@fsm("python")
def signal(valid : Input, done : Input, run : Output):
    while True:
        yield
        if valid:
            run = 1
            while not done:
                yield
            run = 0

def test_1():
    signal.IO.valid.value = 1
    signal.IO.done.value = 0
    next(signal)
    next(signal)
    next(signal)
    assert signal.IO.run.value == 1
    signal.IO.done.value = 1
    next(signal)
    assert signal.IO.run.value == 0

@fsm("python")
def counter(run : Input, done : Output):
    while True:
        yield
        if run:
            for i in range(0, 15):
                yield
            done = 1
            yield
            done = 0

def test_counter():
    counter.IO.run.value = 1
    next(counter)
    for i in range(0, 15):
        assert counter.IO.done.value == 0
        next(counter)
    assert counter.IO.done.value == 1

@fsm("python")
def uart_transmitter(data : Input[8], signal : Input, tx : Output):
    while True:
        yield
        if signal:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield

def test_uart_tx():
    data = 0xBE
    uart_transmitter.IO.data.value   = data
    uart_transmitter.IO.signal.value = 1

    expected = "0{0:b}1".format(data)
    actual = ""
    for i in range(0, 10):
        next(uart_transmitter)
        actual += str(uart_transmitter.IO.tx.value)
    assert expected == actual
