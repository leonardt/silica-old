import magma
import ast
import astor
import inspect
from silica.backend import PyFSM
import silica.backend
from silica.cfg import ControlFlowGraph
import silica.ast_utils as ast_utils
from silica.transformations import desugar_for_loops, \
    desugar_yield_from_range, specialize_constants, constant_fold, \
    inline_yield_from_functions
import os


def round_to_next_power_of_two(x):
    return 1 << (x - 1).bit_length()


def validate_arguments(func):
    """
    Catch bad (non-magma) types in FSM definitions
    """
    assert isinstance(func, ast.FunctionDef)
    for arg in func.args.args:
        try:
            _type = eval(astor.to_source(arg.annotation), globals(),
                         magma.__dict__)()
            if not isinstance(_type, magma.t.Type):
                raise Exception
        except Exception:
            # We catch then reraise an exception here because an exception can
            # be raised in the eval logic before we even get to check if it's a
            # magma type
            raise Exception(
                "Invalid type {} for argument {}".format(
                    astor.to_source(arg.annotation).rstrip(), arg.arg))


def FSM(f, func_locals, func_globals, backend, clock_enable=False,
        render_cfg=False):
    constants = {}
    for name, value in func_locals.items():
        if isinstance(value, (int, )):
            constants[name] = value

    _file, line_no = astor.code_to_ast.get_file_info(f)
    file_dir = os.path.dirname(_file)
    # `ast_utils.get_ast` returns a module so grab first statement in body
    tree = ast_utils.get_ast(f).body[0]
    validate_arguments(tree)

    local_vars = set()
    tree = specialize_constants(tree, constants)
    tree = constant_fold(tree)
    tree = inline_yield_from_functions(tree, func_locals, func_globals)
    tree, loopvars = desugar_yield_from_range(tree)
    local_vars.update(loopvars)
    tree, loopvars = desugar_for_loops(tree)
    local_vars.update(loopvars)

    cfg = ControlFlowGraph(tree)
    local_vars.update(cfg.local_vars)

    local_vars = list(sorted(local_vars))
    if render_cfg:
        cfg.render()  # pragma: no cover
    if backend == "magma":
        return silica.backend.magma.compile(cfg, local_vars, tree,
                                            clock_enable, func_globals,
                                            func_locals)
    elif backend == "verilog":
        return silica.backend.verilog.compile(cfg, local_vars, tree,
                                              clock_enable, func_globals,
                                              func_locals, file_dir)
    raise NotImplementedError(backend)


def fsm(mode_or_fn="magma", clock_enable=False, render_cfg=False):
    stack = inspect.stack()
    func_locals = stack[1].frame.f_locals
    func_globals = stack[1].frame.f_globals
    if isinstance(mode_or_fn, str):
        def wrapped(fn):
            if mode_or_fn == "python":
                return PyFSM(fn, clock_enable)
            else:
                return FSM(fn, func_locals, func_globals, mode_or_fn,
                           clock_enable, render_cfg)
        return wrapped
    return FSM(mode_or_fn, func_locals, func_globals, "magma", clock_enable,
               render_cfg)
