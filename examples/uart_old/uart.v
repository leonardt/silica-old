`include "uart_transmitter.v"
`include "baud_tx.v"
`include "baud_rx.v"
`include "uart_receiver.v"
`include "aFifo.v"
module main (input  CLKIN, output TX, input RX);
    wire baud_tx_out;
    baud_tx baud_tx_inst(.out(baud_tx_out), .CLKIN(CLKIN));
    wire baud_rx_out;
    baud_rx baud_rx_inst(.out(baud_rx_out), .CLKIN(CLKIN));

    wire rx_valid;
    wire [7:0] tx_data;
    wire [7:0] rx_data;
    wire read_empty;
    wire tx_ready;
    wire fifo_full;

    aFifo fifo(.Data_out(tx_data), .Empty_out(read_empty),
        .ReadEn_in(tx_ready), .RClk(baud_tx_out), .Data_in(rx_data),
        .Full_out(fifo_full), .WriteEn_in(rx_valid), .WClk(baud_rx_out),
        .Clear_in(0));

    uart_receiver uart_receiver_inst(.rx(RX), .ready(~fifo_full),
        .data(rx_data), .valid(rx_valid), .clock_enable(baud_rx_out),
        .CLKIN(CLKIN));

    uart_transmitter uart_transmitter_inst(.data(tx_data), .valid(~read_empty),
        .tx(TX), .ready(tx_ready),
        .clock_enable(baud_tx_out), .CLKIN(CLKIN));
endmodule
