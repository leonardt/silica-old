from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

BAUD_RATE  = 115200
CLOCK_RATE = int(12e6)  # 12 mhz


def REGs(n):
    return [Register(8) for i in range(n)]

def MUXs(n):
    return [Mux(2,8) for i in range(n)]

# TODO: Use the ROM definition from class, should we merge this into mantle?
def _ROM(logn, init, A):
    n = 1 << logn
    assert len(A) == logn
    assert len(init) == n

    muxs = MUXs(n-1)
    for i in range(n//2):
        muxs[i](init[2*i], init[2*i+1], A[0])

    k = 0
    l = 1 << (logn-1)
    for i in range(logn-1):
        for j in range(l//2):
            muxs[k+l+j](muxs[k+2*j], muxs[k+2*j+1], A[i+1])
        k += l
        l //= 2

    return muxs[n-2]


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
baud_clock = CounterModM(103, 8)
uart = uart_transmitter()

# We use a ROM to store our message, it should look up the next entry every 11
# baud ticks (the time it takes to send the current byte)
advance = CounterModM(11, 4, ce=True)
wire(advance.CE, baud_clock.COUT)

# This counter controls the ROM, it's clock enable is controlled by the baud
# clock divider `advance`
counter = Counter(4, ce=True)
wire(counter.CE, advance.COUT)

message = "Hello, world! \r\n"
message_bytes = [int2seq(ord(char), 8) for char in message]
rom = _ROM(4, message_bytes, counter.O)

wire(uart.data, rom.O)
wire(uart.valid, 1)
wire(uart.tx, main.TX)
wire(uart.CE, baud_clock.COUT)

if __name__ == '__main__':
    compile("printf", main)
