import copy
import ast
import astor
import inspect
import textwrap
from silica.backend import PyFSM
import silica.backend.verilog as verilog
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
import silica.ast_utils as ast_utils
from silica.transformations import desugar_for_loops, desugar_yield_from_range, \
    specialize_constants
from silica.type_checker import type_check
import os
from copy import deepcopy


def get_global_vars_for_func(fn):
    """
    inspect.getmembers() returns a list of (name, value) pairs.
    we are interested in name == __globals__
    """
    return [x for x in inspect.getmembers(fn) if x[0] == "__globals__"][0][1]

class FSM:
    def __init__(self, f, backend, clock_enable=False, render_cfg=False):
        # TODO: Instead of global namespace for function, should get the
        # current frame of the function definition (needed to support higher
        # order definitions with scoped/closure variables)
        func_globals = get_global_vars_for_func(f)
        constants = {}
        for name, value in func_globals.items():
            if isinstance(value, (int, )):
                constants[name] = value

        _file, line_no = astor.code_to_ast.get_file_info(f)
        file_dir = os.path.dirname(_file)
        # `ast_utils.get_ast` returns a module so grab first statement in body
        tree = ast_utils.get_ast(f).body[0]  
        func_name = tree.name

        local_vars = set()
        tree           = specialize_constants(tree, constants)
        tree, loopvars = desugar_yield_from_range(tree)
        local_vars.update(loopvars)
        tree, loopvars = desugar_for_loops(tree)
        local_vars.update(loopvars)
        type_check(tree)

        local_vars = list(sorted(loopvars))
        cfg = ControlFlowGraph(tree)
        if render_cfg:
            cfg.render()  # pragma: no cover
        if backend == "verilog":
            tree = verilog.compile(func_name, tree, cfg, local_vars, clock_enable, file_dir)
        else:
            raise NotImplementedError(backend)  # pragma: no cover


def fsm(mode_or_fn="verilog", clock_enable=False, render_cfg=False):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, mode_or_fn, clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn, "verilog", clock_enable, render_cfg)

