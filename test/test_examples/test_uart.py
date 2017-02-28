from subprocess import call
import filecmp
import os

def test():
    file_dir = os.path.dirname(__file__)
    package_dir = os.path.dirname(os.path.dirname(file_dir))
    call(['python3', os.path.join(package_dir, 'examples/uart/uart.py')])
    assert filecmp.cmp(os.path.join(package_dir, "examples/uart/uart_transmitter.v"), 
                       os.path.join(file_dir, "uart_gold/uart_transmitter.v"), shallow=False)
    assert filecmp.cmp(os.path.join(package_dir, "examples/uart/uart_receiver.v"), 
                       os.path.join(file_dir, "uart_gold/uart_receiver.v"), shallow=False)
    assert filecmp.cmp(os.path.join(package_dir, "examples/uart/baud_tx.v"), 
                       os.path.join(file_dir, "uart_gold/baud_tx.v"), shallow=False)
    assert filecmp.cmp(os.path.join(package_dir, "examples/uart/baud_rx.v"), 
                       os.path.join(file_dir, "uart_gold/baud_rx.v"), shallow=False)

