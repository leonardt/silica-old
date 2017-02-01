import ast
import astor
from graphviz import Digraph

class BasicBlock:
    def __init__(self):
        self.statements = []

    def add(self, stmt):
        self.statements.append(stmt)


class ControlFlowGraph(ast.NodeVisitor):

    def __init__(self, ast):
        super()
        self.blocks = []
        self.edges = []
        self.curr_block = None

        self.visit(ast)

    def get_new_block(self):
        block = BasicBlock()
        self.blocks.append(block)
        return block

    def add_edge(self, source, sink, label=""):
        self.edges.append((source, sink, label))

    def process_stmt(self, stmt):
        if isinstance(stmt, (ast.While, ast.For)):
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_edge(old_block, self.curr_block)
            self.curr_block.add(stmt)
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
            self.curr_block = self.get_new_block()
            self.add_edge(old_block, self.curr_block)
            self.curr_block.add(stmt)
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

    def consolidate_empty_blocks(self):
        new_blocks = []
        for block in self.blocks:
            if len(block.statements) > 0:
                new_blocks.append(block)
                continue
            sources = []
            sinks = []
            for source, sink, label in self.edges:
                if sink == block:
                    sources.append((source, label))
            for source, sink, label in self.edges:
                if source == block:
                    sinks.append(sink)
            for source, label in sources:
                for sink in sinks:
                    self.add_edge(source, sink, label)
            self.edges = [x for x in self.edges if block not in x]
        self.blocks = new_blocks

    def visit_FunctionDef(self, node):
        self.curr_block = self.get_new_block()
        for stmt in node.body:
            self.process_stmt(stmt)
        self.consolidate_empty_blocks()

    def render(self):
        dot = Digraph(name="top")
        for block in self.blocks:
            label = ""
            for statement in block.statements:
                if isinstance(statement, (ast.While,)):
                    label += "while {}:".format(astor.to_source(statement.test).rstrip())
                elif isinstance(statement, (ast.For,)):
                    label += "for {} in {}:".format(astor.to_source(statement.target).rstrip(), astor.to_source(statement.iter).rstrip())
                elif isinstance(statement, (ast.If,)):
                    label += "if {}:".format(astor.to_source(statement.test).rstrip())
                else:
                    label += astor.to_source(statement)
                label += "\n"
            dot.node(str(id(block)), label.rstrip()) 
        for source, sink, label in self.edges:
            dot.edge(str(id(source)), str(id(sink)), label)


        dot.render("cfg.gv", view=True)
