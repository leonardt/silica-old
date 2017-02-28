from silica import fsm, Input, Output

def downsample(size_x, size_y):
    @fsm
    def _downsample(_input : Input, _output : Output, valid : Output):
        while True:
            for y in range(0, size_y):
                for x in range(0, size_x):
                    _output = _input
                    valid   = x % 2
                    yield
    return _downsample
