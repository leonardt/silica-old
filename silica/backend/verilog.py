import ast
import astor
import magma
import os

def compile(cfg, local_vars, tree, clock_enable, func_globals, func_locals, file_dir):
    local_widths = {name: width for name, width in local_vars}
    params = []
    for arg in tree.args.args:
        _type = eval(astor.to_source(arg.annotation), globals(), magma.__dict__)()
        type_str = "output reg" if _type.isoutput() else "input"
        if isinstance(_type, magma.ArrayType):
            type_str += " [{}:0]".format(_type.N)
        params.append(type_str + " " + arg.arg)
    if clock_enable:
        # params.append(Declaration(Symbol("input"), Symbol("clock_enable")))
        params.append("input clock_enable")
    params.append("input CLKIN")
    source = ""
    source += "module {}({});\n".format(tree.name, ", ".join(params))
    state_width = (len(cfg.paths) - 1).bit_length()
    source += "reg [{}:0] yield_state;\n".format(state_width - 1)
    source += "initial begin\n    yield_state = 0;\nend\n"
    for var in sorted(cfg.state_vars):  # Sort for regression tests
        if var != "yield_state":
            width = local_widths[var]
            source += "reg [{}:0] {};\n".format(width - 1, var)
    if clock_enable:
        source += "always @(posedge CLKIN) if (clock_enable) begin\n"
    else:
        source += "always @(posedge CLKIN) begin\n"
    for path in cfg.paths:
        state = path[-1]
        if path is cfg.paths[0]:
            prog = "if "
        else:
            prog = "else if "
        prog += "({}".format(astor.to_source(state.yield_state).rstrip())
        if len(state.conds) > 0:
            prog += " && "
        prog += " && ".join(astor.to_source(cond) for cond in state.conds).rstrip()
        prog += ") begin \n    "
        prog += ";\n    ".join(astor.to_source(statement).rstrip() for statement in state.statements)
        prog += ";\nend\n"
        prog = prog.replace("~", "!")
        prog = prog.replace(" = ", " <= ")
        prog = prog.replace("and", "&&")
        prog = "\n    ".join(prog.splitlines())
        source += "    " + prog + "\n"
    source += "end\n"
    source += "endmodule"
    with open(os.path.join(file_dir, tree.name + ".v"), "w") as f:
        f.write(source)
    return None
