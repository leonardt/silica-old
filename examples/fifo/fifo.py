from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm


def REGs(n):
    return [Register(8, ce=True) for i in range(n)]

def MUXs(n):
    return [Mux(2,8) for i in range(n)]

def readport(logn, regs, raddr):
    n = 1 << logn

    muxs = MUXs(n-1)
    for i in range(n//2):
        muxs[i](regs[2*i], regs[2*i+1], raddr[0])

    k = 0
    l = 1 << (logn-1)
    for i in range(logn-1):
        for j in range(l//2):
            muxs[k+l+j](muxs[k+2*j], muxs[k+2*j+1], raddr[i+1])
        k += l
        l //= 2

    return muxs[n-2]

def writeport(logn, regs, WADDR, I, WE):
    n = 1 << logn

    decoder = Decoder(logn)
    enable = And(2,1<<logn)
    enable(decoder(WADDR), array(*(n*[WE])))

    for i in range(n):
        regs[i](I, CE=enable.O[i])

def RAM(logn, RADDR, WADDR, I, WE):
    assert len(RADDR) == logn
    assert len(WADDR) == logn

    regs = REGs(1 << logn)
    writeport(logn, regs, WADDR, I, WE)
    return readport(logn, regs, RADDR)

def DualRAM(logn, RADDR0, RADDR1, WADDR, I, WE):
    assert len(RADDR0) == logn
    assert len(RADDR1) == logn
    assert len(WADDR) == logn

    regs = REGs(1 << logn)
    writeport(logn, regs, WADDR, I, WE)
    return readport(logn, regs, RADDR0), readport(logn, regs, RADDR1)


height = 8
width = 8
addr_width = max(1, height.bit_length())

@fsm
def control_logic(read_enable   : In(Bit),
                  write_enable  : In(Bit),
                  empty         : In(Bit),
                  full          : In(Bit),
                  status        : Out(Array(addr_width, Bit)),
                  read_pointer  : Out(Array(addr_width, Bit)),
                  write_pointer : Out(Array(addr_width, Bit))):
    while True:
        if read_enable and ~empty:
            read_pointer = read_pointer + 1
        if write_enable and ~full:
            write_pointer = write_pointer + 1
        if read_enable and ~write_enable:
            status = status - 1
        elif write_enable and ~read_enable:
            status = status + 1
        yield

fifo = DefineCircuit('fifo',
    "data_in"      , In(Array(width, Bit)), 
    "data_out"     , Out(Array(width, Bit)), 
    "write_enable" , In(Bit), 
    "read_enable"  , In(Bit), 
    "read_pointer" , Out(Array(addr_width, Bit)),
    "write_pointer", Out(Array(addr_width, Bit)),
    "empty"        , Out(Bit), 
    "full"         , Out(Bit),
    "CLK"          , In(Bit)
)
control = control_logic()

ram = RAM(addr_width, control.read_pointer, control.write_pointer, fifo.data_in, fifo.write_enable)
wire(control.read_pointer, fifo.read_pointer)
wire(control.write_pointer, fifo.write_pointer)
wire(ram, fifo.data_out)
# full = status == height - 1
full = EQ(addr_width)(control.status, int2seq(height - 1, addr_width))
wire(full, fifo.full)
wire(full, control.full)
# empty = status == 0
empty = EQ(addr_width)(control.status, int2seq(0, addr_width))
wire(empty, fifo.empty)
wire(empty, control.empty)

wire(control.write_enable, fifo.write_enable)
wire(control.read_enable, fifo.read_enable)

EndCircuit()

icestick = IceStick()
icestick.Clock.on()
for i in range(len(icestick.PMOD0)):
    icestick.PMOD0[i].output().on()
# for i in range(len(icestick.PMOD1)):
#     icestick.PMOD1[i].output().on()
main = icestick.main()
circ = fifo()
wire(circ.write_enable, 1)
wire(circ.read_enable, 0)
wire(int2seq(8, 8), circ.data_in)
wire(circ.write_pointer[0], main.PMOD0[0])
wire(circ.write_pointer[1], main.PMOD0[1])
wire(circ.write_pointer[2], main.PMOD0[2])
wire(circ.write_pointer[3], main.PMOD0[3])

if __name__ == '__main__':
    compile("fifo", main)
