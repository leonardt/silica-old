from magma import *
from mantle import *
from silica import fsm

@fsm("verilog", clock_enable=True)
def blink(D1 : Out(Bit), D2 : Out(Bit), D3 : Out(Bit)):
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
