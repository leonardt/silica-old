NAME = simple

PCF = $(NAME).pcf

DEVICE = 1k
QUIET = -q

$(NAME).bin: $(NAME).v $(PCF) $(NAME).py
	python3 $(NAME).py
	yosys $(QUIET) -p 'synth_ice40 -top main -blif $(NAME).blif' $(NAME).v
	arachne-pnr $(QUIET) -d $(DEVICE) -o $(NAME).txt -p $(PCF) $(NAME).blif
	icepack $(NAME).txt $(NAME).bin

upload: $(NAME).bin
	iceprog $(NAME).bin

upload_mac: $(NAME).bin
	sudo kextunload -b com.apple.driver.AppleUSBFTDI
	iceprog $(NAME).bin
	sudo kextload -b com.apple.driver.AppleUSBFTDI

sim_tx: sim_tx.cpp
	verilator -Wall --cc uart_transmitter.v --exe sim_tx.cpp
	cd obj_dir && make -j -f Vuart_transmitter.mk Vuart_transmitter
	./obj_dir/Vuart_transmitter

clean:
	rm -f *.bin *.txt *.blif *.rpt *.pcf *.v

.PHONY: all explain install clean
