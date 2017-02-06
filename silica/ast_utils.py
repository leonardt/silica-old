import ast
import astor

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

def get_call_func(node):
    if is_name(node.func):
        return node.func.id
    # Should handle nested expressions/alternate types
    raise NotImplementedError(type(node.value.func))
