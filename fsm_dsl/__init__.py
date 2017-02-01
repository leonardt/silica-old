from fsm_dsl.cfg import ControlFlowGraph
from fsm_dsl.ast_utils import *
from fsm_dsl.transformations import desugar_for_loops
from fsm_dsl.python_backend import PyFSM
from fsm_dsl.types import *

import ast
import astor
import inspect
import textwrap

class FSM:
    def __init__(self, f):
        tree = get_ast(f)
        tree = desugar_for_loops(tree)
        cfg = ControlFlowGraph(tree)
        cfg.render()

def fsm(mode):
    def wrapped(fn):
        if mode == "python":
            return PyFSM(fn)
        else:
            return FSM(fn)
    return wrapped
