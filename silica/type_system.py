import ast
import astor


class TypeError(RuntimeError):
    pass


class _Type:
    def __init__(self, width):
        self.width = width


class Output(_Type):
    pass


class Input(_Type):
    pass


class Local(_Type):
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

    def get_width_of_expr(self, node):
        if isinstance(node, ast.BinOp):
            return max(self.get_width_of_expr(node.left),
                       self.get_width_of_expr(node.right))
        elif isinstance(node, ast.Num):
            return max(node.n.bit_length(), 1)
        elif isinstance(node, ast.Name):
            return self.symbol_table[node.id].width
        raise NotImplementedError(type(node))  # pragma: no cover

    def visit_Assign(self, node):
        self.visit(node.value)
        if len(node.targets) == 1:
            self.visit(node.targets[0])
            assert isinstance(node.targets[0], ast.Name)
            target = node.targets[0].id
            expr_width = self.get_width_of_expr(node.value)
            if target in self.symbol_table:
                target_width = self.symbol_table[target].width
                if target_width != expr_width:
                    raise TypeError("Mismatched width, trying to assign expression `{}` of width {} to variable `{}` of width {}".format(astor.to_source(node.value).rstrip(), expr_width, target, target_width))
            else:
                self.symbol_table[target] = Local(expr_width)


        else:
            raise NotImplementedError()  # pragma: no cover

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
