import ast
import astor
from silica.transformations import specialize_constants
from silica.cfg.types import Block, BasicBlock, Yield, Branch, HeadBlock
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
        self.promote_live_variables()
        paths = self.collect_paths_between_yields()
        self.render_paths_between_yields(paths)
        exit()

    def promote_live_variables(self):
        for block in self.blocks:
            if isinstance(block, BasicBlock):
                for statement in block.statements:


    def find_paths(self, block):
        if isinstance(block, Yield):
            return [[block]]
        elif isinstance(block, BasicBlock):
            return [[block] + path for path in self.find_paths(block.outgoing_edge[0])]
        elif isinstance(block, Branch):
            return [[block] + path for path in self.find_paths(block.true_edge)] + \
                   [[block] + path for path in self.find_paths(block.false_edge)]
        else:
            raise NotImplementedError(type(block))

    def collect_paths_between_yields(self):
        paths = []
        for block in self.blocks:
            if isinstance(block, (Yield, HeadBlock)):
                paths.extend([block] + path for path in self.find_paths(block.outgoing_edge[0]))
        return paths


    def collect_constant_assigns(self, statements):
        constant_assigns = {}
        for stmt in statements:
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Num) and len(stmt.targets) == 1:
                    if isinstance(stmt.targets[0], ast.Name):
                        constant_assigns[stmt.targets[0].id] = stmt.value.n
                    else:
                        # TODO: This should already be guaranteed by a type checker
                        assert stmt.targets[0].name in constant_assigns, "Assigned to multiple constants"
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
                except NameError as e:
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
                self.add_false_edge(old_block, self.curr_block)
                for sub_stmt in stmt.orelse:
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
                    self.add_edge(source, sink, source_label)
                    if source_label == "F":
                        source.false_edge = sink
                    elif source_label == "T":
                        source.true_edge = sink
                    else:  # pragma: no cover
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
        self.head_block = HeadBlock()
        self.blocks.append(self.head_block)
        self.curr_block = self.get_new_block()
        self.add_edge(self.head_block, self.curr_block)
        for stmt in node.body:
            self.process_stmt(stmt)
        self.consolidate_empty_blocks()
        self.remove_if_trues()

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

    def render_paths_between_yields(self, paths):  # pragma: no cover
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
