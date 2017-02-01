from fsm_dsl.transformations.desugar_for_loops import desugar_for_loops
import astor
import ast

def test_range_two_args():
    tree = ast.parse("""
for x in range(0, 15):
    print(x)
""")
    tree = desugar_for_loops(tree)
    expected = """x = 0
while x < 15:
    print(x)
    x = x + 1
"""
    assert expected == astor.to_source(tree)

def test_range_three_args():
    tree = ast.parse("""
for x in range(0, 15, 4):
    print(x)
""")
    tree = desugar_for_loops(tree)
    expected = """x = 0
while x < 15:
    print(x)
    x = x + 4
"""
    assert expected == astor.to_source(tree)
