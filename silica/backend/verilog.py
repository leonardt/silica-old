from silica.cfg import *
import ast
from copy import deepcopy
import silica.ast_utils as ast_utils
import os

class Node:
    tab = "    "
    semicolon = ";"

    def dump(self, nonblocking=False, python=False):
        raise NotImplementedError(type(self))  # pragma: no cover

    def prune_branches(self, symbol_table):
        pass

    def qualify_constants(self):
        pass

class Block(Node):
    def __init__(self, body):
        if not isinstance(body, list):
            assert isinstance(body, Node)
            body = [body]
        self.body = body

    def dump(self, nonblocking=False, python=False):
        prog = "begin\n"
        for s in self.body:
            for line in s.dump(nonblocking, python).splitlines():
                prog += self.tab + line + s.semicolon + "\n"
        prog += "end"
        return prog

    def prune_branches(self, symbol_table):
        new_body = []
        for s in self.body:
            if isinstance(s, Assign):
                if isinstance(s.value, Constant):
                    if isinstance(s.target, Symbol):
                        symbol_table[s.target.name] = s.value.value
                    elif isinstance(s.target, Declaration):
                        symbol_table[s.target.name.name] = s.value.value
                    else:
                        raise NotImplementedError(type(s.target))  # pragma: no cover
                new_body.append(s)
            elif isinstance(s, If):
                s.then.prune_branches(deepcopy(symbol_table))
                if s._else is not None:
                    s._else.prune_branches(deepcopy(symbol_table))
                try:
                    if eval(s.cond.dump(python=True), deepcopy(symbol_table)):
                        new_body.extend(s.then.body)
                    else:
                        new_body.extend(s._else.body)
                except NameError:
                    new_body.append(s)
            else:
                s.prune_branches(deepcopy(symbol_table))
                new_body.append(s)
        self.body = new_body

    def qualify_constants(self):
        [s.qualify_constants() for s in self.body]

class Module(Block):
    semicolon = ""
    def __init__(self, name, params, body):
        super().__init__(body)
        self.name = name
        self.params = params

    def dump(self, nonblocking=False, python=False):
        prog  = "module {}({}, input CLKIN);\n".format(
            self.name,
            ", ".join(p.dump(nonblocking, python) for p in self.params)
        )
        for s in self.body:
            for line in s.dump(nonblocking, python).splitlines():
                prog += self.tab + line + s.semicolon + "\n"
        prog += "endmodule"
        return prog

class Symbol(Node):
    def __init__(self, name):
        self.name = name

    def dump(self, nonblocking=False, python=False):
        return self.name

class Subscript(Node):
    def __init__(self, target, index):
        self.target = target
        self.index = index

    def dump(self, nonblocking=False, python=False):
        return "{}[{}]".format(self.target.dump(nonblocking, python), self.index.dump(nonblocking, python))

class Slice(Node):
    def __init__(self, bottom, top):
        self.bottom = bottom
        self.top = top

    def dump(self, nonblocking=False, python=False):
        return "{}:{}".format(self.bottom.dump(nonblocking, python), self.top.dump(nonblocking, python))

class Constant(Node):
    def __init__(self, value):
        self.value = value
        self.qualified = False

    def dump(self, nonblocking=False, python=False):
        if self.qualified:
            return "{0}'b{1:b}".format(max(self.value.bit_length(), 1), self.value)
        else:
            return str(self.value)

    def qualify_constants(self):
        self.qualified = True

class Declaration(Node):
    def __init__(self, typ, name, width=1):
        self.typ = typ
        self.name = name
        self.width = width

    def dump(self, nonblocking=False, python=False):
        return "{} {} {}".format(
            self.typ.dump(nonblocking, python), 
            "[{}:0]".format(self.width - 1) if self.width > 1 else "",
            self.name.dump(nonblocking, python))

class Op(Node):
    def __init__(self, op, python_op=None):
        self.op = op
        self.python_op = python_op

    def dump(self, nonblocking=False, python=False):
        if python and self.python_op is not None:
            return self.python_op
        return self.op

Add    = Op("+")
Sub    = Op("-")
Mul    = Op("*")
Lt     = Op("<")
LtE    = Op("<=")
BitOr  = Op("|")
BitAnd = Op("&")
And    = Op("&&", "and")
Mod    = Op("%")
binop_map = {
    ast.Add: Add,
    ast.Sub: Sub,
    ast.Lt:  Lt,
    ast.LtE: LtE,
    ast.BitOr:  BitOr,
    ast.BitAnd: BitAnd,
    ast.Mult: Mul,
    ast.And: And,
    ast.Mod: Mod
}

class BinaryOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def dump(self, nonblocking=False, python=False):
        return "{} {} {}".format(self.left.dump(nonblocking, python),
                self.op.dump(nonblocking, python), self.right.dump(nonblocking, python))

    def qualify_constants(self):
        self.left.qualify_constants()
        self.right.qualify_constants()

LogicalNot = Op("!", "not")

unop_map = {
    ast.Not: LogicalNot,
}

class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def dump(self, nonblocking=False, python=False):
        return "{}({})".format(self.op.dump(nonblocking, python), self.operand.dump(nonblocking, python))


