module uart_transmitter(input[7:0]  data, input  valid, output  tx, output  ready, input  clock_enable, input CLKIN);
    reg [2:0] state = 1'b0;
    reg [3:0] i;
    always @(posedge CLKIN) if (clock_enable) begin
        case (state)
            0: begin
                tx = 1'b1;
                if (valid) begin
                    ready = 1'b1;
                    state = 1'b1;
                end else begin
                    state = 1'b0;
                end
            end
            1: begin
                ready = 1'b0;
                tx = 1'b0;
                state = 2'b10;
            end
            2: begin
                i = 1'b0;
                tx = data[i];
                state = 2'b11;
            end
            3: begin
                i = i + 1'b1;
                if (i < 4'b1000) begin
                    tx = data[i];
                    state = 2'b11;
                end else begin
                    tx = 1'b1;
                    state = 3'b100;
                end
            end
            4: begin
                state = 1'b0;
            end
        endcase
    end
endmodule