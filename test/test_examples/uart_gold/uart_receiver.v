module uart_receiver(input  rx, input  ready, output[7:0]  data, output  valid, input  clock_enable, input CLKIN);
    reg [2:0] state = 1'b0;
    reg [7:0] data;
    reg[3:0]  ____x0;
    reg[3:0]  ____x1;
    reg[3:0]  ____x2;
    reg[3:0]  ____x3;
    reg[3:0]  i;
    always @(posedge CLKIN) if (clock_enable) begin
        case (state)
            0: begin
                valid = 1'b0;
                if (!(rx) && ready) begin
                    ____x0 = 1'b0;
                    state = 1'b1;
                end else begin
                    state = 1'b0;
                end
            end
            1: begin
                ____x0 = ____x0 + 1'b1;
                if (____x0 < 4'b1000) begin
                    state = 1'b1;
                end else begin
                    if (!(rx)) begin
                        i = 1'b0;
                        ____x1 = 1'b0;
                        state = 2'b10;
                    end else begin
                        state = 1'b0;
                    end
                end
            end
            2: begin
                ____x1 = ____x1 + 1'b1;
                if (____x1 < 4'b1111) begin
                    state = 2'b10;
                end else begin
                    data[i] = rx;
                    state = 2'b11;
                end
            end
            3: begin
                i = i + 1'b1;
                if (i < 4'b1000) begin
                    ____x1 = 1'b0;
                    state = 2'b10;
                end else begin
                    ____x2 = 1'b0;
                    state = 3'b100;
                end
            end
            4: begin
                ____x2 = ____x2 + 1'b1;
                if (____x2 < 4'b1111) begin
                    state = 3'b100;
                end else begin
                    valid = rx;
                    state = 3'b101;
                end
            end
            5: begin
                valid = 1'b0;
                ____x3 = 1'b0;
                state = 3'b110;
            end
            6: begin
                ____x3 = ____x3 + 1'b1;
                if (____x3 < 4'b1110) begin
                    state = 3'b110;
                end else begin
                    state = 1'b0;
                end
            end
        endcase
    end
endmodule