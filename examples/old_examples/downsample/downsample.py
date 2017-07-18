from magma import *
from mantle import *
from silica import fsm

size_x = 100
size_y = 100
factor = 2

@fsm(clock_enable=True)
def downsample(valid : Out(Bit)):
    while True:
        for y in range(0, size_y):
            for x in range(0, size_x // factor):
                # valid = x % 2
                # TODO: Can we desguar this with strength reduction?
                valid = 1
                yield
                for j in range(0, factor):
                    valid = 0
                    yield

icestick = IceStick()
icestick.Clock.on()
icestick.D1.on()
main = icestick.main()
circ = downsample()
counter = Counter(23)
wire(circ.CE, counter.COUT)
wire(circ.valid, main.D1)

compile("downsample", main)
