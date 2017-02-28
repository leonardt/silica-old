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
            if isinstance(node.op, ast.Mod):
                return self.get_width_of_expr(node.right) - 1
            return max(self.get_width_of_expr(node.left),
                       self.get_width_of_expr(node.right))
        elif isinstance(node, ast.Num):
            return max(node.n.bit_length(), 1)
        elif isinstance(node, ast.Name):
            return self.symbol_table[node.id].width
        elif isinstance(node, ast.Call) and node.func.id == "Reg":
            assert len(node.args) == 1
            return max(node.args[0].n.bit_length(), 1)
        elif isinstance(node, ast.Subscript):
            # FIXME: Support slices
            return 1
        raise NotImplementedError(type(node))  # pragma: no cover

    def visit_Assign(self, node):
        self.visit(node.value)
        if len(node.targets) == 1:
            self.visit(node.targets[0])
            expr_width = self.get_width_of_expr(node.value)
            if isinstance(node.targets[0], ast.Name):
                target = node.targets[0].id
                if target in self.symbol_table:
                    target_width = self.symbol_table[target].width
                    if target_width < expr_width:
                        raise TypeError("Mismatched width, trying to assign expression `{}` of width {} to variable `{}` of width {}".format(astor.to_source(node.value).rstrip(), expr_width, target, target_width))
                else:
                    self.symbol_table[target] = Local(expr_width)
            elif isinstance(node.targets[0], ast.Subscript):
                # FIXME: Support slices
                if expr_width > 1:
                    raise TypeError("Mismatched width, trying to assign expression `{}` of width {} to variable `{}` of width {}".format(astor.to_source(node.value).rstrip(), expr_width, target, target_width))



        else:
            raise NotImplementedError()  # pragma: no cover

    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name):
            _id = node.value.id
            if isinstance(node.ctx, ast.Load) and \
               isinstance(self.symbol_table[_id], Output):
                raise TypeError("Cannot read from `{}` with type Output".format(_id))
            elif isinstance(node.ctx, ast.Store) and \
                 isinstance(self.symbol_table[_id], Input):
                raise TypeError("Cannot write to `{}` with type Input".format(_id))
        else:
            raise NotImplementedError()

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
