from magma import *
from mantle import *
from loam.boards.icestick import IceStick
from silica import fsm

@fsm
def addr_logic(
        m_axi_araddr  : Out(Array(32, Bit)),
        m_axi_arready : In(Bit),
        m_axi_arvalid : Out(Bit),

        # Control config
        config_valid      : In(Bit),
        config_start_addr : In(Array(32, Bit)),
        config_nbytes     : In(Array(32, Bit)),

        addr_ready : Out(Bit)
    ):
    while True:
        if config_valid:
            addr_ready = 0
            m_axi_araddr = config_start_addr
            m_axi_arvalid = 1
            yield
            # Burst size is 128 bytes (18 * 6) so we divide config_nbytes by 128
            for _ in range(config_nbytes[7:], bit_width=25):  
                while ~m_axi_arready:
                    yield
                m_axi_araddr += 128
                yield
            addr_ready = 1
            m_axi_arvalid = 0
            yield
        else:
            yield

@fsm 
def read_logic(
        m_axi_rvalid          : In(Bit),
        config_valid          : In(Bit),
        config_nbytes         : In(Array(32, Bit)),
        data_ready_downstream : In(Bit),
        data_valid            : Out(Bit),
        read_ready            : Out(Bit)
    ):
    while True:
        if config_valid:
            read_ready = 0
            data_valid = m_axi_rvalid
            yield
            for _ in range(start=0, stop=config_nbytes, step=8, bit_width=32):  # Each valid cycle gives us 8 bytes
                yield
                while ~(m_axi_rvalid & data_ready_downstream):
                    yield
            data_valid = 0
            read_ready = 1
            yield
        else:
            yield


icestick = IceStick()
icestick.Clock.on()
icestick.Clock.on()
for i in range(4):
    icestick.PMOD0[i].output().on()
main = icestick.main()
# read = read_logic()
# wire(read.m_axi_rvalid, 1)
# wire(read.config_valid, 1)
# wire(read.config_nbytes, int2seq(10, 32))
# wire(read.data_ready_downstream, 1)
# wire(read.data_valid, main.PMOD0[0])
# wire(read.read_ready, main.PMOD0[1])
# wire(0, main.PMOD0[2])
# wire(0, main.PMOD0[3])
# addr = addr_logic()
# wire(addr.m_axi_araddr, main.I0)
# wire(addr.m_axi_arready, 1)
# wire(addr.m_axi_arvalid, main.PMOD0[0])
# 
# wire(1, addr.config_valid)
# wire(int2seq(0x44, 32), addr.config_start_addr)
# wire(int2seq(1280, 32), addr.config_nbytes)
# 
# wire(addr.addr_ready, main.PMOD0[1])
# wire(addr.m_axi_araddr[7], main.PMOD0[2])
# wire(addr.m_axi_araddr[8], main.PMOD0[3])

dram_reader = DefineCircuit('dram_reader', 
        # AXI port
        "m_axi_araddr"  , Out(Array(32, Bit)),
        "m_axi_arready" , In(Bit),
        "m_axi_arvalid" , Out(Bit),
        "m_axi_rdata"   , In(Array(64, Bit)),
        "m_axi_rready"  , Out(Bit),
        "m_axi_rresp"   , In(Array(2, Bit)),
        "m_axi_rvalid"  , In(Bit),
        "m_axi_rlast"   , In(Bit),
        "m_axi_arlen"   , Out(Array(4, Bit)),
        "m_axi_arsize"  , Out(Array(3, Bit)),
        "m_axi_arburst" , Out(Array(2, Bit)),
        # Control config
        "config_valid"      , In(Bit),
        "config_ready"      , Out(Bit),
        "config_start_addr" , In(Array(32, Bit)),
        "config_nbytes"     , In(Array(32, Bit)),
        # Ram port
        "data_ready_downstream" , In(Bit),
        "data_valid"            , Out(Bit),
        "data"                  , Out(Array(64, Bit))
    )
m_axi_arlen   = 0b1111
m_axi_arsize  = 0b011
m_axi_arburst = 0b1

