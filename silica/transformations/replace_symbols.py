import ast
from copy import deepcopy


class SymbolReplacer(ast.NodeTransformer):
    def __init__(self, symbol_table, ctx):
        self.symbol_table = symbol_table
        self.ctx = ctx

    def visit_Name(self, node):
        if node.id in self.symbol_table and (self.ctx is None or 
                isinstance(node.ctx, self.ctx)):
            return deepcopy(self.symbol_table[node.id])
        return node

def replace_symbols(tree, symbol_table, ctx=None):
    return SymbolReplacer(symbol_table, ctx).visit(tree)
