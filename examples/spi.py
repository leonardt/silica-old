from silica import Output, Input, fsm
"""
Currently broken
"""

@fsm
def spi_master(MOSI     : Output,
               MISO     : Input,
               byte_out : Input[8],
               byte_in  : Output[8]):
    while True:
        # Wait for byte to send and target slave
        yield
        byte_in = 0
        # Select the slave
        bit = 0x80
        for i in range(7, -1, -1):
            MOSI = byte_out[i]
            # Yield the current bit and receive the next bit from slave
            yield
            byte_in[i] = MISO
        # Deselect the slave
        SS = 0


slave_id = 0
@fsm
def spi_slave(MOSI     : Input, 
              MISO     : Output, 
              SS       : Input[4], 
              byte_in  : Output[8], 
              byte_out : Input[8]):
    while True:
        yield
        if SS == slave_id:
            for i in range(7, -1, -1):
                MOSI = byte_out[i]
                # Yield the current bit and receive the next bit from slave
                yield
                byte_in[i] = MISO
