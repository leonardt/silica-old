module baud_rx(output  out, input CLKIN);
    reg  state = 1'b0;
    reg[4:0]  i;
    always @(posedge CLKIN) begin
        case (state)
            0: begin
                out = 1'b0;
                i = 1'b0;
                state = 1'b1;
            end
            1: begin
                i = i + 1'b1;
                if (i < 5'b11000) begin
                    state = 1'b1;
                end else begin
                    out = 1'b1;
                    state = 1'b0;
                end
            end
        endcase
    end
endmodule