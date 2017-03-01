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


def test_mod():
    try:
        @fsm
        def bad_width(a : Input[4], b : Output[1]):
            while True:
                yield
                b = a % 1
    except TypeError as e:
        assert False, "Program should not throw TypeError"


def test_bool_op_width():
    try:
        @fsm
        def bad_width(a : Input[1], b : Input[2], c : Input[3], d : Output[2]):
            while True:
                yield
                d = a or b or c
        assert False, "Program should throw TypeError"
    except TypeError as e:
        assert str(e) == "Mismatched width, trying to assign expression `(a or b or c)` of width 3 to variable `d` of width 2"


def test_compare_width():
    try:
        @fsm
        def bad_width(a : Input[1], b : Input[2], c : Output[1]):
            while True:
                yield
                c = a < b
    except TypeError as e:
        assert False, "Program should not throw TypeError"


def test_subscript():
    try:
        @fsm
        def bad_width(a : Input[2], b : Input[2], c : Output[2]):
            while True:
                yield
                c[0] = a + b
    except TypeError as e:
        assert str(e) == "Mismatched width, trying to assign expression `(a + b)` of width 2 to variable `c[0]` of width 1"


def test_bad_read_from_subscript():
    try:
        @fsm
        def bad_width(a : Input[2], b : Input[2], c : Output[2]):
            while True:
                yield
                c[1] = c[0]
    except TypeError as e:
        assert str(e) == "Cannot read from `c` with type Output"


def test_bad_write_to_subscript():
    try:
        @fsm
        def bad_width(a : Input[2], b : Input[2], c : Output[2]):
            while True:
                yield
                b[1] = a[0]
    except TypeError as e:
        assert str(e) == "Cannot write to `b` with type Input"
