from silica import fsm, Input, Output

size_x = 100
size_y = 100

@fsm
def _downsample(_input : Input, _output : Output, valid : Output):
    while True:
        for y in range(0, size_y):
            for x in range(0, size_x):
                _output = _input
                valid   = x % 2
                yield
