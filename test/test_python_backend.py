from silica import fsm, Input, Output

@fsm("python")
def signal(valid : Input, done : Input, run : Output):
    while True:
        yield
        if valid:
            run = 1
            while not done:
                yield
            run = 0

def test_1():
    signal.IO.valid.value = 1
    signal.IO.done.value = 0
    next(signal)
    next(signal)
    next(signal)
    assert signal.IO.run.value == 1
    signal.IO.done.value = 1
    next(signal)
    assert signal.IO.run.value == 0

@fsm("python")
def counter(run : Input, done : Output):
    while True:
        yield
        if run:
            for i in range(0, 15):
                yield
            done = 1
            yield
            done = 0

def test_counter():
    counter.IO.run.value = 1
    next(counter)
    for i in range(0, 15):
        assert counter.IO.done.value == 0
        next(counter)
    assert counter.IO.done.value == 1

@fsm("python")
def uart_transmitter(data : Input[8], signal : Input, tx : Output):
    while True:
        yield
        if signal:
            tx = 0  # start bit
            yield
            for i in range(0, 8):
                tx = data[i]
                yield
            tx = 1  # end bit
            yield

def test_uart_tx():
    data = 0xBE
    uart_transmitter.IO.data.value   = data
    uart_transmitter.IO.signal.value = 1

    expected = "0{0:b}1".format(data)
    actual = ""
    for i in range(0, 10):
        next(uart_transmitter)
        actual += str(uart_transmitter.IO.tx.value)
    assert expected == actual


def test_input_type_error():
    try:
        @fsm("python")
        def write_to_input(a : Input, b : Output):
            while True:
                yield
                a = 1
                b = a
        assert False, "Program should throw a type error"
    except TypeError as e:
        pass


def test_output_type_error():
    try:
        @fsm("python")
        def read_from_output(a : Input, b : Output, c : Output):
            while True:
                yield
                b = a
                c = b
        assert False, "Program should throw a type error"
    except TypeError as e:
        assert str(e) == "Attempting to read from an Output variable b"


VGA_NUM_ROWS     = 48
VGA_NUM_COLS     = 64


# Following in terms of 25 MHz clock
VGA_HSYNC_TDISP  = VGA_NUM_COLS
VGA_HSYNC_TPW    = 9
VGA_HSYNC_TFP    = 1
VGA_HSYNC_TBP    = 4
VGA_HSYNC_OFFSET = VGA_HSYNC_TPW + VGA_HSYNC_TBP
VGA_HSYNC_TS     = VGA_HSYNC_OFFSET + VGA_HSYNC_TDISP + VGA_HSYNC_TFP

# Following in terms of lines
VGA_VSYNC_TDISP  = VGA_NUM_ROWS
VGA_VSYNC_TPW    = 2
VGA_VSYNC_TFP    = 1
VGA_VSYNC_TBP    = 3
VGA_VSYNC_OFFSET = VGA_VSYNC_TPW + VGA_VSYNC_TBP
VGA_VSYNC_TS     = VGA_VSYNC_OFFSET + VGA_VSYNC_TDISP + VGA_VSYNC_TFP
def test_vga():

    @fsm("python", clock_enable=True)
    def vga_timing(
            horizontal_sync : Output,
            vertical_sync   : Output,
            pixel_valid     : Output,
            vga_row         : Output[10],
            vga_col         : Output[10]):
        while True:
            for row in range(0, VGA_VSYNC_TS):
                for col in range(0, VGA_HSYNC_TS):
                    pixel_valid = VGA_VSYNC_OFFSET <= row <= VGA_VSYNC_OFFSET + VGA_NUM_ROWS and \
                                  VGA_HSYNC_OFFSET <= col <= VGA_HSYNC_OFFSET + VGA_NUM_COLS

                    horizontal_sync = 0 <= col < VGA_HSYNC_TPW
                    vertical_sync   = 0 <= row < VGA_VSYNC_TPW

                    vga_col = col - VGA_HSYNC_OFFSET
                    vga_row = row - VGA_VSYNC_OFFSET
                    yield

    for row in range(0, VGA_VSYNC_TS):
        for col in range(0, VGA_HSYNC_TS):
            assert vga_timing.IO.pixel_valid.value == (VGA_VSYNC_OFFSET <= row <= VGA_VSYNC_OFFSET + VGA_NUM_ROWS and \
                          VGA_HSYNC_OFFSET <= col <= VGA_HSYNC_OFFSET + VGA_NUM_COLS)

            assert vga_timing.IO.horizontal_sync.value == (0 <= col < VGA_HSYNC_TPW)
            assert vga_timing.IO.vertical_sync.value   == (0 <= row < VGA_VSYNC_TPW)

            int2bits = lambda x: [int(n) for n in bin(x)[2:].zfill(10)]
            if vga_timing.IO.pixel_valid.value:
                assert vga_timing.IO.vga_col.value == int2bits(col - VGA_HSYNC_OFFSET)
                assert vga_timing.IO.vga_row.value == int2bits(row - VGA_VSYNC_OFFSET)
            next(vga_timing)
