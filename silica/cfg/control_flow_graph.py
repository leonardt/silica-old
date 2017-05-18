import ast
import astor
from silica.transformations import specialize_constants, replace_symbols
from silica.visitors import collect_names
from silica.cfg.types import Block, BasicBlock, Yield, Branch, HeadBlock, State
import tempfile
from copy import deepcopy


class ControlFlowGraph(ast.NodeVisitor):
    def __init__(self, tree, clock_enable, local_vars):
        super()
        local_widths = {name: width for name, width in local_vars}
        self.blocks = []
        self.curr_block = None
        self.curr_yield_id = 1

        outputs = set()
        inputs = set()
        for arg in tree.args.args:
            if "Out" in astor.to_source(arg.annotation):
                outputs.add(arg.arg)
            elif "In" in astor.to_source(arg.annotation):
                inputs.add(arg.arg)
            else:
                assert False
        self.visit(tree)
        self.bypass_conds()
        paths = self.collect_paths_between_yields()
        paths = self.promote_live_variables(paths)
        paths, state_vars = self.append_state_info(paths, outputs, inputs)
        self.paths = paths
        self.state_vars = state_vars

        # self.render_paths_between_yields(self.paths)
        # exit()

        # state_width = (len(paths) - 1).bit_length()
        # source = "reg [{}:0] yield_state;\n".format(state_width - 1)
        # source += "initial begin\n    yield_state = 0;\nend\n"
        # for var in sorted(state_vars):  # Sort for regression tests
        #     if var != "yield_state":
        #         width = local_widths[var]
        #         source += "reg [{}:0] {};\n".format(width - 1, var)
        # if clock_enable:
        #     source += "always @(posedge CLKIN) if (clock_enable) begin\n"
        # else:
        #     source += "always @(posedge CLKIN) begin\n"
        # for path in paths:
        #     state = path[-1]
        #     prog = "if ({}".format(astor.to_source(state.yield_state).rstrip())
        #     if len(state.conds) > 0:
        #         prog += " && "
        #     prog += " && ".join(astor.to_source(cond) for cond in state.conds).rstrip()
        #     prog += ") begin \n    "
        #     prog += ";\n    ".join(astor.to_source(statement).rstrip() for statement in state.statements)
        #     prog += ";\nend\n"
        #     prog = prog.replace("~", "!")
        #     prog = prog.replace(" = ", " <= ")
        #     prog = prog.replace("and", "&&")
        #     prog = "\n    ".join(prog.splitlines())
        #     source += "    " + prog + "\n"
        # source += "end\n"
        # self.source = source

    def append_state_info(self, paths, outputs, inputs):
        for path in paths:
            state = State()
            if isinstance(path[0], HeadBlock):
                yield_id = 0
            else:
                yield_id = path[0].yield_id
            state.yield_state = ast.Compare(ast.Name("yield_state", ast.Load()), [ast.Eq()], [ast.Num(yield_id)],)
            for i in range(1, len(path)):
                block = path[i]
                if isinstance(block, Branch):
                    cond = block.cond
                    if path[i + 1] is block.false_edge:
                        cond = ast.UnaryOp(ast.Invert(), cond)
                    state.conds.append(cond)
            state.statements.append(ast.Assign([ast.Name("yield_state", ast.Store())], ast.Num(path[-1].yield_id)))
            path.append(state)
        state_vars = {"yield_state"}
        for path in paths:
            state = path[-1]
            for cond in state.conds:
                names = collect_names(cond)
                for name in names:
                    if name not in outputs and \
                       name not in inputs:
                        state_vars.update(names)
        for path in paths:
            state = path[-1]
            seen = {"yield_state"}
            for block in path[:-1]:
                if isinstance(block, BasicBlock):
                    for statement in block.statements:
                        assert isinstance(statement, ast.Assign)
                        if isinstance(statement.targets[0], ast.Name):
                            seen.add(statement.targets[0].id)
                        state.statements.append(statement)
            # for output in outputs:
            #     if output not in seen:
            #         state.statements.append(ast.Assign([ast.Name(output, ast.Store())], ast.Name(output + "_last", ast.Load())))
            # for state_var in state_vars:
            #     if state_var not in seen:
            #         state.statements.append(ast.Assign([ast.Name(state_var, ast.Store())], ast.Name(state_var + "_last", ast.Load())))
        return paths, state_vars


    def promote_live_variables(self, paths):
        for path in paths:
            symbol_table = {}
            for block in path:
                if isinstance(block, BasicBlock):
                    new_statements = []
                    for statement in block.statements:
                        statement = replace_symbols(statement, symbol_table, ctx=ast.Load)
                        if isinstance(statement, ast.Assign) and \
                           len(statement.targets) == 1 and \
                           isinstance(statement.targets[0], ast.Name):
                            symbol_table[statement.targets[0].id] = statement.value
                        new_statements.append(statement)
                    block.statements = new_statements
                elif isinstance(block, Branch):
                    block.cond = replace_symbols(block.cond, symbol_table, ctx=ast.Load)
        return paths


    def find_paths(self, block):
        if isinstance(block, Yield):
            return [[deepcopy(block)]]
        elif isinstance(block, BasicBlock):
            return [[deepcopy(block)] + path for path in self.find_paths(block.outgoing_edge[0])]
        elif isinstance(block, Branch):
            true_paths = [[deepcopy(block)] + path for path in self.find_paths(block.true_edge)]
            false_paths = [[deepcopy(block)] + path for path in self.find_paths(block.false_edge)]
            for path in true_paths:
                path[0].true_edge = path[1]
            for path in false_paths:
                path[0].false_edge = path[1]
            return true_paths + false_paths
        else:
            raise NotImplementedError(type(block))

    def collect_paths_between_yields(self):
        paths = []
        for block in self.blocks:
            if isinstance(block, (Yield, HeadBlock)):
                paths.extend([block] + path for path in self.find_paths(block.outgoing_edge[0]))
        return paths


    def collect_constant_assigns(self, statements):
        constant_assigns = {}
        for stmt in statements:
            if isinstance(stmt, ast.Assign):
                if isinstance(stmt.value, ast.Num) and len(stmt.targets) == 1:
                    if isinstance(stmt.targets[0], ast.Name):
                        constant_assigns[stmt.targets[0].id] = stmt.value.n
                    else:
                        # TODO: This should already be guaranteed by a type checker
                        assert stmt.targets[0].name in constant_assigns, "Assigned to multiple constants"
        return constant_assigns

    def bypass_conds(self):
        for block in self.blocks:
            if isinstance(block, BasicBlock) and \
               isinstance(block.outgoing_edge[0], Branch):
                constants = self.collect_constant_assigns(block.statements)
                branch = block.outgoing_edge[0]
                cond = deepcopy(branch.cond)
                cond = specialize_constants(cond, constants)
                try:
                    if eval(astor.to_source(cond)):
                        # FIXME: Interface violation, need a remove method from blocks
                        block.outgoing_edges = {(branch.true_edge, "")}
                    else:
                        block.outgoing_edges = {(branch.false_edge, "")}
                except NameError as e:
                    pass


    def get_new_block(self):
        block = BasicBlock()
        self.blocks.append(block)
        return block

    def new_branch(self, test):
        block = Branch(test)
        self.blocks.append(block)
        return block

    def new_yield(self):
        block = Yield()
        block.yield_id = self.curr_yield_id
        self.curr_yield_id += 1
        self.blocks.append(block)
        return block

    def add_edge(self, source, sink, label=""):
        source.add_outgoing_edge(sink, label)
        sink.add_incoming_edge(source, label)
        # self.edges.append((source, sink, label))

    def add_true_edge(self, source, sink):
        assert isinstance(source, Branch)
        source.add_outgoing_edge(sink, "T")
        source.true_edge = sink
        sink.add_incoming_edge(source, "T")

    def add_false_edge(self, source, sink):
        assert isinstance(source, Branch)
        source.add_outgoing_edge(sink, "F")
        source.false_edge = sink
        sink.add_incoming_edge(source, "F")

    def process_stmt(self, stmt):
        # TODO: Should be able to refactor this to reuse logic for "branching"
        # nodes
        if isinstance(stmt, ast.While):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            # self.curr_block.add(ast.If(stmt.test, [], []))
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_true_edge(old_block, self.curr_block)
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            self.add_edge(self.curr_block, old_block)
            self.curr_block = self.get_new_block()
            self.add_false_edge(old_block, self.curr_block)
        elif isinstance(stmt, (ast.If,)):
            old_block = self.curr_block
            self.curr_block = self.new_branch(stmt.test)
            self.add_edge(old_block, self.curr_block)
            # self.curr_block.add(stmt)
            old_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_true_edge(old_block, self.curr_block)
            for sub_stmt in stmt.body:
                self.process_stmt(sub_stmt)
            end_then_block = self.curr_block
            if len(stmt.orelse) > 0:
                self.curr_block = self.get_new_block()
                self.add_false_edge(old_block, self.curr_block)
                for sub_stmt in stmt.orelse:
                    self.process_stmt(sub_stmt)
                end_else_block = self.curr_block
            self.curr_block = self.get_new_block()
            self.add_edge(end_then_block, self.curr_block)
            if len(stmt.orelse) > 0:
                self.add_edge(end_else_block, self.curr_block)
            else:
                self.add_false_edge(old_block, self.curr_block)
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Yield):
                old_block = self.curr_block
                self.curr_block = self.new_yield()
                self.add_edge(old_block, self.curr_block)
                old_block = self.curr_block
                self.curr_block = self.get_new_block()
                self.add_edge(old_block, self.curr_block)
            elif isinstance(stmt.value, ast.Str): 
                # Docstring, ignore
                pass
            else:  # pragma: no cover
                raise NotImplementedError(stmt.value)
        else:
            self.curr_block.add(stmt)

    def remove_block(self, block):
        for source, source_label in block.incoming_edges:
            source.outgoing_edges.remove((block, source_label))
        for sink, sink_label in block.outgoing_edges:
            sink.incoming_edges.remove((block, sink_label))
        for source, source_label in block.incoming_edges:
            if isinstance(source, Branch):
                if len(block.outgoing_edges) == 1:
                    sink, sink_label = list(block.outgoing_edges)[0]
                    self.add_edge(source, sink, source_label)
                    if source_label == "F":
                        source.false_edge = sink
                    elif source_label == "T":
                        source.true_edge = sink
                    else:  # pragma: no cover
                        assert False
                else:
                    assert len(block.outgoing_edges) == 0
            else:
                for sink, sink_label in block.outgoing_edges:
                    self.add_edge(source, sink, source_label)

    def consolidate_empty_blocks(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, BasicBlock) and len(block.statements) == 0:
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def remove_if_trues(self):
        new_blocks = []
        for block in self.blocks:
            if isinstance(block, Branch) and (isinstance(block.cond, ast.NameConstant) \
                    and block.cond.value == True):
                self.remove_block(block)
            else:
                new_blocks.append(block)
        self.blocks = new_blocks

    def visit_FunctionDef(self, node):
        self.head_block = HeadBlock()
        self.blocks.append(self.head_block)
        self.curr_block = self.get_new_block()
        self.add_edge(self.head_block, self.curr_block)
        for stmt in node.body:
            self.process_stmt(stmt)
        self.consolidate_empty_blocks()
        self.remove_if_trues()

    def render(self):  # pragma: no cover
        from graphviz import Digraph
        dot = Digraph(name="top")
        for block in self.blocks:
            if isinstance(block, Branch):
                label = "if " + astor.to_source(block.cond)
                dot.node(str(id(block)), label.rstrip(), {"shape": "invhouse"})
            elif isinstance(block, Yield):
                label = "yield"
                dot.node(str(id(block)), label.rstrip(), {"shape": "oval"})
            elif isinstance(block, BasicBlock):
                label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                dot.node(str(id(block)), label.rstrip(), {"shape": "box"}) 
            elif isinstance(block, HeadBlock):
                label = "Initial"
                dot.node(str(id(block)), label.rstrip(), {"shape": "doublecircle"}) 
            else:
                raise NotImplementedError(type(block))
        # for source, sink, label in self.edges:
            for sink, label in block.outgoing_edges:
                dot.edge(str(id(block)), str(id(sink)), label)


        file_name = tempfile.mktemp("gv")
        dot.render(file_name, view=True)
        # print(file_name)
        # exit()

    def render_paths_between_yields(self, paths):  # pragma: no cover
        from graphviz import Digraph
        dot = Digraph(name="top")
        for i, path in enumerate(paths):
            prev = None
            for block in path:
                if isinstance(block, Branch):
                    label = "if " + astor.to_source(block.cond)
                    dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "invhouse"})
                elif isinstance(block, Yield):
                    label = "yield {}".format(block.yield_id)
                    dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "oval"})
                elif isinstance(block, BasicBlock):
                    label = "\n".join(astor.to_source(stmt) for stmt in block.statements)
                    dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "box"}) 
                elif isinstance(block, HeadBlock):
                    label = "Initial"
                    dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "doublecircle"}) 
                elif isinstance(block, State):
                    label = "{}".format(astor.to_source(block.yield_state).rstrip())
                    if len(block.conds) > 0:
                        label += " && "
                    label += " && ".join(astor.to_source(cond) for cond in block.conds)
                    label += "\n"
                    label += "\n".join(astor.to_source(statement) for statement in block.statements)
                    dot.node(str(i) + str(id(block)), label.rstrip(), {"shape": "doubleoctagon"})
                else:
                    raise NotImplementedError(type(block))
                if prev is not None:
                    if isinstance(prev, Branch):
                        if block is prev.false_edge:
                            label = "F"
                        else:
                            label = "T"
                    else:
                        label = ""
                    dot.edge(str(i) + str(id(prev)), str(i) + str(id(block)), label)
                prev = block

        file_name = tempfile.mktemp("gv")
        dot.render(file_name, view=True)
