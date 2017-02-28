import ast


class TypeError(RuntimeError):
    pass


class _Type:
    def __init__(self, width):
        self.width = width


class Output(_Type):
    pass


class Input(_Type):
    pass


def get_type(typ, width):
    return eval("{}({})".format(typ, width))


class TypeChecker(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.symbol_table = {}

    def visit_FunctionDef(self, node):
        for arg in node.args.args:
            if isinstance(arg.annotation, ast.Subscript):
                assert isinstance(arg.annotation.slice.value, ast.Num)
                assert isinstance(arg.annotation.value, ast.Name)
                width = arg.annotation.slice.value.n
                typ = arg.annotation.value.id
            else:
                width = 1
                typ = arg.annotation.id
            self.symbol_table[arg.arg] = get_type(typ, width)
        [self.visit(s) for s in node.body]

    def visit_Name(self, node):
        if node.id in self.symbol_table:
            if isinstance(node.ctx, ast.Load) and \
               isinstance(self.symbol_table[node.id], Output):
                raise TypeError("Cannot read from `{}` with type Output".format(node.id))
            elif isinstance(node.ctx, ast.Store) and \
                 isinstance(self.symbol_table[node.id], Input):
                raise TypeError("Cannot write to `{}` with type Input".format(node.id))


def type_check(tree):
    return TypeChecker().visit(tree)
