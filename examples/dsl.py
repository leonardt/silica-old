import ast
import astor
import inspect
import textwrap


def print_ast(tree):
    print(astor.to_source(tree))

def get_ast(obj):
    return astor.code_to_ast(obj)

# TODO: would be cool to metaprogram these is_* funcs
def is_call(node):
    return isinstance(node, ast.Call)

def is_name(node):
    return isinstance(node, ast.Name)

def is_subscript(node):
    return isinstance(node, ast.Subscript)

def get_call_name(node):
    if is_name(node.func):
        return node.func.id
    # Should handle nested expressions/alternate types
    raise NotImplementedError(type(node.value.func))

class IOVar:
    def __init__(self, name, typ, width):
        self.name = name
        self.typ = typ
        self.width = width

def get_io_vars(tree):
    collector = IOCollector()
    collector.visit(tree)
    return collector.io_vars

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
            raise NotImplementedError("a, b, c = ... not implemented yet")
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
                # TODO: Linenumber?
                raise TypeError("Attempting to read from an Output variable {}".format(target.id))
        return node


def rewrite_io_vars(tree, io_vars):
    return IOVarRewriter(io_vars).visit(tree)

class FSM:
    def __init__(self, f):
        tree = get_ast(f)
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
        src = astor.to_source(tree)
        print(src)
        exec(src)
        f = eval(tree.name)
        args = []
        for var in io_vars:
            args.append(eval("_{}({})".format(var.typ, var.width)))
        self.cor = f(*args)
        next(self.cor)
        self.IO = lambda x: None  # Hack, allows us to dynamically add attributes
        for var, arg in zip(io_vars, args):
            setattr(self.IO, var.name, arg)

    def __next__(self):
        next(self.cor)


class _IO:
    def __init__(self, width=1):
        self._value = 0
        self.width = width

    @property
    def value(self):
        if self.width > 1:
            val = []
            _val = self._value
            for i in range(0, self.width):
                val.insert(0, _val & 1)
                _val >>= 1
            return val
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class _Output(_IO):
    pass

class _Input(_IO):
    pass

class IO:
    def __getitem__(self, index):
        pass

Output = IO()
Input = IO()
