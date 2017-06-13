import magma
import copy
import ast
import astor
import inspect
import textwrap
from silica.backend import PyFSM
import silica.backend
import silica.backend.verilog as verilog
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
import silica.ast_utils as ast_utils
from silica.transformations import desugar_for_loops, desugar_yield_from_range, \
    specialize_constants, replace_symbols, constant_fold
from silica.visitors import collect_names
from silica.code_gen import Source
import silica.ast_utils as ast_utils
import os
from copy import deepcopy


def round_to_next_power_of_two(x):
    return 1<<(x-1).bit_length()


def FSM(f, func_locals, func_globals, backend, clock_enable=False, render_cfg=False):
        constants = {}
        for name, value in func_locals.items():
            if isinstance(value, (int, )):
                constants[name] = value

        _file, line_no = astor.code_to_ast.get_file_info(f)
        file_dir = os.path.dirname(_file)
        # `ast_utils.get_ast` returns a module so grab first statement in body
        tree = ast_utils.get_ast(f).body[0]  
        func_name = tree.name

        local_vars = set()
        tree           = specialize_constants(tree, constants)
        tree           = constant_fold(tree)
        tree, loopvars = desugar_yield_from_range(tree)
        local_vars.update(loopvars)
        tree, loopvars = desugar_for_loops(tree)
        local_vars.update(loopvars)

        local_vars = list(sorted(loopvars))
        cfg = ControlFlowGraph(tree, clock_enable)
        if render_cfg:
            cfg.render()  # pragma: no cover
        if backend == "magma":
            return silica.backend.magma.compile(cfg, local_vars, tree, clock_enable, func_globals, func_locals)
        elif backend == "verilog":
            return silica.backend.verilog.compile(cfg, local_vars, tree, clock_enable, func_globals, func_locals, file_dir)
        raise NotImplementedError(backend)
        # return backend.compile(cfg)


def fsm(mode_or_fn="verilog", clock_enable=False, render_cfg=False):
    stack = inspect.stack()
    func_locals = stack[1].frame.f_locals
    func_globals = stack[1].frame.f_globals
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, func_locals, func_globals, mode_or_fn, clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn, func_locals, func_globals, "magma", clock_enable, render_cfg)

