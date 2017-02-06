import ast
import astor
import inspect
import textwrap
from silica.python_backend import PyFSM
from silica.cfg import ControlFlowGraph
from silica.ast_utils import *
from silica.transformations import desugar_for_loops

class FSM:
    def __init__(self, f):
        tree = get_ast(f)
        tree = desugar_for_loops(tree)
        cfg = ControlFlowGraph(tree)
        cfg.render()

def fsm(mode_or_fn):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn)
            else:
                return FSM(fn)
        return wrapped
    return FSM(mode_or_fn)

