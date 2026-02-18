from tests.ast.print_tree_test import print_walk, DATA
import pyslang as sl

if __name__ == '__main__':
    tree = sl.SyntaxTree.fromFile(str(DATA / "simple.v"))
    out = print_walk(tree)
    for i, line in enumerate(out.splitlines(), 1):
        if "3:" in line or "IdentifierName @ 3:20" in line or "clk" in line:
            print(f"{i:03}: {line}")
