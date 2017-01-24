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
    __unique_var_id = 0
    def __init__(self, typ):
        self.typ = typ
        self.unique_id = "__var{}".format(IOVar.__unique_var_id)
        IOVar.__unique_var_id += 1

    def __repr__(self):
        return "IOVar(typ={},unique_id={})".format(self.typ, self.unique_id)

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

def fsm(f):
    tree = get_ast(f)
    io_vars = get_io_vars(tree)
    def wrapped(*args, **kwargs):
        cor = f(*args, **kwargs)
        cor.next()
        return cor
    wrapped.io = io_vars
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

    def set(self, node, value):


class IO:
    def __init__(self, width=1):
        self.width = width

class Output(IO):
    pass

class Input(IO):
    pass
