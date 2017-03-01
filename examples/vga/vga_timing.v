module vga_timing(output  horizontal_sync, output  vertical_sync, output  pixel_valid, output[9:0]  vga_row, output[9:0]  vga_col, input  clock, input  reset, input  clock_enable, input CLKIN);
    reg  state = 1'b0;
    always @(posedge CLKIN) if (clock_enable) begin
        case (state)
            0: begin
                col = col + 1'b1;
                if (col < 10'b1100100000) begin
                    pixel_valid = 8'b10010000 <= col <= 10'b1100010000 && 6'b100011 <= row <= 10'b1000000011;
                    horizontal_sync = 1'b0 <= col < 7'b1100000;
                    vertical_sync = 1'b0 <= row < 2'b10;
                    vga_col = col - 8'b10010000;
                    vga_row = row - 6'b100011;
                    state = 1'b0;
                end else begin
                    row = row + 1'b1;
                    if (row < 10'b1000001101) begin
                        col = 1'b0;
                        pixel_valid = 8'b10010000 <= col <= 10'b1100010000 && 6'b100011 <= row <= 10'b1000000011;
                        horizontal_sync = 1'b0 <= col < 7'b1100000;
                        vertical_sync = 1'b0 <= row < 2'b10;
                        vga_col = col - 8'b10010000;
                        vga_row = row - 6'b100011;
                        state = 1'b0;
                    end else begin
                        row = 1'b0;
                        col = 1'b0;
                        pixel_valid = 8'b10010000 <= col <= 10'b1100010000 && 6'b100011 <= row <= 10'b1000000011;
                        horizontal_sync = 1'b0 <= col < 7'b1100000;
                        vertical_sync = 1'b0 <= row < 2'b10;
                        vga_col = col - 8'b10010000;
                        vga_row = row - 6'b100011;
                        state = 1'b0;
                    end
                end
            end
        endcase
    end
endmodule