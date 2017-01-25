from dsl import FSM, Input, Output

@FSM
def uart_transmitter(data : Input, signal : Input, tx : Output):
    while True:
        yield
        if signal:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data & 1  # send next bit
                yield
                data >>= 1
            tx = 1  # end bit
            yield

data = 0xBE
uart_transmitter.IO.data.value   = data
uart_transmitter.IO.signal.value = 1

print("Expected : 0{}1".format("{0:b}".format(data)[::-1]))  # reversed because data is sent LSB first
print("Actual   : ", end="")
for i in range(0, 10):
    next(uart_transmitter)
    print(uart_transmitter.IO.tx.value, end="")
print()
