import ast
from silica.ast_utils import *

class ForLoopDesugarer(ast.NodeTransformer):
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
           node.iter.func.id == "range" and 4 > len(node.iter.args) > 1:
            assert isinstance(node.target, ast.Name)
            if len(node.iter.args) == 2:
                incr = ast.Num(1)
            else:
                incr = node.iter.args[2]
            return [
                ast.Assign([node.target], node.iter.args[0]),
                ast.While(ast.BinOp(node.target, ast.Lt(), node.iter.args[1]),
                    node.body + [
                        ast.Assign([node.target], ast.BinOp(
                            node.target, ast.Add(), incr))
                    ], [])
            ]
        else:
            raise NotImplementedError("Unsupport for loop construct {}".format(node.iter))

def desugar_for_loops(tree):
    return ForLoopDesugarer().visit(tree)
