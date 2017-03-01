from silica import fsm, Input, Output


VGA_NUM_ROWS     = 480
VGA_NUM_COLS     = 640


# Following in terms of 25 MHz clock
VGA_HSYNC_TDISP  = VGA_NUM_COLS
VGA_HSYNC_TPW    = 96
VGA_HSYNC_TFP    = 16
VGA_HSYNC_TBP    = 48
VGA_HSYNC_OFFSET = VGA_HSYNC_TPW + VGA_HSYNC_TBP
VGA_HSYNC_TS     = VGA_HSYNC_OFFSET + VGA_HSYNC_TDISP + VGA_HSYNC_TFP

# Following in terms of lines
VGA_VSYNC_TDISP  = VGA_NUM_ROWS
VGA_VSYNC_TPW    = 2
VGA_VSYNC_TFP    = 10
VGA_VSYNC_TBP    = 33
VGA_VSYNC_OFFSET = VGA_VSYNC_TPW + VGA_VSYNC_TBP
VGA_VSYNC_TS     = VGA_VSYNC_OFFSET + VGA_VSYNC_TDISP + VGA_VSYNC_TFP

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
