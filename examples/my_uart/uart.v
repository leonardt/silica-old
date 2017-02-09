`include "uart_transmitter.v"
`include "baud.v"
`include "data_controller.v"
module main (input  CLKIN, output TX);
    wire run;
    wire done;
    wire [7:0] baud;
    wire baud_cout;
    CounterModM8 inst0 (.O(baud), .COUT(baud_cout), .CLK(CLKIN));

    wire [7:0] data;
    data_controller data_controller_inst(.data(data), .done(done), .clock_enable(baud_cout & done), .CLKIN(CLKIN));

    uart_transmitter uart_transmitter_inst(.data(data), .run(1), .tx(TX), .done(done), .clock_enable(baud_cout), .CLKIN(CLKIN));
endmodule
