import os

from silica.code_gen import Source
from silica.transformations import desugar_for_loops, desugar_yield_from_range, \
    specialize_constants, replace_symbols, constant_fold
from silica.visitors import collect_names

import silica.ast_utils as ast_utils

from mantle.expressions import process_circuit_ast

import ast
import astor


# TODO: Factor this into transformations module
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

def compile(cfg, local_vars, tree, clock_enable, func_globals, func_locals):
    source = Source()

    # for statement in cfg.initial_statements:
    #     source.add_line(astor.to_source(statement).rstrip())
    num_yields = cfg.curr_yield_id
    yield_width = (num_yields - 1).bit_length()

    local_vars.append(("yield_state", yield_width))
    outputs = ast_utils.get_outputs_from_func(tree)

    num_states = len(cfg.states)
    state_width = (num_states - 1).bit_length()
    source.add_line("state = Register({}, ce={})".format(num_states, clock_enable))
    DEBUG_STATE = False
    if DEBUG_STATE:
        source.add_line("wire(state.O, state_out)")
    if clock_enable:
        source.add_line("wire(state.CE, CE)")
    replace_symbol_table = {}
    for var, width in local_vars + outputs:
        source.add_line("{}_reg = Register({}, ce={})".format(var, width, clock_enable))
        if clock_enable:
            source.add_line("wire({}_reg.CE, CE)".format(var))
        if (var, width) in outputs:
            source.add_line("wire({var}_reg.O, {var})".format(var=var))
        replace_symbol_table[var] = ast.Attribute(ast.Name(var + "_reg", ast.Load()), "O", ast.Load())
        source.add_line("{}_next = Or({}, {})".format(var, num_states, width))
        source.add_line("wire({var}_next.O, {var}_reg.I)".format(var=var))
    for i, state_info in enumerate(cfg.states):
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
        for i, state_info in enumerate(cfg.states):
            source.add_line("{}_{} = And(2, {})".format(var, i, width))
            source.add_line("wire({var}_{i}.O, {var}_next.I{i})".format(var=var, i=i))
            if width > 1:
                for j in range(width):
                    source.add_line("wire(state.O[{i}], {var}_{i}.I0[{j}])".format(i=i, var=var, j=j))
            else:
                source.add_line("wire(state.O[{i}], {var}_{i}.I0)".format(i=i, var=var))
            result = [statement for statement in  state_info.statements if var in collect_names(statement, ast.Store)]
            # assert len(result) <= 1, [astor.to_source(s).rstrip() for s in result]
            if len(result) == 0:
                source.add_line("wire({var}_reg.O, {var}_{i}.I1)".format(var=var, i=i))
            else:
                statement = result[-1]  # TODO: Should we use last connect semantics?
                symbol_table = {
                    var: ast.Attribute(ast.Name("{}_{}".format(var, i), ast.Load()), "I1", ast.Store())
                }
                statement = replace_symbols(statement, symbol_table, ast.Store)
                source.add_line(astor.to_source(statement).rstrip())


    # print(source)
    tree.body = ast.parse(str(source)).body
    tree.decorator_list = [ast.Name("circuit", ast.Load())]
    if clock_enable:
        tree.args.args.append(ast.arg("CE", ast.parse("In(Bit)").body[0].value))
    if DEBUG_STATE:
        tree.args.args.append(ast.arg("state_out", ast.parse("Out(Array({}, Bit))".format(num_states)).body[0].value))
    tree = specialize_compares_with_increments(tree)
    if int(os.environ.get("SILICA_DEBUG", "0")) >= 1:
        print(astor.to_source(tree))
    source, name = process_circuit_ast(tree)
    if int(os.environ.get("SILICA_DEBUG", "0")) >= 2:
        for i, line in enumerate(source.splitlines()):
            print("{} {}".format(i + 1, line))
    exec(source, func_globals, func_locals)
    return eval(name, func_globals, func_locals)
