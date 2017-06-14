import tempfile
from copy import deepcopy

import ast
import astor
import magma

from silica.transformations import specialize_constants, replace_symbols, constant_fold
from silica.visitors import collect_names
from silica.cfg.types import BasicBlock, Yield, Branch, HeadBlock, State


def parse_arguments(arguments):
    """
    arguments : a list of ast.arg nodes each annotated with a magma In or Out type

    return    : a tuple (inputs, outputs), where inputs and outputs sets of
                strings containing the input and output arguments respectively
    """
    outputs = set()
    inputs = set()
    for arg in arguments:
        _type = eval(astor.to_source(arg.annotation), globals(), magma.__dict__)()
        if _type.isoutput():
            outputs.add(arg.arg)
        else:
            assert _type.isinput()
            inputs.add(arg.arg)
    return inputs, outputs


def add_edge(source, sink, label=""):
    """
    Add an edge between source and sink with label
    """
    source.add_outgoing_edge(sink, label)
    sink.add_incoming_edge(source, label)


def add_true_edge(source, sink):
    """
    Add an edge form source to sink with label="T" and set the `true_edge`
    attribute on source
    """
    assert isinstance(source, Branch)
    source.add_outgoing_edge(sink, "T")
    source.true_edge = sink
    sink.add_incoming_edge(source, "T")


def add_false_edge(source, sink):
    """
    Add an edge from source to sink with label="F" and set the `false_edge`
    attribute on source
    """
    assert isinstance(source, Branch)
    source.add_outgoing_edge(sink, "F")
    source.false_edge = sink
    sink.add_incoming_edge(source, "F")


