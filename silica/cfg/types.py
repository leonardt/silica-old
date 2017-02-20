

class Block:
    def __init__(self):
        self.outgoing_edges = set()
        self.incoming_edges = set()

    def add_outgoing_edge(self, sink, label=""):
        self.outgoing_edges.add((sink, label))

    def add_incoming_edge(self, source, label=""):
        self.incoming_edges.add((source, label))


class BasicBlock(Block):
    def __init__(self):
        super().__init__()
        self.statements = []

    def add(self, stmt):
        self.statements.append(stmt)



class Branch(Block):
    def __init__(self, cond):
        super().__init__()
        self.cond = cond
        self.true_edge = None
        self.false_edge = None

    def add_false_edge(self, sink):
        self.false_edge = sink

    def add_true_edge(self, sink):
        self.true_edge = sink

class Yield(Block):
    pass
