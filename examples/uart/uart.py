from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

BAUD_RATE  = 115200
CLOCK_RATE = int(12e6)  # 12 mhz


@fsm(clock_enable=True)
def uart_transmitter(data : In(Array(8, Bit)), valid : In(Bit), tx : Out(Bit)):
    while True:
        if valid:
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


icestick = IceStick()
icestick.Clock.on()
icestick.TX.output().on()
main = icestick.main()
baud_clock = CounterModM(103, 8)
uart = uart_transmitter()
wire(uart.data, int2seq(94, 8))
wire(uart.valid, 1)
wire(uart.tx, main.TX)
wire(uart.CE, baud_clock.COUT)

if __name__ == '__main__':
    compile("uart", main)
