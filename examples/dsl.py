import ast
import inspect
import textwrap


def get_ast(obj):
    """
    from https://github.com/ucb-sejits/ctree/blob/master/ctree/frontend.py
    Return the Python ast for the given object, which may
    be anything that inspect.getsource accepts (incl.
    a module, class, method, function, traceback, frame,
    or code object).
    """
    indented_program_txt = inspect.getsource(obj)
    program_txt = textwrap.dedent(indented_program_txt)
    return ast.parse(program_txt)

# TODO: would be cool to metaprogram these is_* funcs
def is_call(node):
    return isinstance(node, ast.Call)

def is_name(node):
    return isinstance(node, ast.Name)

def get_call_name(node):
    if is_name(node.func):
        return node.func.id
    # Should handle nested expressions/alternate types
    raise NotImplementedError(type(node.value.func))

class FSMDSLException(Exception):
    pass

class DoubleInstantiationException(FSMDSLException):
    def __init__(self, name):
        super().__init__("Tried to instantiate variable " + name + "more than once")


class IOVar:
    def __init__(self, name, typ):
        self.name = name
        self.typ = typ

class IOCollector(ast.NodeVisitor):
    def __init__(self):
        super()
        self.io_vars = lambda: None  # Hack allows us to dynamically add attributes

    def visit_Assign(self, node):
        if is_call(node.value) and get_call_name(node.value) in {"Output", "Input"}:
           for target in node.targets:
               assert is_name(target), "Current instantiation only supports Names on the left side"
               name = target.id
               if hasattr(self.io_vars, name):
                   # TODO: Can we get a line number here?
                   raise DoubleInstantiationException(name)
               setattr(self.io_vars, name, IOVar(get_call_name(node.value)))

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


def rewrite_io_vars(tree, io_vars):
    return IOVarRewriter(io_vars).visit(tree)

def fsm(f):
    tree = get_ast(f)
    io_vars = []
    for arg in tree.body[0].args.args:
        if arg.annotation.id in {"Input", "Output"}:
            io_vars.append(IOVar(arg.arg, arg.annotation.id))
    tee = rewrite_io_vars(tree, io_vars)
    def wrapped(*args, **kwargs):
        cor = f(*args, **kwargs)
        cor.next()
        return cor
    return wrapped


class Module:
    def __init__(self):
        self.fsms = []
        self.connections = []

    def init_fsm(self, fn):
        self.fsms.append(fn)
        return fn

    def connect(self, source, sink):
        assert isinstance(source, IOVar) and isinstance(sink, IOVar)
        self.connections.append((source.unique_id, sink.unique_id))

class IO:
    def __init__(self, width=1):
        self.width = width

class Output(IO):
    pass

class Input(IO):
    pass
