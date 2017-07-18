from silica import Output, Input, fsm

# @fsm
# def spi_master(MOSI     : Output,
#                MISO     : Input,
#                byte_out : Input[8],
#                byte_in  : Output[8]):
#     while True:
#         # Wait for byte to send and target slave
#         yield
#         byte_in = 0
#         # Select the slave
#         bit = 0x80
#         for i in range(7, -1, -1):
#             MOSI = byte_out[i]
#             # Yield the current bit and receive the next bit from slave
#             yield
#             byte_in[i] = MISO
#         # Deselect the slave
#         SS = 0


slave_id = 0
@fsm
def spi_slave(MOSI     : In(Bit), 
              MISO     : Out(Bit), 
              SS       : In(Array(4, Bit)),
              SCK      : In(Bit),
              byte_in  : Out(Array(8, Bit)),
              byte_out : In(Array(8, Bit)),
              done     : Out(Bit)):
    SCK_reg = Register(1)
    SCK_old_reg = Register(1)
    wire(SCK, SCK_reg.I[0])
    wire(SCK_reg.O, SCK_old_reg.I)
    while True:
        if SS == slave_id:
            for i in range(7, -1, -1):
                if not SCK_old_reg and SCK_reg:
                    byte_in[i] = MOSI
                else:
                    MISO = byte_out[i]
                yield
            done = 1
            yield
            done = 0
        else:
            yield
