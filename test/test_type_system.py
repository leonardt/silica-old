from silica import fsm, Input, Output, TypeError


def test_write_to_input():
    try:
        @fsm
        def write_to_input(a : Input, b : Output):
            while True:
                yield
                b = a
                a = 1
        assert False, "Program should throw TypeError"
    except TypeError as e:
        assert str(e) == "Cannot write to `a` with type Input"


def test_read_from_output():
    try:
        @fsm
        def read_from_output(a : Output, b : Output):
            while True:
                yield
                a = b
        assert False, "Program should throw TypeError"
    except TypeError as e:
        assert str(e) == "Cannot read from `b` with type Output"


def test_mismatched_width():
    try:
        @fsm
        def bad_width(a : Input[4], b : Output[3]):
            while True:
                yield
                b = a + 1
        assert False, "Program should throw TypeError"
    except TypeError as e:
        assert str(e) == "Mismatched width, trying to assign expression `{}` of width {} to variable `{}` of width {}".format("(a + 1)", 4, "b", 3)
