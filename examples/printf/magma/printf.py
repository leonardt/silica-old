from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

from monitor import BAUD_RATE  # Defined in monitor.py
CLOCK_RATE = int(12e6)  # 12 mhz


@fsm(clock_enable=True)
def uart_transmitter(data : In(Array(8, Bit)), run : In(Bit), tx : Out(Bit)):
    while True:
        if run:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield
            # Holding the line high for an extra baud cycle seems to improve
            # reliability of transmission (reduces framing issues?)
            yield
        else:
            tx = 1
            yield


icestick = IceStick()
icestick.Clock.on()
icestick.TX.output().on()
main = icestick.main()
baud_clock = CounterModM(103, 7)
uart = uart_transmitter()

c1 = Counter(7)
c2 = Counter(8)

@fsm(clock_enable=True)
def send_message(send    : In(Bit),
                 message : In(Array(8, Bit)),
                 id      : In(Array(8, Bit)),
                 out     : Out(Array(8, Bit)),
                 run     : Out(Bit)):
    while True:
        if send:
            out = id
            run = 1
            yield
            run = 0
            for i in range(10):
                yield
            out = message
            run = 1
            yield
            run = 0
            for i in range(10):
                yield
        else:
            yield

data = Register(8, ce=True)
wire(data.I, c2.O)
wire(data.CE, c1.COUT)
sender = send_message()
wire(sender.CE, baud_clock.COUT)
wire(c1.COUT, sender.send)
wire(data.O, sender.message)
wire(int2seq(11, 8), sender.id)
wire(uart.data, sender.out)
wire(uart.run, sender.run)
wire(uart.tx, main.TX)
wire(uart.CE, baud_clock.COUT)

if __name__ == '__main__':
    compile("printf", main)
