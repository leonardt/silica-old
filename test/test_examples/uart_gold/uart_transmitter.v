module uart_transmitter(input[7:0] data, input valid, output reg tx, output reg ready, input clock_enable, input CLKIN);
reg [3:0] yield_state;
initial begin
    yield_state = 0;
end
reg [4:0] i;
always @(posedge CLKIN) if (clock_enable) begin
if ((yield_state == 0) && valid) begin 
    yield_state <= 1;
    ready <= 1;
end
if ((yield_state == 0) && (!valid)) begin 
    yield_state <= 5;
    tx <= 1;
end
if ((yield_state == 1)) begin 
    yield_state <= 2;
    ready <= 0;
    tx <= 0;
end
if ((yield_state == 2)) begin 
    yield_state <= 3;
    i <= 0;
    tx <= data[0];
end
if ((yield_state == 3) && (i + 1 < 8)) begin 
    yield_state <= 3;
    i <= i + 1;
    tx <= data[i + 1];
end
if ((yield_state == 3) && (!(i + 1 < 8))) begin 
    yield_state <= 4;
    i <= i + 1;
    tx <= 1;
end
if ((yield_state == 4) && valid) begin 
    yield_state <= 1;
    ready <= 1;
end
if ((yield_state == 4) && (!valid)) begin 
    yield_state <= 5;
    tx <= 1;
end
if ((yield_state == 5) && valid) begin 
    yield_state <= 1;
    ready <= 1;
end
if ((yield_state == 5) && (!valid)) begin 
    yield_state <= 5;
    tx <= 1;
end
end
endmodule