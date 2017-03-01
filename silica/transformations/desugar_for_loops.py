import ast
from silica.ast_utils import *

class ForLoopDesugarer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.loopvars = set()

    def visit_For(self, node):
        new_body = []
        for s in node.body:
            result = self.visit(s)
            if isinstance(result, list):
                new_body.extend(result)
            else:
                new_body.append(result)
        node.body = new_body
        if is_call(node.iter) and is_name(node.iter.func) and \
           node.iter.func.id == "range" and 4 > len(node.iter.args) > 0:
            assert isinstance(node.target, ast.Name)
            if len(node.iter.args) <= 2:
                incr = ast.Num(1)
            else:
                incr = node.iter.args[2]
            if len(node.iter.args) == 1:
                start = ast.Num(0)
                end = node.iter.args[0]
            else:
                start = node.iter.args[0]
                end = node.iter.args[1]
            width = end.n.bit_length()
            self.loopvars.add((node.target.id, width))
            return [
                ast.Assign([node.target], start),
                ast.While(ast.BinOp(node.target, ast.Lt(), end),
                    node.body + [
                        ast.Assign([node.target], ast.BinOp(
                            node.target, ast.Add(), incr))
                    ], [])
            ]
        else:  # pragma: no cover
            print_ast(node)
            raise NotImplementedError("Unsupport for loop construct {}".format(node.iter))

def desugar_for_loops(tree):
    desugarer = ForLoopDesugarer()
    desugarer.visit(tree)
    return tree, desugarer.loopvars
