from silica.types import *
from silica.fsm import fsm

def inline(func):
    # TODO: Should we just inline by default?
    func.__silica_inline = True
    return func