class Assign(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def dump(self, nonblocking=False, python=False):
        return "{} {}= {}".format(self.target.dump(nonblocking, python),
                "<" if nonblocking else "",
                self.value.dump(nonblocking, python))

    def qualify_constants(self):
        self.target.qualify_constants()
        self.value.qualify_constants()

class AlwaysPosedgeBlock(Node):
    semicolon = ""
    def __init__(self, body, clock_enable=False):
        self.body = Block(body)
        self.clock_enable = clock_enable

    def dump(self, nonblocking=False, python=False):
        prog = "always @(posedge CLKIN) "
        if self.clock_enable:
            prog += "if (clock_enable) "
        # prog += self.body.dump(True)
        prog += self.body.dump(nonblocking, python)

        return prog

    def prune_branches(self, symbol_table):
        self.body.prune_branches(symbol_table)

    def qualify_constants(self):
        self.body.qualify_constants()

class Case(Node):
    semicolon = ""
    def __init__(self, cond, bodies):
        """
        bodies should be a dict mapping case -> body
        """
        self.cond = cond
        assert isinstance(bodies, dict)
        self.bodies = bodies

    def dump(self, nonblocking=False, python=False):
        prog = "case ({})\n".format(self.cond.dump(nonblocking, python))
        for key, body in self.bodies.items():
            block = "{}: ".format(key)
            block += body.dump(nonblocking, python) + "\n"
            for line in block.splitlines():
                prog += self.tab + line + "\n"
        prog += "endcase"
        return prog

    def prune_branches(self, symbol_table):
        for key, body in self.bodies.items():
            body.prune_branches(deepcopy(symbol_table))

    def qualify_constants(self):
        for key, body in self.bodies.items():
            body.qualify_constants()

class If(Node):
    semicolon = ""
    def __init__(self, cond, then, _else=None):
        self.cond = cond
        self.then = Block(then)
        self._else = Block(_else)

    def dump(self, nonblocking=False, python=False):
        prog = "if ({}) ".format(self.cond.dump(nonblocking, python))
        prog += self.then.dump(nonblocking, python)
        if self._else is not None:
            prog += " else "
            prog += self._else.dump(nonblocking, python)
        return prog

    def qualify_constants(self):
        self.cond.qualify_constants()
        self.then.qualify_constants()
        self._else.qualify_constants()

def _compile(block):
    tab = "    "
    prog = []
    if isinstance(block, Branch):
        true_body = _compile(block.true_edge)
        if block.false_edge is not None:
            false_body = _compile(block.false_edge)
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
        if isinstance(block.value, ast.Call):
            assert block.value.func.id in {"Reg"}
            assert len(block.value.args) == 1
            assert isinstance(block.value.args[0], ast.Num)
            return Declaration(
                    Symbol(block.value.func.id.lower()),
                    _compile(block.targets[0]),
                    block.value.args[0].n)
        return Assign(_compile(block.targets[0]), _compile(block.value))
    elif isinstance(block, ast.Name):
        return Symbol(block.id)
    elif isinstance(block, ast.Num):
        return Constant(block.n)
    elif isinstance(block, ast.BinOp):
        return BinaryOp(_compile(block.left), binop_map[type(block.op)], _compile(block.right))
    elif isinstance(block, ast.Subscript):
        return Subscript(_compile(block.value), _compile(block.slice.value))
    elif isinstance(block, ast.UnaryOp):
        return UnaryOp(unop_map[type(block.op)], _compile(block.operand))
    elif isinstance(block, ast.BoolOp):
        curr = _compile(block.values[0])
        for value in block.values[1:]:
            curr = BinaryOp(_compile(value), binop_map[type(block.op)], curr)
        return curr
    elif isinstance(block, ast.Compare):
        curr = _compile(block.left)
        for op, comparator in zip(block.ops, block.comparators):
            curr = BinaryOp(curr, binop_map[type(op)], _compile(comparator))
        return curr
    elif isinstance(block, ast.Expr):
        if isinstance(block.value, ast.Str):
            return []  # docstring, ignore
        raise NotImplementedError(type(block))  # pragma: no cover
    else:  # pragma: no cover
        ast_utils.print_ast(block)
        raise NotImplementedError(type(block))
    return prog

def compile(func_name, tree, cfg, local_vars, clock_enable, file_dir):
    params = []
    for arg in tree.args.args:
        if isinstance(arg.annotation, ast.Subscript):
            assert isinstance(arg.annotation.slice.value, ast.Num)
            assert isinstance(arg.annotation.value, ast.Name)
            typ = Subscript(Symbol(arg.annotation.value.id.lower()), 
                            Slice(Constant(arg.annotation.slice.value.n - 1), Constant(0)))
        else:
            typ = Symbol(arg.annotation.id.lower())
        params.append(Declaration(typ, Symbol(arg.arg)))
    if clock_enable:
        params.append(Declaration(Symbol("input"), Symbol("clock_enable")))
    module_body = []
    module = Module(func_name, params, module_body)

    for block in cfg.blocks:
        if len(block.incoming_edges) == 0:
            # Initial bloc
            module_body.extend(_compile(s) for s in block.statements)
    for var, width in local_vars:
        module_body.append(Declaration(Subscript(Symbol("reg"), Slice(Constant(width - 1), Constant(0))), Symbol(var)))

    always_block_body = []
    module_body.append(AlwaysPosedgeBlock(always_block_body, clock_enable))
    case_bodies = {}
    always_block_body.append(Case(Symbol("state"), case_bodies))
    num_states = 0
    for block in cfg.blocks:
        if isinstance(block, Yield):
            num_states += 1
            key = block.yield_id
            assert key not in case_bodies
            assert len(block.outgoing_edges) == 1, "Yield should only have one exit"
            body = _compile(list(block.outgoing_edges)[0][0])
            case_bodies[key] = Block(body)
    state_width = (num_states - 1).bit_length()
    module_body.insert(0, 
        Assign(Declaration(Symbol("reg"), Symbol("state"), state_width), Constant(0)))
    module.prune_branches({})
    module.qualify_constants()
    with open(os.path.join(file_dir, func_name + ".v"), "w") as f:
        f.write(module.dump())

