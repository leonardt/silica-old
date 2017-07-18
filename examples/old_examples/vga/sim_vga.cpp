#include "Vvga_timing.h"
#include "verilated.h"
#include <cassert>
#include <iostream>


#define VGA_NUM_ROWS     480
#define VGA_NUM_COLS     640
#define VGA_HSYNC_TDISP  VGA_NUM_COLS
#define VGA_HSYNC_TPW    96
#define VGA_HSYNC_TFP    16
#define VGA_HSYNC_TBP    48
#define VGA_HSYNC_OFFSET (VGA_HSYNC_TPW + VGA_HSYNC_TBP)
#define VGA_HSYNC_TS     (VGA_HSYNC_OFFSET + VGA_HSYNC_TDISP + VGA_HSYNC_TFP)
#define VGA_VSYNC_TDISP  VGA_NUM_ROWS
#define VGA_VSYNC_TPW    2
#define VGA_VSYNC_TFP    10
#define VGA_VSYNC_TBP    33
#define VGA_VSYNC_OFFSET (VGA_VSYNC_TPW + VGA_VSYNC_TBP)
#define VGA_VSYNC_TS     (VGA_VSYNC_OFFSET + VGA_VSYNC_TDISP + VGA_VSYNC_TFP)

int main(int argc, char **argv, char **env) {
    Verilated::commandArgs(argc, argv);
    Vvga_timing* top = new Vvga_timing;
    top->CLKIN = 1;
    top->clock_enable = 1;

    for (int row = 0; row < VGA_VSYNC_TS; row++) {
        for (int col = 0; col < VGA_HSYNC_TS; col++) {
            top->CLKIN = 0;
            top->eval();
            top->CLKIN = 1;
            top->eval();
            bool pixel_valid = (VGA_VSYNC_OFFSET <= row && row <= VGA_VSYNC_OFFSET + VGA_NUM_ROWS) && (VGA_HSYNC_OFFSET <= col && col <= VGA_HSYNC_OFFSET + VGA_NUM_COLS);
            assert(top->pixel_valid == pixel_valid);
            assert(top->horizontal_sync == col < VGA_HSYNC_TPW);
            assert(top->vertical_sync == row < VGA_VSYNC_TPW);
            if (pixel_valid) {
                assert(top->vga_col == col - VGA_HSYNC_OFFSET);
                assert(top->vga_row == row - VGA_VSYNC_OFFSET);
            };
        }
    }

    delete top;
    exit(0);
}
