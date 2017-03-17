sim_vga: sim_vga.cpp
	# python3 vga.py
	verilator -Wall --cc vga_timing.v --exe sim_vga.cpp
	cd obj_dir && make -j -f Vvga_timing.mk Vvga_timing
	./obj_dir/Vvga_timing

clean:
	rm -f ./obj_dir

.PHONY: sim_vga clean
