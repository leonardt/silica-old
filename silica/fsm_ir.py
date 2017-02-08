from silica.cfg import *
import ast
from copy import deepcopy

class Node:
    tab = "    "
    semicolon = ";"

    def dump(self):
        raise NotImplementedError(type(self))

    def prune_branches(self, symbol_table):
        pass

class Block(Node):
    def __init__(self, body):
        self.body = body

    def dump(self):
        prog = "begin\n"
        for s in self.body:
            for line in s.dump().splitlines():
                prog += self.tab + line + s.semicolon + "\n"
        prog += "end"
        return prog

    def prune_branches(self, symbol_table):
        new_body = []
        for s in self.body:
            if isinstance(s, Assign) and isinstance(s.value, Constant):
                if isinstance(s.target, Symbol):
                    symbol_table[s.target.name] = s.value.value
                elif isinstance(s.target, Declaration):
                    symbol_table[s.target.name.name] = s.value.value
                else:
                    raise NotImplementedError(type(s.target))
                new_body.append(s)
            elif isinstance(s, If):
                s.then.prune_branches(deepcopy(symbol_table))
                if s._else is not None:
                    s._else.prune_branches(deepcopy(symbol_table))
                try:
                    if eval(s.cond.dump(), deepcopy(symbol_table)):
                        new_body.extend(s.then.body)
                    else:
                        new_body.extend(s._else.body)
                except NameError:
                    new_body.append(s)
            else:
                s.prune_branches(deepcopy(symbol_table))
                new_body.append(s)
        self.body = new_body

class Module(Block):
    semicolon = ""
    def __init__(self, name, params, body):
        super().__init__(body)
        self.name = name
        self.params = params

    def dump(self):
        prog  = "module {}({}, input CLKIN)\n".format(
            self.name,
            ", ".join(p.dump() for p in self.params)
        )
        for s in self.body:
            for line in s.dump().splitlines():
                prog += self.tab + line + s.semicolon + "\n"
        prog += "endmodule"
        return prog


class Symbol(Node):
    def __init__(self, name):
        self.name = name

    def dump(self):
        return self.name

class Constant(Node):
    def __init__(self, value):
        self.value = value

    def dump(self):
        return str(self.value)

class Declaration(Node):
    def __init__(self, typ, name):
        self.typ = typ
        self.name = name

    def dump(self):
        return "{} {}".format(self.typ.dump(), self.name.dump())

class Op(Node):
    def __init__(self, op):
        self.op = op

    def dump(self):
        return self.op

Add = Op("+")
Lt  = Op("<")
binop_map = {
    ast.Add: Add,
    ast.Lt:  Lt,
}

class BinaryOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def dump(self):
        return "{} {} {}".format(self.left.dump(), self.op.dump(), self.right.dump())

class Assign(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def dump(self):
        return "{} = {}".format(self.target.dump(), self.value.dump())

class AlwaysPosedgeBlock(Node):
    semicolon = ""
    def __init__(self, body):
        self.body = Block(body)

    def dump(self):
        prog = "always @(posedge CLKIN) "
        prog += self.body.dump()
        prog += "end"
        return prog

    def prune_branches(self, symbol_table):
        self.body.prune_branches(symbol_table)

class Case(Node):
    semicolon = ""
    def __init__(self, cond, bodies):
        """
        bodies should be a dict mapping case -> body
        """
        self.cond = cond
        assert isinstance(bodies, dict)
        self.bodies = bodies

    def dump(self):
        prog = "case ({})\n".format(self.cond.dump())
        for key, body in self.bodies.items():
            prog += "{}: ".format(key)
            prog += body.dump() + "\n"
        prog += "endcase"
        return prog

    def prune_branches(self, symbol_table):
        for key, body in self.bodies.items():
            body.prune_branches(deepcopy(symbol_table))

class If(Node):
    semicolon = ""
    def __init__(self, cond, then, _else=None):
        self.cond = cond
        self.then = Block(then)
        self._else = Block(_else)

    def dump(self):
        prog = "if ({}) ".format(self.cond.dump())
        prog += self.then.dump()
        if self._else is not None:
            prog += " else "
            prog += self._else.dump()
        return prog

def _compile(block):
    tab = "    "
    prog = []
    if isinstance(block, Branch):
        true_body = _compile(block.true_edge)
        if not isinstance(true_body, list):
            true_body = [true_body]
        if block.false_edge is not None:
            false_body = _compile(block.false_edge)
            if not isinstance(false_body, list):
                false_body = [false_body]
        else:
            false_body = None
        prog.append(If(_compile(block.cond), true_body, false_body))
    elif isinstance(block, BasicBlock):
        for stmt in map(_compile, block.statements):
            if isinstance(stmt, list):
                prog.extend(stmt)
            else:
                prog.append(stmt)
        for stmt in map(lambda x: _compile(x[0]), block.outgoing_edges):
            if isinstance(stmt, list):
                prog.extend(stmt)
            else:
                prog.append(stmt)
    elif isinstance(block, Yield):
        return Assign(Symbol("state"), Constant(block.yield_id))
    elif isinstance(block, ast.Assign):
        assert len(block.targets) == 1
        return Assign(_compile(block.targets[0]), _compile(block.value))
    elif isinstance(block, ast.Name):
        return Symbol(block.id)
    elif isinstance(block, ast.Num):
        return Constant(block.n)
    elif isinstance(block, ast.BinOp):
        return BinaryOp(_compile(block.left), binop_map[type(block.op)], _compile(block.right))
    else:
        raise NotImplementedError(type(block))
    return prog

def convert_to_fsm_ir(cfg, params, local_vars):
    module_body = []
    module = Module("foo", params, module_body)
    module_body.append(
        Assign(Declaration(Symbol("reg"), Symbol("state")), Constant(0)))

    for var in local_vars:
        module_body.append(Declaration(Symbol("reg"), Symbol(var)))

    always_block_body = []
    module_body.append(AlwaysPosedgeBlock(always_block_body))
    case_bodies = {}
    always_block_body.append(Case(Symbol("state"), case_bodies))
    for block in cfg.blocks:
        if isinstance(block, Yield):
            key = block.yield_id
            assert key not in case_bodies
            assert len(block.outgoing_edges) == 1, "Yield should only have one exit"
            case_bodies[key] = Block(_compile(list(block.outgoing_edges)[0][0]))
    module.prune_branches({})
    print(module.dump())
