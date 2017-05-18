from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

BAUD_RATE  = 28800
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
for i in range(len(icestick.PMOD0)):
    icestick.PMOD0[i].output().on()
# for i in range(len(icestick.PMOD1)):
#     icestick.PMOD1[i].output().on()
main = icestick.main()
baud_clock = CounterModM(103, 8)
uart = uart_transmitter()
wire(uart.data, int2seq(85, 8))
wire(uart.valid, 1)
wire(uart.tx, main.TX)
wire(uart.tx, main.PMOD0[0])
wire(uart.tx, main.PMOD0[1])
wire(uart.tx, main.PMOD0[2])
wire(uart.tx, main.PMOD0[3])
# wire(uart.state_out[3], main.PMOD1[0])
# wire(uart.state_out[4], main.PMOD1[1])
# wire(uart.state_out[5], main.PMOD1[2])
# wire(uart.state_out[6], main.PMOD1[3])
wire(uart.CE, baud_clock.COUT)

compile("uart", main)
