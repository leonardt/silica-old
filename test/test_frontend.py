from magma import *
from mantle import *
from silica import fsm


def test_good_arguments():
    try:
        @fsm
        def func(a : In(Bit), b : Out(Bit)):
            while True:
                a = b
                yield
    except Exception as e:
        assert False, "This should not throw an exception," \
                      " got \"{}: {}\"".format(e.__class__.__name__, e)


def test_bad_arguments():
    try:
        @fsm
        def func(a : In(Bit), b : 3):
            while True:
                a = b
                yield
        assert False, "This should throw an exception"
    except Exception as e:
        assert str(e) == "Invalid type (3) for argument b"
