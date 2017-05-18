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
from silica.code_gen import Source
import silica.ast_utils as ast_utils
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


class ComparesWithIncrementsSpecializer(ast.NodeTransformer):
    def visit_Compare(self, node):
        if len(node.comparators) == 1:
            if isinstance(node.comparators[0], ast.Num):
                if isinstance(node.left, ast.BinOp) and isinstance(node.left.right, ast.Num):
                    if isinstance(node.left.op, ast.Add):
                        node.comparators[0].n -= node.left.right.n
                    else:
                        raise NotImplementedError()
                    node.left = node.left.left
        return node


def specialize_compares_with_increments(tree):
    return ComparesWithIncrementsSpecializer().visit(tree)


def FSM(f, backend, clock_enable=False, render_cfg=False):
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

        local_vars = list(sorted(loopvars))
        cfg = ControlFlowGraph(tree, clock_enable, local_vars)
        if render_cfg:
            cfg.render()  # pragma: no cover
        source = Source()
        num_yields = cfg.curr_yield_id
        yield_width = (num_yields - 1).bit_length()

        local_vars.append(("yield_state", yield_width))
        outputs = ast_utils.get_outputs_from_func(tree)

        num_states = len(cfg.paths)
        state_width = (num_states - 1).bit_length()
        source.add_line("state = Register({}, ce={})".format(num_states, clock_enable))
        DEBUG_STATE = False
        if DEBUG_STATE:
            source.add_line("wire(state.O, state_out)")
        source.add_line("wire(state.CE, CE)")
        replace_symbol_table = {}
        for var, width in local_vars + outputs:
            source.add_line("{}_reg = Register({}, ce={})".format(var, width, clock_enable))
            source.add_line("wire({}_reg.CE, CE)".format(var))
            if (var, width) in outputs:
                source.add_line("wire({var}_reg.O, {var})".format(var=var))
            replace_symbol_table[var] = ast.Attribute(ast.Name(var + "_reg", ast.Load()), "O", ast.Load())
            source.add_line("{}_next = Or({}, {})".format(var, num_states, width))
            source.add_line("wire({var}_next.O, {var}_reg.I)".format(var=var))
        for i, path in enumerate(cfg.paths):
            state_info = path[-1]
            state_info.statements = [replace_symbols(statement, replace_symbol_table, ast.Load) for statement in state_info.statements]
            curr = state_info.yield_state
            for cond in state_info.conds:
                curr = ast.BinOp(curr, ast.BitAnd(), cond)
            for var, _ in local_vars + outputs:
                symbol_table = {
                    var: ast.Attribute(ast.Name(var + "_next", ast.Load()), "O", ast.Load())
                }
                curr = replace_symbols(curr, symbol_table, ast.Load)
            source.add_line("state.I[{}] = {}".format(i, astor.to_source(curr).rstrip()))
        for var, width in local_vars + outputs:
            for i, path in enumerate(cfg.paths):
                source.add_line("{}_{} = And(2, {})".format(var, i, width))
                source.add_line("wire({var}_{i}.O, {var}_next.I{i})".format(var=var, i=i))
                if width > 1:
                    for j in range(width):
                        source.add_line("wire(state.O[{i}], {var}_{i}.I0[{j}])".format(i=i, var=var, j=j))
                else:
                    source.add_line("wire(state.O[{i}], {var}_{i}.I0)".format(i=i, var=var))
                state_info = path[-1]
                result = [statement for statement in  state_info.statements if var in collect_names(statement, ast.Store)]
                assert len(result) <= 1, [astor.to_source(s).rstrip() for s in result]
                if len(result) == 0:
                    source.add_line("wire({var}_reg.O, {var}_{i}.I1)".format(var=var, i=i))
                else:
                    statement = result[-1]  # TODO: Should we use last connect semantics?
                    symbol_table = {
                        var: ast.Attribute(ast.Name("{}_{}".format(var, i), ast.Load()), "I1", ast.Store())
                    }
                    statement = replace_symbols(statement, symbol_table, ast.Store)
                    source.add_line(astor.to_source(statement).rstrip())


        print(source)
        tree.body = ast.parse(str(source)).body
        tree.decorator_list = [ast.Name("circuit", ast.Load())]
        if clock_enable:
            tree.args.args.append(ast.arg("CE", ast.parse("In(Bit)").body[0].value))
        if DEBUG_STATE:
            tree.args.args.append(ast.arg("state_out", ast.parse("Out(Array({}, Bit))".format(num_states)).body[0].value))
        tree = specialize_compares_with_increments(tree)
        print(astor.to_source(tree))
        source, name = process_circuit_ast(tree)
        for i, line in enumerate(source.splitlines()):
            print("{} {}".format(i + 1, line))
        exec(source)
        return eval(name)


def fsm(mode_or_fn="verilog", clock_enable=False, render_cfg=False):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, mode_or_fn, clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn, "TODO: REMOVE THIS PARAM", clock_enable, render_cfg)

