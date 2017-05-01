from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

@fsm(clock_enable=True)
def simple(D1 : Out(Bit), D2 : Out(Bit), D3 : Out(Bit)):
    while True:
        D1 = 1
        D2 = 0
        D3 = 0
        yield
        D1 = 0
        D2 = 1
        D3 = 0
        yield
        D1 = 0
        D2 = 0
        D3 = 1
        yield


icestick = IceStick()
icestick.Clock.on()
icestick.D1.on()
icestick.D2.on()
icestick.D3.on()
main = icestick.main()
s = simple()
counter = Counter(23)
wire(s.CE, counter.COUT)
wire(s.D1, main.D1)
wire(s.D2, main.D2)
wire(s.D3, main.D3)

compile("simple", main)
