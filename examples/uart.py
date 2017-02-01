from dsl import FSM, Input, Output

# @FSM
# def signal(valid : Input, done : Input, run : Output):
#     while True:
#         yield
#         if valid:
#             run = 1
#             while not done:
#                 yield
#             run = 0

# signal.IO.valid.value = 1
# signal.IO.done.value = 0
# next(signal)
# next(signal)
# next(signal)
# print("Run should be high: {}".format(signal.IO.run.value == 1))
# signal.IO.done.value = 1
# next(signal)
# print("Run should be low: {}".format(signal.IO.run.value == 0))

@FSM
def counter(run : Input, done : Output):
    while True:
        yield
        if run:
            for i in range(0, 15):
                yield
            done = 1
            yield
            done = 0

# counter.IO.run.value = 1
# next(counter)
# print(counter.IO.done.value == 0)
# for i in range(0, 15):
#     next(counter)
# print(counter.IO.done.value == 1)

# @FSM
# def uart_transmitter(data : Input[8], signal : Input, tx : Output):
#     while True:
#         yield
#         if signal:
#             tx = 0  # start bit
#             yield
#             for i in range(0, 8):
#                 tx = data[i]
#                 yield
#             tx = 1  # end bit
#             yield
# 
# data = 0xBE
# uart_transmitter.IO.data.value   = data
# uart_transmitter.IO.signal.value = 1
# 
# print("Expected : 0{0:b}1".format(data))
# print("Actual   : ", end="")
# for i in range(0, 10):
#     next(uart_transmitter)
#     print(uart_transmitter.IO.tx.value, end="")
# print()
