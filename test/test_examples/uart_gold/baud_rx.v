module baud_rx(output reg out, input CLKIN);
reg [16:0] yield_state;  // TODO: Infer state width
initial begin
    yield_state = 0;
end
reg [15:0]i;  // TODO: Infer state_var width
always @(posedge CLKIN) begin
if ((yield_state == 0)) begin 
    yield_state <= 1;
end
if ((yield_state == 1)) begin 
    yield_state <= 2;
    out <= 0;
    i <= 0;
end
if ((yield_state == 2) && (i + 1 < 24)) begin 
    yield_state <= 2;
    i <= i + 1;
end
if ((yield_state == 2) && (!(i + 1 < 24))) begin 
    yield_state <= 1;
    i <= i + 1;
    out <= 1;
end
end
endmodule