addr_logic = addr_logic()  # TODO: Add sugar for function call syntax for wiring arguments
wire(addr_logic.m_axi_araddr, dram_reader.m_axi_araddr)
wire(addr_logic.m_axi_arready, dram_reader.m_axi_arready)
wire(addr_logic.m_axi_arvalid, dram_reader.m_axi_arvalid)

wire(addr_logic.config_valid, dram_reader.config_valid)
wire(addr_logic.config_start_addr, dram_reader.config_start_addr)
wire(addr_logic.config_nbytes, dram_reader.config_nbytes)

read_logic = read_logic()

wire(read_logic.m_axi_rvalid, dram_reader.m_axi_rvalid)
wire(read_logic.config_valid, dram_reader.config_valid)
wire(read_logic.config_nbytes, dram_reader.config_nbytes)
wire(read_logic.data_ready_downstream, dram_reader.data_ready_downstream)
wire(read_logic.data_valid, dram_reader.data_valid)

data = dram_reader.m_axi_rdata
# config_ready = read_logic.read_ready & addr_logic.addr_ready
config_ready = And(2, width=1)(read_logic.read_ready, addr_logic.addr_ready)
wire(dram_reader.config_ready, config_ready)
EndCircuit()


if __name__ == '__main__':
    compile("dram_reader", main)

"""
Documentation pulled from
https://www.xilinx.com/support/documentation/ip_documentation/axi_master_burst/v1_00_a/ds844_axi_master_burst.pdf

m_axi_araddr  : AXI Master Burst Read Address Channel Address Bus. The
                starting address for the requested read transaction.

m_axi_arready : AXI Master Burst Read Address Channel Read Address Ready.
                Indicates target is ready to accept the read address.
                    * 1 = Target read to accept address.
                    * 0 = Target not ready to accept address.

m_axi_arvalid : AXI Master Burst Read Address Channel Read Address Valid.
                Indicates if m_axi_araddr is valid.
                    * 1 = Read Address is valid.
                    * 0 = Read Address is not valid.

m_axi_rdata   : AXI Master Burst Read Data Channel Read Data. Read data bus
                for the requested read transaction.

m_axi_rready  : AXI Master Burst Read Data Channel Ready. Indicates the
                read channel is ready to accept read data.
                    * 1 = Is ready.
                    * 0 = Is not ready

m_axi_rresp   : AXI Master Burst Read Data Channel Response.  Indicates
                results of the read transaction.
                    * 00b = OKAY - Normal access has been successful.
                    * 01b = EXOKAY - Not supported.
                    * 10b = SLVERR - Slave returned error on transaction.
                    * 11b = DECERR - Decode error, transaction targeted
                            unmapped address.

m_axi_rvalid  : AXI Master Burst Read Data Channel Data Valid.  Indicates
                m_axi_rdata is valid.
                    * 1 = Valid read data.
                    * 0 = Not valid read data.

m_axi_rlast   : AXI Master Burst Read Data Channel Last. Indicates the last
                data beat of a burst transaction.
                    * 0 = Not last data beat.
                    * 1 = Last data beat.
m_axi_arlen   : AXI Master Burst Read Address Channel Burst Length. This
                qualifier specifies the requested AXI Read transaction
                length in data beats - 1.
m_axi_arsize  : AXI Master Burst Read Address Channel Burst Size.
                Indicates the data transaction width of each burst data
                beat.
                    * 000b = Not Supported by AXI Master burst.
                    * 001b = Not Supported by AXI Master burst.
                    * 010b = 4 bytes (32-bit wide burst).
                    * 011b = 8 bytes (64-bit wide burst).
                    * 100b = 16 bytes (128-bit wide burst).
                    * 101b = Not Supported by AXI Master burst.
                    * 110b = Not Supported by AXI Master burst.
                    * 111b = Not Supported by AXI Master burst.
m_axi_arburst : AXI Master Burst Read Address Channel Burst Type.
                Indicates type of burst.
                    * 00b = FIXED - Not supported.
                    * 01b = INCR - Incrementing address.
                    * 10b = WRAP - Not supported.
                    * 11b = Reserved.
"""
