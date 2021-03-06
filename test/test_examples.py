from magma import *
from magma.python_simulator import PythonSimulator
from magma.scope import Scope
import sys
# Add the examples directory to path so we can import them
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "examples"))


def test_uart():
    import uart.magma.uart as uart_example
    simulator = PythonSimulator(uart_example.main)
    # TODO: Why do we need to warm up with two clock cycles?
    for _ in range(2):
        for j in range(103 * 2):
            simulator.step()
            simulator.evaluate()
    scope = Scope()
    expected_bytes = []
    for char in uart_example.message:
        expected_bytes.append([0] + int2seq(ord(char), 8) + [1, 1])  # Extra stop bit because the example holds the line high an extra buad tick
    for expected in expected_bytes[:2]:  # check only first 4 because it's slow
        actual = []
        for _ in range(11):
            for j in range(103 * 2):
                simulator.step()
                simulator.evaluate()
            actual.append(int(simulator.get_value(uart_example.uart.tx, scope)))
        assert expected == actual, str(expected) + str(actual)

if __name__ == '__main__':
    test_uart()
