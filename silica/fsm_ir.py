from silica.cfg import *
import ast
from copy import deepcopy

class Node:
    tab = "    "
    semicolon = ";"

    def dump(self, nonblocking=False):
        raise NotImplementedError(type(self))

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

    def dump(self, nonblocking=False):
        prog = "begin\n"
        for s in self.body:
            for line in s.dump(nonblocking).splitlines():
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

    def qualify_constants(self):
        [s.qualify_constants() for s in self.body]

class Module(Block):
    semicolon = ""
    def __init__(self, name, params, body):
        super().__init__(body)
        self.name = name
        self.params = params

    def dump(self, nonblocking=False):
        prog  = "module {}({}, input CLKIN);\n".format(
            self.name,
            ", ".join(p.dump(nonblocking) for p in self.params)
        )
        for s in self.body:
            for line in s.dump(nonblocking).splitlines():
                prog += self.tab + line + s.semicolon + "\n"
        prog += "endmodule"
        return prog

class Symbol(Node):
    def __init__(self, name):
        self.name = name

    def dump(self, nonblocking=False):
        return self.name

class Subscript(Node):
    def __init__(self, target, index):
        self.target = target
        self.index = index

    def dump(self, nonblocking=False):
        return "{}[{}]".format(self.target.dump(), self.index.dump())

class Slice(Node):
    def __init__(self, bottom, top):
        self.bottom = bottom
        self.top = top

    def dump(self, nonblocking=False):
        return "{}:{}".format(self.bottom.dump(), self.top.dump())

class Constant(Node):
    def __init__(self, value):
        self.value = value
        self.qualified = False

    def dump(self, nonblocking=False):
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

    def dump(self, nonblocking=False):
        return "{} {} {}".format(
            self.typ.dump(nonblocking), 
            "[{}:0]".format(self.width - 1) if self.width > 1 else "",
            self.name.dump(nonblocking))

class Op(Node):
    def __init__(self, op):
        self.op = op

    def dump(self, nonblocking=False):
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

    def dump(self, nonblocking=False):
        return "{} {} {}".format(self.left.dump(nonblocking),
                self.op.dump(nonblocking), self.right.dump(nonblocking))

    def qualify_constants(self):
        self.left.qualify_constants()
        self.right.qualify_constants()

class Assign(Node):
    def __init__(self, target, value):
        self.target = target
        self.value = value

    def dump(self, nonblocking=False):
        return "{} {}= {}".format(self.target.dump(nonblocking),
                "<" if nonblocking else "",
                self.value.dump(nonblocking))

    def qualify_constants(self):
        self.target.qualify_constants()
        self.value.qualify_constants()

class AlwaysPosedgeBlock(Node):
    semicolon = ""
    def __init__(self, body, clock_enable=False):
        self.body = Block(body)
        self.clock_enable = clock_enable

    def dump(self, nonblocking=False):
        prog = "always @(posedge CLKIN) "
        if self.clock_enable:
            prog += "if (clock_enable) "
        # prog += self.body.dump(True)
        prog += self.body.dump()

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

    def dump(self, nonblocking=False):
        prog = "case ({})\n".format(self.cond.dump(nonblocking))
        for key, body in self.bodies.items():
            block = "{}: ".format(key)
            block += body.dump(nonblocking) + "\n"
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

    def dump(self, nonblocking=False):
        prog = "if ({}) ".format(self.cond.dump(nonblocking))
        prog += self.then.dump(nonblocking)
        if self._else is not None:
            prog += " else "
            prog += self._else.dump(nonblocking)
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
    else:
        raise NotImplementedError(type(block))
    return prog

def convert_to_fsm_ir(name, cfg, params, local_vars, clock_enable):
    module_body = []
    module = Module(name, params, module_body)

    for block in cfg.blocks:
        if len(block.incoming_edges) == 0:
            # Initial bloc
            module_body.extend(_compile(s) for s in block.statements)
    # for var in local_vars:
    #     module_body.append(Declaration(Symbol("reg"), Symbol(var)))

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
    with open(name + ".v", "w") as f:
        f.write(module.dump())

