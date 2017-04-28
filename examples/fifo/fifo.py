from magma import *
from mantle import *

def fifo(height, width):
    addr_width = max(1, height.bit_length())
    @circuit
    def _fifo(data_in      : In(Array(width, Bit)), 
              data_out     : Out(Array(width, Bit)), 
              write_enable : In(Bit), 
              read_enable  : In(Bit), 
              empty        : Out(Bit), 
              full         : Out(Bit)):
        mem = [Reg(width) for _ in range(height)]
        read_pointer = Reg(addr_width)
        write_pointer = Reg(addr_width)
        status = Reg(addr_width)
        full = status == height - 1
        empty = status == 0
        @fsm
        def write_logic():
            write_pointer = 0
            while True:
                if write_enable and ~full:
                    write_pointer += 1
                    mem[write_pointer] = data_in
                yield

        @fsm
        def read_logic():
            read_pointer = 0
            while True:
                if read_enable and ~empty:
                    read_pointer += 1
                    data_out = mem[read_pointer]
                yield

        @fsm
        def status_logic():
            while True:
                if read_enable and ~write_enable:
                    status -= 1
                elif write_enable and ~read_enable:
                    status += 1
                yield
    return _fifo
