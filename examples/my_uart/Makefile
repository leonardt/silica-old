NAME = uart

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

clean:
	rm -f *.bin *.txt *.blif *.rpt

.PHONY: all explain install clean
