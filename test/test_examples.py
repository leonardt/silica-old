from subprocess import call
import filecmp
import os

file_dir = os.path.dirname(__file__)
package_dir = os.path.dirname(file_dir)

def test_uart():
    call(['python3', os.path.join(package_dir, 'examples/uart/uart.py')])
    assert call(['make', '-C', os.path.join(package_dir, 'examples/uart'), 'sim_tx']) == 0

def test_vga():
    assert call(['make', '-C', os.path.join(package_dir, 'examples/vga'), 'sim_vga']) == 0
