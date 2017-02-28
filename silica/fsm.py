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


class CheckTreeContainsSymbol(ast.NodeVisitor):
    def __init__(self, symbol):
        self.symbol = symbol
        self.seen = False

    def visit_Name(self, node):
        if node.id == self.symbol:
            self.seen = True

def contains_symbol(tree, symbol):
    visitor = CheckTreeContainsSymbol(symbol)
    visitor.visit(tree)
    return visitor.seen

class SymbolSpecializer(ast.NodeTransformer):
    def __init__(self, symbol, value):
        self.symbol = symbol
        self.value = value

    def visit_Name(self, node):
        if node.id == self.symbol:
            return ast.Num(self.value)
        return node

def specialize_symbol(tree, symbol, value):
    tree = deepcopy(tree)
    return SymbolSpecializer(symbol, value).visit(tree)

def _compile(block):
    tab = "    "
    prog = ""
    if isinstance(block, Branch):
        prog += "if {} begin\n".format(astor.to_source(block.cond).rstrip())
        for line in _compile(block.true_edge).splitlines():
            prog += tab + line + "\n"
        prog += "end\n"
        if block.false_edge is not None:
            prog += "else begin\n"
            for line in _compile(block.false_edge).splitlines():
                prog += tab + line + "\n"
            prog += "end"
    elif isinstance(block, BasicBlock):
        for stmt in block.statements:
            prog += astor.to_source(stmt).rstrip() + ";\n"
        for edge, _ in block.outgoing_edges:
            for line in _compile(edge).splitlines():
                prog += line + "\n"
    elif isinstance(block, Yield):
        prog += "state = {};\n".format(block.yield_id)
    else:
        raise NotImplementedError(type(block))
    return prog

class LocalVariableCollector(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.local_variables = set()
        self.paramaters = set()

    def visit_FunctionDef(self, node):
        for arg in node.args.args:
            self.paramaters.add(arg.arg)
        [self.visit(s) for s in node.body]

    def visit_For(self, node):
        assert isinstance(node.target, ast.Name)
        if node.target.id not in self.paramaters:
            self.local_variables.add(node.target.id)
        [self.visit(s) for s in node.body]

    def visit_Assign(self, node):
        assert len(node.targets) == 1
        if isinstance(node.targets[0], ast.Name):
            if node.targets[0].id not in self.paramaters:
                self.local_variables.add(node.targets[0].id)
        elif isinstance(node.targets[0], ast.Subscript):
            pass
            # if node.targets[0].value.id not in self.paramaters:
            #     raise NotImplementedError()
        else:
            raise NotImplementedError()


def collect_local_variables(tree):
    collector = LocalVariableCollector()
    collector.visit(tree)
    return collector.local_variables

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
        # local_vars = collect_local_variables(tree)

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