class ControlFlowGraph:
    def __init__(self, tree):
        self.blocks = []
        self.curr_block = None
        self.curr_yield_id = 1

        inputs, outputs = parse_arguments(tree.args.args)
        self.build(tree)
        self.bypass_conds()
        try:
            paths = self.collect_paths_between_yields()
        except RecursionError as error:
            # Most likely infinite loop in CFG, TODO: should catch this with an analysis phase
            self.render()
            raise error
        paths = promote_live_variables(paths)
        paths, state_vars = append_state_info(paths, outputs, inputs)
        self.paths = paths
        self.state_vars = state_vars

        # render_paths_between_yields(self.paths)
        # exit()

    def build(self, func_def):
        assert isinstance(func_def, ast.FunctionDef)
        self.head_block = HeadBlock()
        self.blocks.append(self.head_block)
        self.curr_block = self.get_new_block()
        add_edge(self.head_block, self.curr_block)
        for stmt in func_def.body:
            self.process_stmt(stmt)
        self.consolidate_empty_blocks()
        self.remove_if_trues()


    def find_paths(self, block):
        if isinstance(block, Yield):
            return [[deepcopy(block)]]
        elif isinstance(block, BasicBlock):
            return [[deepcopy(block)] + path for path in self.find_paths(block.outgoing_edge[0])]
        elif isinstance(block, Branch):
            true_paths = [[deepcopy(block)] + path for path in self.find_paths(block.true_edge)]
            false_paths = [[deepcopy(block)] + path for path in self.find_paths(block.false_edge)]
            for path in true_paths:
                path[0].true_edge = path[1]
            for path in false_paths:
                path[0].false_edge = path[1]
            return true_paths + false_paths
        else:
            raise NotImplementedError(type(block))

    def collect_paths_between_yields(self):
        paths = []
        for block in self.blocks:
            if isinstance(block, (Yield, HeadBlock)):
                paths.extend([block] + path for path in self.find_paths(block.outgoing_edge[0]))
        return paths


    def bypass_conds(self):
        for block in self.blocks:
            if isinstance(block, BasicBlock) and \
               isinstance(block.outgoing_edge[0], Branch):
                constants = collect_constant_assigns(block.statements)
                branch = block.outgoing_edge[0]
                cond = deepcopy(branch.cond)
                cond = specialize_constants(cond, constants)
                try:
                    if eval(astor.to_source(cond)):
                        # FIXME: Interface violation, need a remove method from blocks
                        block.outgoing_edges = {(branch.true_edge, "")}
                    else:
                        block.outgoing_edges = {(branch.false_edge, "")}
                except NameError:
                    pass


    def get_new_block(self):
        block = BasicBlock()
        self.blocks.append(block)
        return block

    def new_branch(self, test):
        block = Branch(test)
        self.blocks.append(block)
        return block

    def new_yield(self):
        block = Yield()
        block.yield_id = self.curr_yield_id
        self.curr_yield_id += 1
        self.blocks.append(block)
        return block

    def process_stmt(self, stmt):
        if isinstance(stmt, (ast.While, ast.If)):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            add_edge(old_block, self.curr_block)
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            add_true_edge(old_block, self.curr_block)
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            if isinstance(stmt, ast.While):
                add_edge(self.curr_block, old_block)
                self.curr_block = self.get_new_block()
                add_false_edge(old_block, self.curr_block)
            elif isinstance(stmt, (ast.If,)):
                end_then_block = self.curr_block
                if stmt.orelse:
                    self.curr_block = self.get_new_block()
                    add_false_edge(old_block, self.curr_block)
                    for sub_stmt in stmt.orelse:
                        self.process_stmt(sub_stmt)
                    end_else_block = self.curr_block
                self.curr_block = self.get_new_block()
                add_edge(end_then_block, self.curr_block)
                if stmt.orelse:
                    add_edge(end_else_block, self.curr_block)
                else:
                    add_false_edge(old_block, self.curr_block)
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Yield):
                old_block = self.curr_block
                self.curr_block = self.new_yield()
                add_edge(old_block, self.curr_block)
                old_block = self.curr_block
                self.curr_block = self.get_new_block()
                add_edge(old_block, self.curr_block)
            elif isinstance(stmt.value, ast.Str):
                # Docstring, ignore
                pass
            else:  # pragma: no cover
                raise NotImplementedError(stmt.value)
        else:
            self.curr_block.add(stmt)

    def remove_block(self, block):
        for source, source_label in block.incoming_edges:
            source.outgoing_edges.remove((block, source_label))
        for sink, sink_label in block.outgoing_edges:
            sink.incoming_edges.remove((block, sink_label))
        for source, source_label in block.incoming_edges:
            if isinstance(source, Branch):
                if len(block.outgoing_edges) == 1:
                    sink, sink_label = list(block.outgoing_edges)[0]
                    add_edge(source, sink, source_label)
                    if source_label == "F":
                        source.false_edge = sink
                    elif source_label == "T":
                        source.true_edge = sink
                    else:  # pragma: no cover
                        assert False
                else:
                    assert not block.outgoing_edges
            else:
                for sink, sink_label in block.outgoing_edges:
                    add_edge(source, sink, source_label)

    def consolidate_empty_blocks(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, BasicBlock) and not block.statements:
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def remove_if_trues(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, Branch) and (isinstance(block.cond, ast.NameConstant) \
                    and block.cond.value is True):
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def render(self):  # pragma: no cover
        from graphviz import Digraph
        dot = Digraph(name="top")
        for block in self.blocks:
            if isinstance(block, Branch):
                label = "if " + astor.to_source(block.cond)
                dot.node(str(id(block)), label.rstrip(), {"shape": "invhouse"})
            elif isinstance(block, Yield):
                label = "yield"
                dot.node(str(id(block)), label.rstrip(), {"shape": "oval"})
            elif isinstance(block, BasicBlock):
                label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                dot.node(str(id(block)), label.rstrip(), {"shape": "box"})
            elif isinstance(block, HeadBlock):
                label = "Initial"
                dot.node(str(id(block)), label.rstrip(), {"shape": "doublecircle"})
            else:
                raise NotImplementedError(type(block))
        # for source, sink, label in self.edges:
            for sink, label in block.outgoing_edges:
                dot.edge(str(id(block)), str(id(sink)), label)


        file_name = tempfile.mktemp("gv")
        dot.render(file_name, view=True)
        # print(file_name)
        # exit()

