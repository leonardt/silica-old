from dsl import fsm

@fsm
def downsample(size_x, size_y):
    _output = None
    valid   = False
    for y in range(0, size_y):
        for x in range(0, size_x):
            _input  = yield _output, valid
            _output = _input
            valid   = x % 2

gen = downsample(100, 100)
for i in range(0, 5):
    print(gen.send(i))
