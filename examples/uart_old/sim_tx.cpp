#include "Vuart_transmitter.h"
#include "verilated.h"
#include <cassert>

int main(int argc, char **argv, char **env) {
    Verilated::commandArgs(argc, argv);
    Vuart_transmitter* top = new Vuart_transmitter;
    top->CLKIN = 1;
    top->data = 0xBE;
    top->valid = 0;
    top->clock_enable = 1;

    top->CLKIN = 0;
    top->eval();
    top->CLKIN = 1;
    top->eval();
    assert(top->ready == 0);
    assert(top->tx == 1);

    top->valid = 1;
    top->CLKIN = 0;
    top->eval();
    top->CLKIN = 1;
    top->eval();
    assert(top->ready == 1);
    assert(top->tx == 1);

    top->CLKIN = 0;
    top->eval();
    top->CLKIN = 1;
    top->eval();
    assert(top->ready == 0);
    assert(top->tx == 0);

    for (int i = 0; i < 8; i++) {
        top->CLKIN = 0;
        top->eval();
        top->CLKIN = 1;
        top->eval();
        assert(top->tx == ((0xBE >> i) & 1));
    }

    top->CLKIN = 0;
    top->eval();
    top->CLKIN = 1;
    top->eval();
    assert(top->tx == 1);

    delete top;
    exit(0);
}