def render_paths_between_yields(paths):  # pragma: no cover
    from graphviz import Digraph
    dot = Digraph(name="top")
    for i, path in enumerate(paths):
        prev = None
        for block in path:
            if isinstance(block, Branch):
                label = "if " + astor.to_source(block.cond)
                dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "invhouse"})
            elif isinstance(block, Yield):
                label = "yield {}".format(block.yield_id)
                dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "oval"})
            elif isinstance(block, BasicBlock):
                label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "box"})
            elif isinstance(block, HeadBlock):
                label = "Initial"
                dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "doublecircle"})
            elif isinstance(block, State):
                label = "{}".format(astor.to_source(block.yield_state).rstrip())
                if block.conds:
                    label += " && "
                label += " && ".join(astor.to_source(cond) for cond in block.conds)
                label += "\n"
                label += "\n".join(astor.to_source(statement) for statement in block.statements)
                dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "doubleoctagon"})
            else:
                raise NotImplementedError(type(block))
            if prev is not None:
                if isinstance(prev, Branch):
                    if block is prev.false_edge:
                        label = "F"
                    else:
                        label = "T"
                else:
                    label = ""
                dot.edge(str(i) + str(id(prev)), str(i) + str(id(block)), label)
            prev = block

    file_name = tempfile.mktemp("gv")
    dot.render(file_name, view=True)

def collect_constant_assigns(statements):
    constant_assigns = {}
    for stmt in statements:
        if isinstance(stmt, ast.Assign):
            if isinstance(stmt.value, ast.Num) and len(stmt.targets) == 1:
                if isinstance(stmt.targets[0], ast.Name):
                    constant_assigns[stmt.targets[0].id] = stmt.value.n
                else:
                    # TODO: This should already be guaranteed by a type checker
                    assert stmt.targets[0].name in constant_assigns, \
                           "Assigned to multiple constants"
    return constant_assigns


def promote_live_variables(paths):
    for path in paths:
        symbol_table = {}
        for block in path:
            if isinstance(block, BasicBlock):
                new_statements = []
                for statement in block.statements:
                    statement = replace_symbols(statement, symbol_table, ctx=ast.Load)
                    statement = constant_fold(statement)
                    if isinstance(statement, ast.Assign) and \
                       len(statement.targets) == 1 and \
                       isinstance(statement.targets[0], ast.Name):
                        symbol_table[statement.targets[0].id] = statement.value
                    new_statements.append(statement)
                block.statements = new_statements
            elif isinstance(block, Branch):
                block.cond = replace_symbols(block.cond, symbol_table, ctx=ast.Load)
                block.cond = constant_fold(block.cond)
    return paths

def append_state_info(paths, outputs, inputs):
    for path in paths:
        state = State()
        if isinstance(path[0], HeadBlock):
            yield_id = 0
        else:
            yield_id = path[0].yield_id
        state.yield_state = ast.Compare(
            ast.Name("yield_state", ast.Load()),
            [ast.Eq()],
            [ast.Num(yield_id)]
        )
        for i in range(1, len(path)):
            block = path[i]
            if isinstance(block, Branch):
                cond = block.cond
                if path[i + 1] is block.false_edge:
                    cond = ast.UnaryOp(ast.Invert(), cond)
                state.conds.append(cond)
        state.statements.append(ast.Assign(
            [ast.Name("yield_state", ast.Store())],
            ast.Num(path[-1].yield_id)
        ))
        path.append(state)
    state_vars = {"yield_state"}
    for path in paths:
        state = path[-1]
        for cond in state.conds:
            names = collect_names(cond)
            for name in names:
                if name not in outputs and \
                   name not in inputs:
                    state_vars.update(names)
    for path in paths:
        state = path[-1]
        seen = {"yield_state"}
        for block in path[:-1]:
            if isinstance(block, BasicBlock):
                for statement in block.statements:
                    if isinstance(statement, ast.Assign):
                        target = statement.targets[0]
                    elif isinstance(statement, ast.AugAssign):
                        target = statement.target
                    else:
                        raise NotImplementedError
                    if isinstance(target, ast.Name):
                        seen.add(target.id)
                    state.statements.append(statement)
    return paths, state_vars
