import ast

class NameCollector(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_Name(self, node):
        self.names.add(node.id)


def collect_names(tree):
    visitor = NameCollector()
    visitor.visit(tree)
    return visitor.names
