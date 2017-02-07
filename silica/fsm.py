import copy
import ast
import astor
import inspect
import textwrap
from silica.python_backend import PyFSM
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
from silica.ast_utils import *
from silica.transformations import desugar_for_loops

def find_paths(block):
    if isinstance(block, Yield):
        return [[]]
    paths = []
    for sink, _ in block.outgoing_edges:
        for path in find_paths(sink):
            paths.append([block] + path)
    return paths


def find_paths_between_yields(cfg):
    paths = []
    for block in cfg.blocks:
        if isinstance(block, Yield):
            for sink, _ in block.outgoing_edges:
                paths.extend(find_paths(sink))
    return paths


class FSM:
    def __init__(self, f):
        tree = get_ast(f)
        tree = desugar_for_loops(tree)
        cfg = ControlFlowGraph(tree)
        paths = find_paths_between_yields(cfg)
        for i, path in enumerate(paths):
            print("Path {}".format(i))
            for block in path:
                if isinstance(block, BasicBlock):
                    for stmt in block.statements:
                        print(astor.to_source(stmt).rstrip())
                elif isinstance(block, Branch):
                    print("BRANCH: " + astor.to_source(block.cond).rstrip())
            print()

def fsm(mode_or_fn):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn)
            else:
                return FSM(fn)
        return wrapped
    return FSM(mode_or_fn)

