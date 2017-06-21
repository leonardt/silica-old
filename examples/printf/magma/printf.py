from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm
import pickle

from monitor import BAUD_RATE  # Defined in monitor.py
CLOCK_RATE = int(12e6)  # 12 mhz


@fsm(clock_enable=True)
def uart_transmitter(data : In(Array(8, Bit)), 
                     run  : In(Bit), 
                     tx   : Out(Bit),
                     done : Out(Bit)):
    while True:
        if run:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield
            done = 1
            # Holding the line high for an extra baud cycle seems to improve
            # reliability of transmission (reduces framing issues?)
            yield
            done = 0
        else:
            tx = 1
            yield


icestick = IceStick()
icestick.Clock.on()
icestick.TX.output().on()
main = icestick.main()

c1 = Counter(7)
c2 = Counter(8)

START_BYTE  = 0x61
END_BYTE    = 0x62

@fsm(clock_enable=True)
def send_message(send    : In(Bit),
                 message : In(Array(8, Bit)),
                 id      : In(Array(8, Bit)),
                 out     : Out(Array(8, Bit)),
                 run     : Out(Bit),
                 done    : In(Bit)):
    while True:
        if send:
            out = START_BYTE
            run = 1
            yield
            run = 0
            while not done:
                yield

            out = id
            run = 1
            yield
            run = 0
            while not done:
                yield

            out = message
            run = 1
            yield
            run = 0
            while not done:
                yield

            out = END_BYTE
            run = 1
            yield
            run = 0
            while not done:
                yield
        else:
            yield

messages = {}

unique_printf_id = 0

def gen_unique_printf_id():
    global unique_printf_id
    unique_printf_id += 1
    return unique_printf_id

# printf("c2.O = {}", c2.O, when=c1.COUT)
def printf(message, arg, when=None):
    id = gen_unique_printf_id()
    messages[id] = message
    baud_clock = CounterModM(103, 7)
    uart = uart_transmitter()
    data = Register(8, ce=True)
    wire(data.I, arg)
    wire(data.CE, when)
    sender = send_message()
    wire(sender.CE, baud_clock.COUT)
    wire(when, sender.send)
    wire(data.O, sender.message)
    wire(int2seq(id, 8), sender.id)
    wire(uart.data, sender.out)
    wire(uart.done, sender.done)
    wire(uart.run, sender.run)
    wire(uart.tx, main.TX)
    wire(uart.CE, baud_clock.COUT)

printf("c2.O = {}", c2.O, when=c1.COUT)

if __name__ == '__main__':
    compile("printf", main)
    pickle.dump(messages, open( "messages.pkl", "wb"))
