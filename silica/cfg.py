import ast
import astor

class BasicBlock:
    def __init__(self):
        self.statements = []
        self.outgoing_edges = set()
        self.incoming_edges = set()

    def add(self, stmt):
        self.statements.append(stmt)

    def add_outgoing_edge(self, sink, label):
        self.outgoing_edges.add((sink, label))

    def add_incoming_edge(self, source, label):
        self.incoming_edges.add((source, label))

class Branch(BasicBlock):
    def __init__(self, cond):
        super().__init__()
        self.cond = cond


class ControlFlowGraph(ast.NodeVisitor):

    def __init__(self, ast):
        super()
        self.blocks = []
        self.curr_block = None

        self.visit(ast)

    def get_new_block(self):
        block = BasicBlock()
        self.blocks.append(block)
        return block

    def new_branch(self, test):
        block = Branch(test)
        self.blocks.append(block)
        return block

    def add_edge(self, source, sink, label=""):
        source.add_outgoing_edge(sink, label)
        sink.add_incoming_edge(source, label)
        # self.edges.append((source, sink, label))

    def outgoing_edges(block):
        edges = []
        for source, _, _ in self.edges:
            if source == block:
                edges.append(source)
        return edges

    def process_stmt(self, stmt):
        # TODO: Should be able to refactor this to reuse logic for "branching"
        # nodes
        if isinstance(stmt, (ast.While, ast.For)):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            # self.curr_block.add(ast.If(stmt.test, [], []))
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_edge(old_block, self.curr_block, label="T")
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            self.add_edge(self.curr_block, old_block)
            self.curr_block = self.get_new_block()
            self.add_edge(old_block, self.curr_block, label="F")
        elif isinstance(stmt, (ast.If,)):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_edge(old_block, self.curr_block, label="T")
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
                self.add_edge(old_block, self.curr_block, label="F")
        else:
            self.curr_block.add(stmt)

    def remove_block(self, block):
        for source, source_label in block.incoming_edges:
            source.outgoing_edges.remove((block, source_label))
        for sink, sink_label in block.outgoing_edges:
            sink.incoming_edges.remove((block, sink_label))
        for source, source_label in block.incoming_edges:
            for sink, sink_label in block.outgoing_edges:
                self.add_edge(source, sink, source_label)

    def consolidate_empty_blocks(self):
        new_blocks = []
        for block in self.blocks:
            if len(block.statements) > 0 or isinstance(block, Branch):
                new_blocks.append(block)
            else:
                self.remove_block(block)
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
                dot.node(str(id(block)), label.rstrip(), {"shape":"box"})
            else:
                label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                dot.node(str(id(block)), label.rstrip()) 
        # for source, sink, label in self.edges:
            for sink, label in block.outgoing_edges:
                dot.edge(str(id(block)), str(id(sink)), label)


        dot.render("cfg.gv", view=True)
