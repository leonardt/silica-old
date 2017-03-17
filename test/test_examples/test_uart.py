from subprocess import call
import filecmp
import os

def test():
    file_dir = os.path.dirname(__file__)
    package_dir = os.path.dirname(os.path.dirname(file_dir))
    call(['python3', os.path.join(package_dir, 'examples/uart/uart.py')])
    assert call(['make', '-C', os.path.join(package_dir, 'examples/uart'), 'sim_tx']) == 0
