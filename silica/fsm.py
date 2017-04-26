import magma
from mantle.expressions import process_circuit_ast
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
    specialize_constants, replace_symbols
from silica.visitors import collect_names
from silica.type_checker import type_check
import os
from copy import deepcopy


def get_global_vars_for_func(fn):
    """
    inspect.getmembers() returns a list of (name, value) pairs.
    we are interested in name == __globals__
    """
    return [x for x in inspect.getmembers(fn) if x[0] == "__globals__"][0][1]


def round_to_next_power_of_two(x):
    return 1<<(x-1).bit_length()


class Source:
    def __init__(self):
        self._source = ""

    def add_line(self, line):
        self._source += line + "\n"

    def __str__(self):
        return self._source.rstrip()


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
        # Defer to magma type checking for now
        # type_check(tree)

        local_vars = list(sorted(loopvars))
        cfg = ControlFlowGraph(tree, clock_enable, local_vars)
        if render_cfg:
            cfg.render()  # pragma: no cover
        source = Source()
        num_states = len(cfg.paths)
        state_width = (num_states - 1).bit_length()
        source.add_line("yield_state = Register({})".format(state_width))
        mux_height = round_to_next_power_of_two(num_states)
        source.add_line("yield_state_mux = Mux({}, {})".format(mux_height, state_width))
        source.add_line("wire(yield_state.I, yield_state_mux.O)")
        source.add_line("wire(yield_state.O, yield_state_mux.S[:{}])".format(state_width))
        for i in range(num_states):
            # The final statement in the path is the next yield (skip the
            # state_info node which is the actual last item in the list
            # TODO: There should be a better interface, probably a Paths object
            next_state = cfg.paths[i][-2].yield_id
            source.add_line("wire(yield_state_mux.I{i}, int2seq({next_state}, {width}))".format(i=i, next_state=next_state, width=state_width))

        def process(var):
            source.add_line("{}_reg = Register({})".format(var, width))
            source.add_line("{}_mux = Mux({}, {})".format(var, mux_height, state_width))
            source.add_line("wire({}_reg.I, {}_mux.O)".format(var, var))
            source.add_line("wire({}_reg.O, {}_mux.S[:{}])".format(var, var, state_width))
            for i in range(num_states):
                state_info = cfg.paths[i][-1]
                result = [statement for statement in  state_info.statements if var in collect_names(statement, ast.Store)]
                assert len(result) <= 1, [astor.to_source(s).rstrip() for s in result]
                if len(result) == 0:
                    source.add_line("wire({var}.O, {var}_mux_.I[{i}])".format(var=var, i=i))
                else:
                    statement = result[0]
                    symbol_table = {
                        var: ast.Name(var + "_state_{}".format(i), ast.Store())
                    }
                    statement = replace_symbols(statement, symbol_table, ast.Store)
                    source.add_line(astor.to_source(statement).rstrip())
                    source.add_line("wire({var}_state_{i}, {var}_mux.I{i})".format(var=var, i=i))
        for var, width in local_vars:
            source.add_line("{} = Register({})".format(var, width))
            process(var)

        for arg in tree.args.args:
            var = arg.arg
            _type = eval(astor.to_source(arg.annotation), globals(), magma.__dict__)()
            if _type.isoutput():
                if isinstance(_type, magma.ArrayType):
                    width = _type.N
                elif isinstance(_type, magma.BitType):
                    width = 1
                else:
                    raise NotImplementedError(type(_type))
                process(var)
        tree.body = ast.parse(str(source)).body
        tree.decorator_list = [ast.Name("circuit", ast.Load())]
        print(astor.to_source(tree))
        source, _ = process_circuit_ast(tree)
        prog = "from magma import *\nfrom mantle import *\n" + source
        print(source)
        exec(prog)
        exit(1)


def fsm(mode_or_fn="verilog", clock_enable=False, render_cfg=False):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, mode_or_fn, clock_enable, render_cfg)
        return wrapped
