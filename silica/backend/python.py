import ast
from silica.ast_utils import *
from silica.types import *
from silica.transformations.specialize_constants import specialize_constants

class IOVar:
    def __init__(self, name, typ, width):
        self.name = name
        self.typ = typ
        self.width = width

    def get_container(self):
        if self.typ == "Input":
            return Input_(self.width)
        elif self.typ == "Output":
            return Output_(self.width)

class IOVarRewriter(ast.NodeTransformer):
    def __init__(self, io_vars):
        super()
        self.symbol_table = {}
        for var in io_vars:
            self.symbol_table[var.name] = var.typ

    def visit_FunctionDef(self, node):
        node.body = [self.visit(s) for s in node.body]
        return node

    def visit_Assign(self, node):
        node.value = self.visit(node.value)
        if len(node.targets) > 1:
            raise NotImplementedError("a, b, c = ... not implemented yet")  # pragma: no cover
        target = node.targets[0]
        if is_name(target) and target.id in self.symbol_table:
            typ = self.symbol_table[target.id]
            if typ == 'Input':
                # TODO: Linenumber?
                raise TypeError("Attempting to write to Input variable {}".format(target.id))
            elif typ == 'Output':
                target = ast.Attribute(target, "value", ast.Store())
        node.targets[0] = target
        return node

    def visit_Name(self, node):
        if node.id in self.symbol_table:
            typ = self.symbol_table[node.id]
            if typ == 'Input':
                return ast.Attribute(node, "value", ast.Load())
            elif typ == 'Output':
                # TODO: Can we return the linenumber?
                raise TypeError("Attempting to read from an Output variable {}".format(node.id))
        return node


def rewrite_io_vars(tree, io_vars):
    return IOVarRewriter(io_vars).visit(tree)

def get_global_vars_for_func(fn):
    """
    inspect.getmembers() returns a list of (name, value) pairs.
    we are interested in name == __globals__
    """
    return [x for x in inspect.getmembers(fn) if x[0] == "__globals__"][0][1]


class PyFSM:
    def __init__(self, f, clock_enable):
        # `ast_utils.get_ast` returns a module so grab first statement in body
        tree = get_ast(f).body[0]
        io_vars = []
        for arg in tree.args.args:
            annotation = arg.annotation
            width = 1  # default width
            if is_subscript(annotation):
                assert isinstance(annotation.slice.value, ast.Num)
                width = annotation.slice.value.n
                annotation = annotation.value  # Input[1] -> Input
            assert annotation.id in {"Input", "Output"}, annotation.id
            io_vars.append(IOVar(arg.arg, annotation.id, width))
        tree = rewrite_io_vars(tree, io_vars)
        tree.decorator_list = []
        constants = {}
        func_globals = get_global_vars_for_func(f)
        for name, value in func_globals.items():
            if isinstance(value, (int, )):
                constants[name] = value
        tree = specialize_constants(tree, constants)
        src = astor.to_source(tree)
        # print(src)
        exec(src)
        f = eval(tree.name)
        args = []
        for var in io_vars:
            args.append(var.get_container())
        self.cor = f(*args)
        next(self.cor)
        self.IO = lambda x: None  # Hack, allows us to dynamically add attributes
        for var, arg in zip(io_vars, args):
            setattr(self.IO, var.name, arg)

    def __next__(self):
        next(self.cor)
