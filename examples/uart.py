from dsl import FSM, Input, Output

@FSM
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

data = 0xBE
uart_transmitter.IO.data.value   = data
uart_transmitter.IO.signal.value = 1

print("Expected : 0{0:b}1".format(data))
print("Actual   : ", end="")
for i in range(0, 10):
    next(uart_transmitter)
    print(uart_transmitter.IO.tx.value, end="")
print()
