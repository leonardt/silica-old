module baud_tx(output reg out, input CLKIN);
reg [1:0] yield_state;
initial begin
    yield_state = 0;
end
reg [9:0] i;
always @(posedge CLKIN) begin
    if ((yield_state == 0)) begin 
        yield_state <= 1;
    end
    if ((yield_state == 1)) begin 
        yield_state <= 2;
        out <= 0;
        i <= 0;
    end
    if ((yield_state == 2) && (i + 1 < 414)) begin 
        yield_state <= 2;
        i <= i + 1;
    end
    if ((yield_state == 2) && (!(i + 1 < 414))) begin 
        yield_state <= 1;
        i <= i + 1;
        out <= 1;
    end
end
endmodule