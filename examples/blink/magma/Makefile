NAME = blink

DEVICE = 1k
QUIET = -q

$(NAME).bin: $(NAME).py
	python3 $(NAME).py
	yosys $(QUIET) -p 'synth_ice40 -top main -blif $(NAME).blif' $(NAME).v
	arachne-pnr $(QUIET) -d $(DEVICE) -o $(NAME).txt -p $(NAME).pcf $(NAME).blif
	icepack $(NAME).txt $(NAME).bin

upload: $(NAME).bin
	iceprog $(NAME).bin

upload_mac: $(NAME).bin
	sudo kextunload -b com.apple.driver.AppleUSBFTDI
	iceprog $(NAME).bin
	sudo kextload -b com.apple.driver.AppleUSBFTDI

clean:
	rm -f *.bin *.txt *.blif *.rpt *.pcf *.v

.PHONY: all explain install clean
