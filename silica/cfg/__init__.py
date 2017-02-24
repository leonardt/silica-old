import ast
import astor
from silica.cfg.types import Block, BasicBlock, Yield, Branch
from silica.transformations import specialize_constants
import tempfile
from copy import deepcopy


class ControlFlowGraph(ast.NodeVisitor):

    def __init__(self, ast):
        super()
        self.blocks = []
        self.curr_block = None
        self.curr_yield_id = 0

        self.visit(ast)
        self.bypass_conds()

    def collect_constant_assigns(self, statements):
        constant_assigns = {}
        for stmt in statements:
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Num) and len(stmt.targets) == 1:
                    if isinstance(stmt.targets[0], ast.Name):
                        constant_assigns[stmt.targets[0].id] = stmt.value.n
                    elif stmt.targets[0].name in constant_assigns:
                        del constant_assigns[stmt.targets[0].id] 
        return constant_assigns

    def bypass_conds(self):
        for block in self.blocks:
            if isinstance(block, BasicBlock) and \
               isinstance(block.outgoing_edge[0], Branch):
                constants = self.collect_constant_assigns(block.statements)
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

    def get_head_yield(self):
        for block in self.blocks:
            if isinstance(block, Yield) and block.yield_id == 0:
                return block
        assert False, "All CFGs should have at least 1 yield"

    def new_yield(self):
        block = Yield()
        block.yield_id = self.curr_yield_id
        self.curr_yield_id += 1
        self.blocks.append(block)
        return block

    def add_edge(self, source, sink, label=""):
        source.add_outgoing_edge(sink, label)
        sink.add_incoming_edge(source, label)
        # self.edges.append((source, sink, label))

    def add_true_edge(self, source, sink):
        assert isinstance(source, Branch)
        source.add_outgoing_edge(sink, "T")
        source.true_edge = sink
        sink.add_incoming_edge(source, "T")

    def add_false_edge(self, source, sink):
        assert isinstance(source, Branch)
        source.add_outgoing_edge(sink, "F")
        source.false_edge = sink
        sink.add_incoming_edge(source, "F")

    def outgoing_edges(block):
        edges = []
        for source, _, _ in self.edges:
            if source == block:
                edges.append(source)
        return edges

    def process_stmt(self, stmt):
        # TODO: Should be able to refactor this to reuse logic for "branching"
        # nodes
        if isinstance(stmt, ast.While):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            # self.curr_block.add(ast.If(stmt.test, [], []))
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_true_edge(old_block, self.curr_block)
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            self.add_edge(self.curr_block, old_block)
            self.curr_block = self.get_new_block()
            self.add_false_edge(old_block, self.curr_block)
        elif isinstance(stmt, (ast.If,)):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_true_edge(old_block, self.curr_block)
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            end_then_block = self.curr_block
            if len(stmt.orelse) > 0:
                self.curr_block = self.get_new_block()
                self.add_edge(old_block, self.curr_block)
                for sub_stmt in stmt.body:
                    self.process_stmt(sub_stmt)
                end_else_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_edge(end_then_block, self.curr_block)
            if len(stmt.orelse) > 0:
                self.add_edge(end_else_block, self.curr_block)
            else:
                self.add_false_edge(old_block, self.curr_block)
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Yield):
                old_block = self.curr_block
                self.curr_block = self.new_yield()
                self.add_edge(old_block, self.curr_block)
                old_block = self.curr_block
                self.curr_block = self.get_new_block()
                self.add_edge(old_block, self.curr_block)
            elif isinstance(stmt.value, ast.Str): 
                # Docstring, ignore
                pass
            else:
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
                    self.add_edge(source, sink, source_label)
                    if source_label == "F":
                        source.false_edge = sink
                    elif source_label == "T":
                        source.true_edge = sink
                    else:
                        assert False
                else:
                    assert len(block.outgoing_edges) == 0
            else:
                for sink, sink_label in block.outgoing_edges:
                    self.add_edge(source, sink, source_label)

    def consolidate_empty_blocks(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, BasicBlock) and len(block.statements) == 0:
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def remove_if_trues(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, Branch) and (isinstance(block.cond, ast.NameConstant) \
                    and block.cond.value == True):
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def visit_FunctionDef(self, node):
        self.curr_block = self.get_new_block()
        for stmt in node.body:
            self.process_stmt(stmt)
        self.consolidate_empty_blocks()
        self.remove_if_trues()

    def render(self):
        from graphviz import Digraph
        dot = Digraph(name="top")
        for block in self.blocks:
            if isinstance(block, Branch):
                label = "if " + astor.to_source(block.cond)
                dot.node(str(id(block)), label.rstrip(), {"shape": "invhouse"})
            elif isinstance(block, Yield):
                label = "yield"
                dot.node(str(id(block)), label.rstrip(), {"shape": "oval"})
            else:
                label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                dot.node(str(id(block)), label.rstrip(), {"shape": "box"}) 
        # for source, sink, label in self.edges:
            for sink, label in block.outgoing_edges:
                dot.edge(str(id(block)), str(id(sink)), label)


        dot.render(tempfile.mktemp("gv"), view=True)
