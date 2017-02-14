`include "uart_transmitter.v"
`include "baud_tx.v"
`include "baud_rx.v"
`include "data_controller.v"
`include "uart_control.v"
`include "uart_receiver.v"
module main (input  CLKIN, output TX, input RX, output D1, output D2, output D3, output D4, output D5);
    wire baud_tx_out;
    baud_tx baud_tx_inst(.out(baud_tx_out), .CLKIN(CLKIN));
    wire baud_rx_out;
    baud_rx baud_rx_inst(.out(baud_rx_out), .CLKIN(CLKIN));

    wire rx_run;
    wire rx_done;
    wire tx_run;
    wire tx_done;
    // uart_control uart_control_isnt(.rx_run(rx_run), .rx_done(rx_done), .tx_run(tx_run), .tx_done(tx_done), .clock_enable(baud_tx_out), .CLKIN(CLKIN));
    wire [7:0] data;
    uart_receiver uart_receiver_inst(.rx(RX), .run(rx_run), .data(data), .done(rx_done), .clock_enable(baud_rx_out), .CLKIN(CLKIN));
    assign D5 = data[0];
    assign D4 = data[1];
    assign D3 = data[2];
    assign D2 = data[3];
    assign D1 = rx_run;

    initial begin
        rx_run = 1;
    end
    always @(posedge baud_rx_out) begin
        if (rx_run && rx_done) begin
            tx_run = 1;
            rx_run = 0;
        end
    end

    // wire run;
    // wire done;
    // wire [7:0] data;
    // data_controller data_controller_inst(.data(data), .clock_enable(done & baud_out), .CLKIN(CLKIN));

    uart_transmitter uart_transmitter_inst(.data(data), .run(tx_run), .tx(TX), .done(tx_done), .clock_enable(baud_tx_out), .CLKIN(CLKIN));
endmodule
