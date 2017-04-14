from silica import fsm, Input, Output


@fsm(reset=True)
def dram_reader(
        # AXI port
        m_axi_araddr  : Output[32],
        m_axi_arready : Input,
        m_axi_arvalid : Output,
        m_axi_rdata   : Input[64],
        m_axi_rready  : Output,
        m_axi_rresp   : Input[2],
        m_axi_rvalid  : Input,
        m_axi_rlast   : Input,
        m_axi_arlen   : Output[4],
        m_axi_arsize  : Output[3],
        m_axi_arburst : Output[2],

        # Control config
        config_valid      : Input,
        config_read       : Ouput,
        config_start_addr : Input[32],
        config_nbytes     : Input[32],

        # Ram port
        data_ready_downstream : Input,
        data_valid            : Output,
        data                  : Output[64]
    ):
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
    m_axi_arlen   = 0b1111
    m_axi_arsize  = 0b011
    m_axi_arburst = 0b1
    
    addr_ready = wire  # TODO: Figure out this wire logic

    @fsm
    def addr_logic():
        while True:
            if config_valid:
                addr_ready = 0
                m_axi_araddr = config_start_addr
                yield
                for _ in range(config_nbytes // 128):  # TODO: Is this right?
                    m_axi_araddr += 128
                    yield
                addr_ready = 1

    read_ready = wire  # TODO: Figure out this wire logic

    @fsm 
    def read_logic():
        while True:
            if config_valid:
                read_ready = 0
                count = 0
                data_valid = m_axi_rvalid
                for i in range(start=0, stop=config_nbytes // 128, step=8):  # Round to nearest 128 bytes
                    while not (m_axi_rvalid and data_ready_downstream):
                        yield
                data_valid = 0
                read_ready = 1


    data = m_axi_rdata
    config_ready = read_ready and addr_ready


                    

