import ast
import astor
import inspect
import textwrap


def print_ast(tree):  # pragma: no cover
    print(astor.to_source(tree))


def get_ast(obj):
    indented_program_txt = inspect.getsource(obj)
    program_txt = textwrap.dedent(indented_program_txt)
    return ast.parse(program_txt)
    # return astor.code_to_ast(obj)


# TODO: would be cool to metaprogram these is_* funcs
def is_call(node):
    return isinstance(node, ast.Call)

def is_name(node):
    return isinstance(node, ast.Name)

def is_subscript(node):
    return isinstance(node, ast.Subscript)

def get_call_func(node):
    if is_name(node.func):
        return node.func.id
    # Should handle nested expressions/alternate types
    raise NotImplementedError(type(node.value.func))  # pragma: no cover
