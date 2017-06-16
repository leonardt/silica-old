import ast

from magma import *
from silica.cfg import ControlFlowGraph, Yield, BasicBlock, Branch
from silica.cfg.types import HeadBlock
from silica.ast_utils import get_ast


def test1():
    def func(a : In(Bit), b : In(Bit), c : Out(Bit)):
        while True:
            if b:
                c = a
            else:
                c = 0
            yield

    # `ast_utils.get_ast` returns a module so grab first statement in body
    cfg = ControlFlowGraph(get_ast(func).body[0])
    blocks = cfg.blocks
    assert isinstance(blocks[0], HeadBlock),   "First block is a head block" 
    assert len(blocks[0].incoming_edges) == 0, "It should have no incoming edges"
    assert len(blocks[0].outgoing_edges) == 1, "It should have one outgoing edge"
    assert isinstance(blocks[1], Branch),      "Next block is a branch"

    assert (blocks[1], "") in blocks[0].outgoing_edges, "Edge flowing out of first block to second block"
    assert (blocks[0], "") in blocks[1].incoming_edges, "Edge flowing into second block from first block"

    branch = blocks[1]
    assert ast.dump(branch.cond) == ast.dump(ast.Name("b", ast.Load())), "branch.cond should be `b`"

