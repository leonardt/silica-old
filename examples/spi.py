from dsl import Output, Input, fsm, Module

@fsm
def spi_master():
    MOSI = Output()
    MISO = Input()
    SS   = Output(width=4)
    byte_out = Input(width=8)
    byte_in  = Output(width=8)
    while True:
        # Wait for byte to send and target slave
        # byte_out, slave_id = yield byte_in
        yield
        byte_in = 0
        # Select the slave
        SS = slave_id
        bit = 0x80
        while bit:
            MOSI = byte_out & bit
            # Yield the current bit and receive the next bit from slave
            # MISO = yield MOSI
            yield
            if MISO:
                byte_in |= bit
            bit >>= 1
        print("Master received byte " + byte_in + "from Slave ID: " + slave_id)
        # Deselect the slave
        SS = 0

@fsm
def spi_slave(slave_id):
    MOSI = Input()
    MISO = Output()
    SS   = Input(width=4)
    byte_in  = Output(width=8)
    byte_out = Input(width=8)
    while True:
        yield
        if not SS:
            continue
        bit = 0x80
        while bit:
            MOSI = byte_out & bit
            # Yield the current bit and receive the next bit from slave
            # MISO = yield MOSI
            yield
            if MISO:
                byte_in |= bit
            bit >>= 1
        print("Slave ID: " + slave_id + " received byte " + byte_in)

module = Module()
master = module.init_fsm(spi_master)
slave  = module.init_fsm(spi_slave)
module.connect(master.io.MOSI, slave.io.MOSI)
module.connect(master.io.MISO, slave.io.MISO)
module.connect(master.io.SS,   slave.io.SS)
module.set(master.io.byte_out, 0xBE)
module.set(slave.io.byte_out,  0xEF)
module.start()
