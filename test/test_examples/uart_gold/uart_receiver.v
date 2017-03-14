module uart_receiver(input rx, input ready, output reg[7:0] data, output reg valid, input clock_enable, input CLKIN);
reg [16:0] yield_state;  // TODO: Infer state width
initial begin
    yield_state = 0;
end
reg [15:0]____x0;  // TODO: Infer state_var width
reg [15:0]____x1;  // TODO: Infer state_var width
reg [15:0]____x2;  // TODO: Infer state_var width
reg [15:0]____x3;  // TODO: Infer state_var width
reg [15:0]i;  // TODO: Infer state_var width
always @(posedge CLKIN) if (clock_enable) begin
if ((yield_state == 0)) begin 
    yield_state <= 1;
end
if ((yield_state == 1) && (ready & !rx)) begin 
    yield_state <= 2;
    valid <= 0;
    ____x0 <= 0;
end
if ((yield_state == 1) && (!(ready & !rx))) begin 
    yield_state <= 1;
    valid <= 0;
end
if ((yield_state == 2) && (____x0 + 1 < 8)) begin 
    yield_state <= 2;
    ____x0 <= ____x0 + 1;
end
if ((yield_state == 2) && (!(____x0 + 1 < 8))
 && (!rx)) begin 
    yield_state <= 3;
    ____x0 <= ____x0 + 1;
    i <= 0;
    ____x1 <= 0;
end
if ((yield_state == 2) && (!(____x0 + 1 < 8))
 && (!!rx)) begin 
    yield_state <= 1;
    ____x0 <= ____x0 + 1;
end
if ((yield_state == 3) && (____x1 + 1 < 15)) begin 
    yield_state <= 3;
    ____x1 <= ____x1 + 1;
end
if ((yield_state == 3) && (!(____x1 + 1 < 15))) begin 
    yield_state <= 4;
    ____x1 <= ____x1 + 1;
    data[i] <= rx;
end
if ((yield_state == 4) && (i + 1 < 8)) begin 
    yield_state <= 3;
    i <= i + 1;
    ____x1 <= 0;
end
if ((yield_state == 4) && (!(i + 1 < 8))) begin 
    yield_state <= 5;
    i <= i + 1;
    ____x2 <= 0;
end
if ((yield_state == 5) && (____x2 + 1 < 15)) begin 
    yield_state <= 5;
    ____x2 <= ____x2 + 1;
end
if ((yield_state == 5) && (!(____x2 + 1 < 15))) begin 
    yield_state <= 6;
    ____x2 <= ____x2 + 1;
    valid <= rx;
end
if ((yield_state == 6)) begin 
    yield_state <= 7;
    valid <= 0;
    ____x3 <= 0;
end
if ((yield_state == 7) && (____x3 + 1 < 14)) begin 
    yield_state <= 7;
    ____x3 <= ____x3 + 1;
end
if ((yield_state == 7) && (!(____x3 + 1 < 14))) begin 
    yield_state <= 1;
    ____x3 <= ____x3 + 1;
end
end
endmodule