import copy
import ast
import astor
import inspect
import textwrap
from silica.python_backend import PyFSM
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
from silica.ast_utils import *
from silica.transformations import desugar_for_loops
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


class Path:
    def __init__(self, blocks):
        self.blocks = blocks[1:-1]
        self.source_yield = blocks[0]
        self.sink_yield = blocks[-1]

    def contains_always_false_branch(self):
        symbol_table = {}
        for block in self.blocks:
            if isinstance(block, BasicBlock):
                for stmt in block.statements:
                    if isinstance(stmt, ast.Assign) and \
                        isinstance(stmt.value, ast.Num) and \
                        len(stmt.targets) == 1 and \
                        isinstance(stmt.targets[0], ast.Name):
                            symbol_table[stmt.targets[0].id] = stmt.value.n
                    elif isinstance(stmt, ast.Compare):
                        tree = deepcopy(stmt)
                        for symbol, value in symbol_table.items():
                            if contains_symbol(tree, symbol):
                                tree = specialize_symbol(tree, symbol, value)
                        try:
                            if eval(astor.to_source(tree)) is False:
                                return True
                        except NameError as e:
                            pass
        return False

def find_paths(block):
    if isinstance(block, Yield):
        return [[block]]
    paths = []
    if isinstance(block, Branch):
        new_block = BasicBlock()
        new_block.add(ast.Compare(block.cond, [ast.Eq()], [ast.NameConstant(True)]))
        for path in find_paths(block.true_edge):
            paths.append([new_block] + path)

        if block.false_edge is not None:
            new_block = BasicBlock()
            new_block.add(ast.Compare(block.cond, [ast.Eq()], [ast.NameConstant(False)]))
            for path in find_paths(block.false_edge):
                paths.append([new_block] + path)

    else:
        for sink, _ in block.outgoing_edges:
            for path in find_paths(sink):
                paths.append([block] + path)
    return paths


def find_paths_between_yields(cfg):
    paths = []
    for block in cfg.blocks:
        if isinstance(block, Yield):
            for sink, _ in block.outgoing_edges:
                paths.extend([[block] + path for path in  find_paths(sink)])
    return [Path(x) for x in paths]

def filter_impossible_paths(paths):
    return [path for path in paths if not path.contains_always_false_branch()]

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
            if node.targets[0].value.id not in self.paramaters:
                raise NotImplementedError()
        else:
            raise NotImplementedError()


def collect_local_variables(tree):
    collector = LocalVariableCollector()
    collector.visit(tree)
    return collector.local_variables

class FSM:
    def __init__(self, f, clock_enable=False, render_cfg=False):
        tree = get_ast(f)
        name = tree.name
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
        local_vars = collect_local_variables(tree)
        tree = desugar_for_loops(tree)
        cfg = ControlFlowGraph(tree)
        if render_cfg:
            cfg.render()
        tree = convert_to_fsm_ir(name, cfg, params, local_vars, clock_enable)

        # prog  = "module foo({}, input CLKIN)\n".format(", ".join(params))
        # prog += "reg state = 0;\n"
        # for variable in local_vars:
        #     prog += "reg {};\n".format(variable)
        # prog += "always @(posedge CLKIN) begin\n"
        # prog += "    case (state)\n"
        # tab = "    "
        # for block in cfg.blocks:
        #     if isinstance(block, Yield):
        #         prog += tab + "{}:\n".format(block.yield_id)
        #         assert len(block.outgoing_edges) == 1, "Yield should only have one exit"
        #         for line in _compile(list(block.outgoing_edges)[0][0]).splitlines():
        #             prog += tab * 2 + line + "\n"
        # prog += "end\n"
        # prog += "endmodule"
        # print(prog)


def fsm(mode_or_fn="", clock_enable=False, render_cfg=False):
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable, render_cfg)
            else:
                return FSM(fn, clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn)

