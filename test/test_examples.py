from magma import *
from magma.python_simulator import PythonSimulator
from magma.scope import Scope

def test_uart():
    import sys
    sys.path.append('../examples')
    from examples.uart.uart import main, uart

    simulator = PythonSimulator(main)
    # TODO: Why do we need to warm up with two clock cycles?
    for _ in range(2):
        for j in range(103 * 2):
            simulator.step()
            simulator.evaluate()
    scope = Scope()
    expected = [0] + int2seq(85, 8) + [1]
    for h in range(2):
        actual = []
        for _ in range(len(expected)):
            for j in range(103 * 2):
                simulator.step()
                simulator.evaluate()
            actual.append(int(simulator.get_value(uart.tx, scope)))
        assert expected == actual, str(expected) + str(actual)

if __name__ == '__main__':
    test_uart()
