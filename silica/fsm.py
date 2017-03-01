import copy
import ast
import astor
import inspect
import textwrap
from silica.python_backend import PyFSM
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
from silica.ast_utils import *
from silica.transformations import desugar_for_loops, desugar_yield_from_range, \
    specialize_constants
from silica.type_system import type_check
import os
from silica.fsm_ir import *
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

        _file, line_no = astor.code_to_ast.get_file_info(f)
        file_dir = os.path.dirname(_file)
        # `ast_utils.get_ast` returns a module so grab first statement in body
        tree = ast_utils.get_ast(f).body[0]  
        func_name = tree.name
        params = []
        for arg in tree.args.args:
            if isinstance(arg.annotation, ast.Subscript):
                assert isinstance(arg.annotation.slice.value, ast.Num)
                assert isinstance(arg.annotation.value, ast.Name)
                typ = Subscript(Symbol(arg.annotation.value.id.lower()), 
                                Slice(Constant(arg.annotation.slice.value.n - 1), Constant(0)))
            else:
                typ = Symbol(arg.annotation.id.lower())
            params.append(Declaration(typ, Symbol(arg.arg)))

        if clock_enable:
            params.append(Declaration(Symbol("input"), Symbol("clock_enable")))

        constants = {}
        for name, value in func_globals.items():
            if isinstance(value, (int, )):
                constants[name] = value
        tree           = specialize_constants(tree, constants)
        tree, loopvars = desugar_yield_from_range(tree)
        tree           = desugar_for_loops(tree)
        type_check(tree)

        # local_vars = set()
        # local_vars.update(loopvars)
        local_vars = list(sorted(loopvars))
        cfg = ControlFlowGraph(tree)
        if render_cfg:
            cfg.render()
        if backend == "verilog":
            tree = convert_to_fsm_ir(func_name, cfg, params, local_vars, clock_enable, file_dir)
        else:
            raise NotImplementedError(backend)


def fsm(mode_or_fn="verilog", clock_enable=False, render_cfg=False):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, mode_or_fn, clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn, "verilog", clock_enable, render_cfg)

